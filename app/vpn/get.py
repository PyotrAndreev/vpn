import sys
from datetime import datetime
from pathlib import Path
from types import Any

import aiohttp, asyncio
from asyncio import TimeoutError, IncompleteReadError
from aiohttp import TCPConnector, ClientProxyConnectionError, ClientTimeout, ServerDisconnectedError, ClientOSError, ClientResponseError
from python_socks import ProxyError
from aiohttp_socks import ProxyConnector

import polars as pl

from ..utils.files import from_json, to_json
from ..utils.combiner import fast_store_to

import logging
logger = logging.getLogger(__name__)


# Constants
TIMEOUT_GET_RAW_VPN = ClientTimeout(total=10)
VPN_SOURCES = from_json(Path(__file__).parent / 'sources.json')  # look to README to see more sources


async def get_vpns(proxies: list[dict[str, str | bool]], from_local_files: bool = True) -> dict[str, dict[str, Any]] | None:
    """
    Try async via each proxy, return the first successful response body.
    """

    # # TODO: rename 'from_local_files'
    # if from_local_files:
    #     vpns = from_json('tmp/sources/')
    #     # TODO: full path or just dir (rewrite the from_json to try the files from the newest to the oldest)
    #     return vpns

    logger.debug(f"Start VPN fetching by all proxies")

    tasks = [
        asyncio.create_task(_get_raw_vpns(proxy_meta['protocol'], proxy_meta['ip_port']))
        for proxy_meta in proxies
        # here could be filters for country, security and others (not all proxies supports)
    ]
    
    for task in asyncio.as_completed(tasks):  # could be changed 'async for task ...' if using CPython3.13+
        # TODO: how to do, if one proxy can not provide info from all VPN sources? How combine data from the dfferent tasks? 
        vpns: dict[str, dict[str, str | int | None]] | None = await task
        if vpns:
            ### THE ASYNCIO THEORY ###
            # don't need to cancel leftover tasks: each has a timeout and RC will delete:
            #   - p.s.: if sockets, connectors, buffers, etc are needed to be free then you should cancel all tasks before the get_vpns return anything
            #   - coroutine’s frame, locals, and instruction pointer in this coroutine CPyhton object
            #   - Task(...) is a wrapper around a (self._coro) coroutine to which the coroutine returns a value/error
            #   - EventLoop has dqueue in self._ready
            #   - create_task(Task(...)) steps:
            #       1. handle = events.Handle(Task(...)._step, (), self, context)
            #       2. in EventLoop: self._ready.append(handle) → strong link to Task(...) in the dqueue

            #   - tasks has a strong refs to each Task(...); EventLoop has strong refs to each Task(...) before it has been done and weak refs after 
            #   
            #   - get_vpns func returns → RC deletes tasks and:
            #       - if Task(...) status is done:
            #           RC deletes Task(...) → coroutine object
            #       - else:
            #           Task(...) is alive before it's statuce is done
            # TODO: ASYNCIO THEORY: but why the program doesn't shutdown when some asyncio tasks are active?

            to_json(vpns, full_path='vpn/tmp/sources/vpn.json', suffix=f"{datetime.now():%Y%m%d}", max_files_in_dir=2)
            return vpns

    logger.warning("❌ No working proxy found.")
    sys.exit(1)  # terminate with a non-zero exit code


async def _get_raw_vpns(protocol: str, ip_port: str) -> dict[str, dict[str, str | int | None]] | None:
    """
    Receiving VPNs from many sources via one proxy. Store it.
    
    Return dict:
        with list[dict] if VPN IP happend more then one or dict if only unique IPs 
    """
    vpn_store: dict = {}
    proxy = f'{protocol}://{ip_port}'
    connector, proxy_arg = _create_proxy_connector(protocol, proxy)
    
    try:
        async with aiohttp.ClientSession(connector=connector, raise_for_status=True) as session:

            for source, url in VPN_SOURCES.items():

                async with session.get(url, proxy=proxy_arg, timeout=TIMEOUT_GET_RAW_VPN) as response:

                    if is_good_resp(source, resp := await response.text()):
                        logger.info(f"✅ GOT {source} data: {url=} via {proxy=}")
                        _vpn_preprocessing(vpn_store, source, resp)                       
                    else:
                        logger.debug(f"⚠️ Invalid HTML payload via {proxy=}. HTML {len(resp)=}")

            return vpn_store

    except TimeoutError:
        logger.debug(f"⏳ Timeout:\t{proxy=}")
    except IncompleteReadError:
        logger.debug(f"❌ SOCKS handshake failed: {proxy=}")
    except (ClientProxyConnectionError, ProxyError) as e:
        logger.debug(f"🚫 Proxy connection error:\t{proxy=}")
    except ServerDisconnectedError as e:
        logger.debug(f"🔌 Disconnected:\t{proxy=}")
    except ClientOSError as e:
        logger.debug(f"❗ OS error:\t{proxy=}")
    except ClientResponseError as e:
        logger.debug(f"⚠️  Bad HTTP: {e.status=}\t{proxy=}")
    except Exception:
        logger.exception(f"❌ Unexpected error in '_get_raw_vpns' for {proxy=}")
        raise


def _create_proxy_connector(protocol: str, proxy: str) -> tuple[ProxyConnector | TCPConnector, str]:
    """Return an aiohttp/aiohttp_socks connector and proxy argument based on the proxy protocol."""

    if "socks5" == protocol:
        connector = ProxyConnector.from_url(proxy, rdns=True)
        proxy_arg = None       # handled by the connector itself
    elif "socks" in protocol:  # socks5h, socks4, ...:
        connector = ProxyConnector.from_url(proxy)
        proxy_arg = None
    elif "http" in protocol:  # http, https
        connector = TCPConnector()             # normal TCP; aiohttp does the CONNECT
        proxy_arg = proxy     # pass to session.get
    else:
        raise ValueError(f"Unknown proxy protocol: {protocol!r}")
    
    return connector, proxy_arg


def is_good_resp(source: str, data: str) -> bool:
    if source == "vpngate":
        if data.lstrip().startswith("*vpn_servers"):  # got the expected *vpn_servers CSV header
            return True
        return False
    
    elif ...:
        ...


def _vpn_preprocessing(vpn_store: dict, source: str, raw_data: str) -> None:
    '''
    Clean and transform raw VPN data from a proxy source into structured metadata.

    Returns:
        Mapping of IP to metadata dictionary including the source tag
    '''
    try:
        if source == "vpngate":
            # clean the raw data
            raw_data = raw_data.replace("*vpn_servers", '', count=1) \
                               .strip('# *\r\n\t')

            df = pl.read_csv(raw_data.encode(),  # feed Polars a bytes buffer
                             has_header=True)

            vpns: dict = df.with_columns(pl.lit("vpngate").alias("source")) \
                           .rows_by_key(key=['IP'], named=True, unique=True)  # convert to python dict
            
            for ip, meta in vpns.items():
                fast_store_to(vpn_store, ip, meta)

    except Exception:
        ...


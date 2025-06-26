import sys
from pathlib import Path

import aiohttp, asyncio
from asyncio import TimeoutError, IncompleteReadError
from aiohttp import TCPConnector, ClientProxyConnectionError, ClientTimeout, ServerDisconnectedError, ClientOSError, ClientResponseError
from python_socks import ProxyError
from aiohttp_socks import ProxyConnector

import polars as pl

from ..utils.files import from_json

import logging
logger = logging.getLogger(__name__)


# Constants
TIMEOUT_GET_RAW_VPN = ClientTimeout(total=10)
VPN_SOURCES = from_json(Path(__file__).parent / 'sources.json')  # look to README to see more sources


async def get_vpns_from_web(proxies: list[dict[str, str | bool]]) -> str | None:
    """
    Try async via each proxy, return the first successful response body.
    """

    logger.debug(f"Starting VPN fetch by all proxies")

    source = 'vpngate'  # TODO: should be optimised for many sources
    tasks = [
        asyncio.create_task(_get_raw_vpns(proxy_meta['protocol'], proxy_meta['ip_port']))  # , sources=source))
        for proxy_meta in proxies
        # here could be filters for country, security and others (not all proxies supports)
    ]
    
    for task in asyncio.as_completed(tasks):  # could be changed 'async for task ...' if using CPython3.13+
        result = await task
        if result:
            logger.info("✅ Got the first successful response")
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
            return result

            # df = _vpn_preprocessing(result, source)
            
            # TODO: Plugin into CSV / JSON
        
    logger.warning("❌ No working proxy found.")
    sys.exit(1)  # terminate with a non-zero exit code


# async _get_vpns_from_local(...) -> str | None:
#     ...


# async def get_vpns_from_web(proxies: list[dict[str, str | bool]]) -> str | None:
#     ...
#     async while


async def _get_raw_vpns(protocol: str, ip_port: str) -> str | None: #, sources: tuple | str) -> str | None:

    proxy = f'{protocol}://{ip_port}'
    connector, proxy_arg = _create_proxy_connector(protocol, proxy)
    
    try:
        # TODO: 'sources' and 'url' should be optimised for many sources
        url = list(VPN_SOURCES.values())[0]
        async with aiohttp.ClientSession(connector=connector, raise_for_status=True) as session:
            async with session.get(url, proxy=proxy_arg, timeout=TIMEOUT_GET_RAW_VPN) as resp:
                body = await resp.text()
                if is_good_resp(source := 'vpngate', body):
                    logger.debug(f"✅ GOT openvpn data: {url=} via {proxy=}")
                    return body

            # TODO: make the code for many VPN sources:
            # raw_data = dict()
            # for source, url in VPN_SOURCES.items():
            #     async with session.get(url, proxy=proxy_arg, timeout=TIMEOUT_GET_RAW_VPN) as resp:
            #         body = await resp.text()

            #         if is_good_resp(source, body):
            #             logger.debug(f"✅ GOT openvpn data: {url=} via {proxy=}")
            #             raw_data[source] = body
            #         else:
            #             logger.debug(f"⚠️ Invalid HTML payload via {proxy=}. HTML {len(body)=}")
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


# def _vpn_preprocessing(proxies_store: dict, source: str, raw_data: str) -> None:
def _vpn_preprocessing(source: str, raw_data: str) -> list[dict[str, str | bool]]:
    '''clean the responce from proxy sources'''
    vpn_meta: list[dict[str, str | bool]] = []

    try:
        if source == "vpngate":
            # delete the last * and # in a hedder
            raw_data = raw_data.rstrip().rstrip('*') \
                            .replace("#", '', count=1)
            
            return pl.read_csv(raw_data.encode(),  # feed Polars a bytes buffer
                               skip_rows=1,        # drop the first row: '*vpn_servers'
                               has_header=True
            )
        
    except Exception:
        ...


# def try_connect_ovpn_config(ovpn_text, timeout=60):
#     with NamedTemporaryFile("w", suffix=".ovpn", delete=False) as f:
#         f.write(ovpn_text)
#         ovpn_path = f.name

#     try:
#         proc = subprocess.Popen(
#             ["sudo", "openvpn", "--config", ovpn_path],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.STDOUT,
#             text=True
#         )

#         t_start = time.time()
#         while time.time() - t_start < timeout:
#             line = proc.stdout.readline()
#             if "Initialization Sequence Completed" in line:
#                 print("[+] Connected successfully!")
#                 proc.terminate()
#                 return True
#             if "TLS Error" in line or "Connection refused" in line:
#                 break
#         proc.terminate()
#         return False
#     finally:
#         os.remove(ovpn_path)
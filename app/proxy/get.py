import re, sys
from datetime import datetime
from pathlib import Path

import aiohttp, asyncio
from asyncio import TimeoutError, IncompleteReadError
from aiohttp import ClientSession, ClientTimeout, ClientError

from ..utils.files import from_json, to_json
from ..utils.combiner import fast_store_to
# from ..configs.web_sessions import session_pool

import logging
logger = logging.getLogger(__name__)


# Constants
TIMEOUT_GET_RAW_PROXY = ClientTimeout(total=2)
PROTOCOLS_HTTP = ["https", "http"]  # research more about the different protocols: include to the lecture
PROTOCOLS_SOCK = ["socks5", "socks4"]
PROXY_SOURCES = from_json(Path(__file__).parent / 'sources.json')  # look to README to see more sources; used to receice access to VPN servers via the proxies


async def get_proxies() -> list[dict[str, str | bool]]:
    """
    Orchestrate fetching & parsing all proxy sources.
    Uses asyncio.gather(return_exceptions=True) so one failure doesn’t cancel the rest.
    """

    # TODO: try the use (get) proxies from a file.

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        coros = [_get_raw_proxies(session, source) for source in PROXY_SOURCES]
        raw_proxies: list[dict[str, str | bool]] = await asyncio.gather(*coros, return_exceptions=True)

    unique_proxies: dict[str, dict[str, str | bool]] = dict()  # ip_port: meta dict

    for prox in raw_proxies:
        _proxy_preprocessing(unique_proxies, prox['source'], prox['data'])
    
    if (n_proxies := len(unique_proxies)) == 0:
        logger.warning("🚫 No proxies found. Check sources and code.")
        sys.exit(1)  # terminate with a non-zero exit code

    logger.info(f"✅ Got {n_proxies} proxy node{'s' if n_proxies != 1 else ''}")

    to_json(unique_proxies, full_path='vpn/tmp/sources/proxy.json', suffix=f"{datetime.now():%Y%m%d}", max_files_in_dir=2)
    proxies = _try_many_protocols(unique_proxies)
    return proxies


async def _get_raw_proxies(session: ClientSession, source: str) -> dict[str, str]:
    """
    Fetch the raw text from a single source URL
    """
    try:
        logger.debug(f"Getting proxy data from {source=}")

        async with session.get(PROXY_SOURCES[source], timeout=TIMEOUT_GET_RAW_PROXY) as resp:
            text = await resp.text()
        
        logger.debug(f"✅ Got the proxy data {source=}")
        return {'source': source, 'data': text.strip()}
    
    except TimeoutError as e:
        logger.debug(f"⏳ Timeout:\t{source=}")
    except ClientError as e:
        logger.debug(f"⚠️ HTTP error fetching {source=}", exc_info=True)
    except Exception:
        logger.exception(f"❌ Unexpected error in '_get_raw_proxies' for {source=}")
        raise
    
    return {'source': source, 'data': ''}


def _proxy_preprocessing(proxy_store: dict, source: str, raw_data: str) -> None:
    '''
    clean the responce from proxy sources
    unique_proxies: dict should be empty
    '''
    proxy_pattern = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d+$")  # IP:Port pattern

    try:
        if source.startswith("spysme"):
            raw_data: list = raw_data.splitlines()[6:-2]  # takeoff the header and bottom

            for line in raw_data:
                raw_proxy: list[str] = line.split()

                if not proxy_pattern.match(ip_port := raw_proxy[0]):  # skip non-proxy lines
                    continue

                meta = _pase_spysme_meta(raw_proxy, source)

                if source.endswith("http"):
                    meta['protocol'] = 'https' if meta.get('ssl') else 'http'
                else:  # source.endswith("socks")
                    meta['protocol'] = 'socks5'

                fast_store_to(proxy_store, ip_port, meta)

            
        elif source == "proxifly":
            for url in raw_data.splitlines():
                raw_proxy = url.split('://') 

                fast_store_to(proxy_store,
                    raw_proxy[1],  # ip_port
                    {'protocol': raw_proxy[0], 'source': source}  # meta
                )

        else:
            logger.warning(f"Unrecognized {source=} in '_proxy_preprocessing'")

    except Exception:
        logger.exception(f"❌ Error while preprocessing proxies from {source=}")


def _pase_spysme_meta(raw_proxy: list[str], source: str) -> dict[str, str | bool]:
    raw_meta, google_flag = raw_proxy[1].split('-'), raw_proxy[-1]
    country_code, anonymity_flag = raw_meta[0], raw_meta[1].rstrip('!')
    
    return {  # meta of a proxy
        'country': country_code,                    # str
        'anonymity': anonymity_flag,                # str
        'ssl': len(raw_meta) > 2,                   # bool
        'has_problem': raw_meta[-1].endswith('!'),  # str: look on last char in the last element of raw_meta
        'google_passed': google_flag == '+',        # str
        'source': source                            # str
        }


def _try_many_protocols(proxy_store: dict[str, dict[str, str | bool]]) -> list[dict[str, str | bool]]:
    proxies = []
    for ip_port, meta in proxy_store.items():
        if proto := meta.pop('protocol', None):
            proxies.append({'protocol': proto, 'ip_port': ip_port, 'meta': meta})
        else:
            if meta['source'] == 'spysme_socks':
                proxies.extend([{'protocol': proto, 'ip_port': ip_port, 'meta': meta} for proto in PROTOCOLS_SOCK])

    return proxies

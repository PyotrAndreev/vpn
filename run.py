import asyncio

# from .app.configs.web_sessions import session_pool
from .app.proxy.get import get_proxies
from .app.vpn.get import get_vpns_from_web#, get_vpns_from_local
from .app.configs.file_descriptors import set_fd_limit

import logging
logger = logging.getLogger(__name__)


async def main(use_tor: bool = False) -> None:
    # try:
    # await session_pool.open()
    # print(f'{session_pool._sessions=}')

    if use_tor:
        ...
    else:
        # Fetch all raw proxies
        proxies_meta = await get_proxies()

        # Tweak your FD (file descriptors) limit to allow many proxy connections
        set_fd_limit(n_proxies = len(proxies_meta))
        
        res = await get_vpns_from_web(proxies_meta)

        print(res)
        print(f'{len(res)=}\t{type(res)=}')

    # finally:
    #     await session_pool.close()  # close sockets


if __name__ == "__main__":
    # Pass True here if you want to route over TOR
    asyncio.run(main(use_tor=False))

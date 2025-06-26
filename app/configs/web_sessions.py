import asyncio, aiohttp
import aiohttp_socks


# Constants
TOTAL_LIMIT, PER_HOST_LIMIT = 0, 0
TIMEOUT = aiohttp.ClientTimeout(total=10)


class SessionPool:
    """One aiohttp.ClientSession per proxy protocol."""

    def __init__(self) -> None:
        self._sessions: dict[str, aiohttp.ClientSession] = dict()

    async def open(self) -> None:
        # create connectors (inside pools with sockets)
        http_conn = aiohttp.TCPConnector(limit=TOTAL_LIMIT, limit_per_host=PER_HOST_LIMIT)  # pool: HTTP / HTTPS
        sock_conn = aiohttp_socks.ProxyConnector(limit=TOTAL_LIMIT, limit_per_host=PER_HOST_LIMIT, rdns=False)  # try: rdns=True  # pool: SOCKS 4/4a/5
        # rdns=True => send host names to proxies that support it

        # create sessions: wrap connector + cookies + headers
        h_sess = aiohttp.ClientSession(connector=http_conn, timeout=TIMEOUT, raise_for_status=True)
        s_sess = aiohttp.ClientSession(connector=sock_conn, timeout=TIMEOUT, raise_for_status=True)

        self._sessions.update({"http": h_sess, "https": h_sess, 
                               "socks5": s_sess, "socks5h": s_sess, "socks4a": s_sess, "socks4": s_sess})


    async def close(self) -> None:
        # Guard to prevent leaks. Must: event_loop exists, runned from async code
        # await aiohttp.helpers.assert_asyncio_running()

        await asyncio.gather(*(sess.close() for sess in set(self._sessions.values())))


    def get_session(self, protocol: str) -> aiohttp.ClientSession:
        return self._sessions.get(protocol, self._sessions["http"])
    

session_pool = SessionPool()
    
from typing import Any
import polars as pl

import logging
logger = logging.getLogger(__name__)

from ..utils.files import from_json


def connect_vpn(vpns: dict[str, dict[str, Any]], country: str) -> None:
    # TODO: verify that the connection (tunnel) is established. If not (timeout) then try new connection
    vpns = from_json('tmp/sources/vpn_20250702.json')

    df = _to_polars(vpns)

    country_set = set(df['CountryLong'])

    try
    user_choice = int()

    df_filtered = df.filter(pl.col("CountryLong") == country) \
                    .sort("Score", descending=True)  # TODO: better do Score & NumVpnSessions
    
    print(df_filtered)


    # if df.is_empty(df_filtered):
    #     logger.warning(f"❌ No VPN meets the filter criteria: {country=}")
    #     # input(...)
    # else:
    #     logger.debug(f"✅ Chosen ...")
    #     # connection


def _to_polars(vpns: dict[str, dict[str, Any]]) -> pl.DataFrame:
    # Promote the outer key (IP) to its own column and build a row-list
    vpn_rows = [{"IP": ip, **info} for ip, info in vpns.items()]
    # using column-oriented DF to filter and sort fast
    return pl.DataFrame(vpn_rows)  


def _choose_vpn(country: str) -> ...:
    ...

def _user_choice() -> int:
    return int(input('Enter a country number: '))

def try_connect_ovpn_config(ovpn_text, timeout=60):
    with NamedTemporaryFile("w", suffix=".ovpn", delete=False) as f:
        f.write(ovpn_text)
        ovpn_path = f.name

    try:
        proc = subprocess.Popen(
            ["sudo", "openvpn", "--config", ovpn_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        t_start = time.time()
        while time.time() - t_start < timeout:
            line = proc.stdout.readline()
            if "Initialization Sequence Completed" in line:
                print("[+] Connected successfully!")
                proc.terminate()
                return True
            if "TLS Error" in line or "Connection refused" in line:
                break
        proc.terminate()
        return False
    finally:
        os.remove(ovpn_path)



if __name__ == '__main__':
    connect_vpn({1}, 'US')

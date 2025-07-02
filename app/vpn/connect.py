from types import Any
import polars as pl

import logging
logger = logging.getLogger(__name__)


def connect_vpn(vpns: dict[str, dict[str, Any]], filers: ...) -> None:
    # Promote the outer key (IP) to its own column and build a row-list
    vpn_rows = [{"IP": ip, **info} for ip, info in vpns.items()]

    df = pl.DataFrame(vpn_rows)  # using column-oriented DF to filter and sort fast

    # filtering by CountryShort and take the best by Score + NumVpnSessions

    if df.is_empty():
        ...
        logger.warning(f"❌ No VPN meets the filter criteria: {filers}")
        # input(...)
    else:
        logger.debug(f"✅ Chosen ...")
        # connection




def _choose_vpn() -> ...:
    ...



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
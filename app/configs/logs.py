'''setup_logging() is run in root __init__.py to set up logging in all project'''

import logging
import tomllib
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Path(__file__) is vpn/app/configs/
PKG_ROOT = Path(__file__).parents[2]       # 2 levels up = …/vpn
CONFIG_PATH = PKG_ROOT / "pyproject.toml"  # …/vpn/pyproject.toml


def _load_cfg() -> dict[str, str]:
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)["tool"]["logging"]


def setup_logging() -> None:
    logcfg = _load_cfg()

    log_file = PKG_ROOT / logcfg["file"]
    log_file.parent.mkdir(parents=True, exist_ok=True)   # create 'tmp/logs'

    formatter = logging.Formatter(logcfg["format"])

    # handlers
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file = RotatingFileHandler(
        log_file,
        maxBytes=int(logcfg["max_bytes"]),
        backupCount=int(logcfg["backup_count"]),
        encoding="utf-8",
    )
    file.setFormatter(formatter)

    console.setLevel(logcfg["console_level"])
    file.setLevel(logcfg["level"])

    # root logger
    root = logging.getLogger()
    root.handlers.clear()             # remove default stderr handler installed by basicConfig
    root.setLevel(logcfg["level"])
    root.addHandler(console)
    root.addHandler(file)


if __name__ == '__main__':
    setup_logging()

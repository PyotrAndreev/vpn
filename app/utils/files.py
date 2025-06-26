import sys
import json
from pathlib import Path
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


def to_json(data: list[dict[str, str | bool]], file_name: str) -> None:
    """Serialize *data* (list of dicts) to a UTF-8 JSON file."""
    
    path = _dated_path(file_name)
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        logger.debug(f"📝 Wrote {len(data)} records → {path.relative_to(Path.cwd())}")
        
    except Exception:
        logger.exception(f"❌ Could not write JSON to {path}")
        raise


def from_json(full_path: str | Path) -> dict | list[dict]:
    """
    Load JSON from `full_path`, which may be either:
      • a dict:  { "spysme_socks": "...", ... }
      • a list: [ { "name": "...", "url": "..." }, ... ]
    Returns that dict or list. Exits(1) on any I/O or parse error, or on unexpected shape.
    """

    path = Path(full_path)
    if not path.is_file():
        logger.exception(f"❌ Sources not found: {path=}")
        sys.exit(1)  # terminate with a non-zero exit code
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))  # json.loads(raw_text)

    except Exception:
        logger.exception(f"❌ Failed to read/parse JSON from {path}")
        sys.exit(1)  # terminate with a non-zero exit code

    # Case 1: top‐level dict
    if isinstance(data, dict):
        logger.debug(f"✅ Loaded {len(data)} keys from dict at {path}")
        return data

    # Case 2: list of dicts
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        logger.debug(f"✅ Loaded {len(data)} records from list at {path}")
        return data

    # Anything else is unexpected
    logger.error(f"❌ Unexpected JSON structure in {path!r}: got {type(data).__name__}, expected dict or list of dicts")
    sys.exit(1)
    

def to_csv(data: list[dict[str, str | bool]], full_path: str) -> None:
    """Serialize *data* (list of dicts) to a UTF-8 CSV file."""

    path = Path(full_path)
    ...


def from_csv(full_path: str) -> list[dict[str, str | bool]]:
    path = Path(full_path)
    ...


def _dated_path(file_name: str) -> Path:
    """
    Build     source/YYYYMMDD_<file_name>.json
    """
    date = datetime.now().strftime("%Y%m%d")
    if not file_name.endswith(".json"):
        file_name += ".json"
    
    return Path.cwd() / "source" / f"{date}_{file_name}"


def _del_old_files(max_keep: int = 10) -> None:
    """
    Keep only the newest *max_keep* JSON files in SOURCE_DIR.
    """
    files = sorted(
        SOURCE_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,       # newest first
    )
    for old in files[max_keep:]:
        try:
            old.unlink()
            logger.debug("🗑️  Deleted old file %s", old.name)
        except OSError as exc:
            logger.warning("Could not delete %s: %s", old, exc)


# def parse_with_polars(csv_text: str) -> pl.DataFrame:
    
#     # delete the last * and # in a hedder
#     csv_text = csv_text.rstrip().rstrip('*') \
#         .replace("#", '', count=1)

#     return pl.read_csv(
#         csv_text.encode(),      # feed Polars a bytes buffer
#         skip_rows=1,            # drop your malformed first header row
#         has_header=True         # treat what remains as all data
#     )
import sys
import json
from pathlib import Path
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


def to_json(data: dict | list[dict[str, str | bool]], full_path: str | Path, prefix: str = None, suffix: str = None, max_files_in_dir: int = None) -> None:
    """
    Save a Python dict or list of dicts as JSON to the given path.
    Writing a file with the same name replaces the existing one.
    
    Args:
        with_date: If True, prepend "YYYYMMDD_" to the file name.
        max_files_in_dir: Max files allowed matching name pattern; delete oldest if exceeded.
    """
    # Validate data type
    if not isinstance(data, (dict, list)):
        logger.error(f"❌ Invalid data type: {type(data).__name__}. Expected dict or list of dicts.")
        sys.exit(1)

    full_path = Path(full_path).with_suffix(".json")  # ensure .json extension

    if prefix:  # add 'YYYYMMDD_<file_name>.json' from the given path
        date_full_path = full_path.with_name(f"{prefix}_{full_path.name}")
    if suffix:  # add 'YYYYMMDD_<file_name>.json' from the given path
        date_full_path = full_path.with_name(f"{full_path.stem}_{suffix}{full_path.suffix}")

    try:
        date_full_path.parent.mkdir(parents=True, exist_ok=True)  # ensure the dir exists
        date_full_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.debug(f"📝 Saved JSON with {len(data)} items to {full_path}")

        if max_files_in_dir != None:
            _cleanup_old_files(full_path.parent, full_path.stem, max_files_in_dir)

    except Exception:
        logger.exception(f"❌ Failed to write JSON to {full_path}")
        sys.exit(1)


def from_json(full_path: str | Path) -> dict[str: dict] | list[dict]:
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


def _cleanup_old_files(dir_path: Path, match_term: str, max_files: int) -> None:
    """
    Keep only the newest `max_files` files in the folder that contain `match_term` in the filename.
    Older files are deleted based on creation (modification) time.
    """
    match_files: list[Path] = sorted(dir_path.glob(f"*{match_term}*.json"),  # select matching files
                                     key=lambda file: file.stat().st_mtime)  # sort by modification time (oldest first)
    
    if len(match_files) > max_files:  # delete oldest files if above the limit
        to_delete = match_files[:len(match_files)-max_files]

        for file in to_delete:
            try:
                file.unlink()
                logger.debug(f"🗑️ Deleted: {file}")
            except OSError as exc:
                logger.warning(f"⚠️ Could not delete old {file=} to enforce file limit")

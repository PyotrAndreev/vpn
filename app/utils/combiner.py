from typing import Any, Callable
from datetime import datetime, timedelta
from numbers import Number

import logging
logger = logging.getLogger(__name__)


def fast_store_to(merge_buf: dict[str, dict[str, Any]],
                  key:   str,
                  data:  dict[str, Any]) -> None:
    """
    Insert or merge a single record by key in to a provided buffer.
    Avoiding duplicates.
    """
    
    logger.debug(f"Storing new records with {key=} to a provided buffer")

    if key in merge_buf:
        logger.debug(f"The {key=} alredy in the buffer")
        _merge_existed_rec(merge_buf[key], data)  # store[key] -- existed data, data -- possible new data 
    else:
        merge_buf[key] = data.copy()              # keep your original intact


def _merge_existed_rec(old: dict[str, Any],
                       new: dict[str, Any]) -> None:
    """
    Mutates *old* in-place, merging values from *new*.
    Field-specific rule chosen from MERGE_RULE, else prefer_defined().
    Not saving keys with non-info values
    """
    logger.debug(f"The key already in the buffer. Data resolving...")
    
    for name, new_val in new.items():
        
        if name in ('source', 'protocol'):  # proxy
            # TODO: should be found a better solution
            # the 2 vars of sourse and protocol could be storred to not loss any info 
            continue  # don't change their values

        # logger.debug(f'key {name=}')

        old_val = old.get(name)
        is_old_null = old_val in _NULL_INFO
        is_new_null = new_val in _NULL_INFO

        if is_old_null and is_new_null:    
            continue  # as not info

        if old_val == new_val:
            continue

        if is_old_null ^ is_new_null:  # XOR, if only one contains info
            old[name] = new_val if not is_new_null else old_val
            continue
        
        # both non-empty → resolve conflict
        if type(new_val) is type(old_val):

            if isinstance(new_val, bool):
                logger.debug(f"⚠️ The values have bool types for {name=}; {new_val=} and {old_val=}. Resolve it in code.")
                # TODO: should be found a better solution
                continue  # don't see the univertial correct rule
            else:
                if rule := MERGE_RULE.get(type(new_val), default_rule):
                    old[name] = rule(old_val, new_val)

        else:
            logger.debug(f"⚠️ The values have different types for {name=}: {type(new_val)=} and {type(old_val)=}; {new_val=} and {old_val=}. Resolve it in code.")
            # TODO: should be found a better solution
            continue  # don't see the univertial correct rule


_NULL_INFO = frozenset({None, '', (), b'', memoryview(b'')})  # , [], set(), {}, bytearray(b'')  # for not hashable, use tuple -> losing O(1)
# do not include: 0, False. It is info.

### --- rules --- ### 

def longer(new: str, old: str) -> str:
    """Return the longer of two strings (≥ keeps new)."""
    chosen = new if len(new) >= len(old) else old
    logger.debug(f"📄 longer(): picked {chosen!r} over {(old if chosen is new else new)!r}")
    return chosen

def larger(new: Number, old: Number) -> Number:
    """Return the larger numeric value."""
    chosen = new if new >= old else old
    logger.debug(f"🔢 larger(): picked {chosen!r} over {(old if chosen is new else new)!r}")
    return chosen

def smaller(new: Number, old: Number) -> Number:
    """Return the smaller numeric value."""
    chosen = new if new <= old else old
    logger.debug(f"🔢 smaller(): picked {chosen!r} over {(old if chosen is new else new)!r}")
    return chosen

def union_sets(new, old):
    """Return union of two sets (or frozensets)."""
    merged = new | old
    logger.debug(f"🔗 union_sets(): |{len(new)}|∪|{len(old)}| → |{len(merged)}|")
    return merged

def concat_seq(new, old):
    """Concatenate lists/tuples preserving type."""
    merged = (*new, *old) if isinstance(new, tuple) else new + old
    logger.debug(f"➕ concat_seq(): len {len(new)} + {len(old)} → {len(merged)}")
    return merged

def newer(new: datetime, old: datetime) -> datetime:
    """Return the newer (later) datetime."""
    chosen = new if new >= old else old
    logger.debug(f"⏰ newer(): picked {chosen!r} over {(old if chosen is new else new)!r}")
    return chosen

# fallback when no rule found
def default_rule(new, old) -> None:
    logger.warning(f"⚠️  No rule for type {type(old)=}. Skip the merging. Resolve it in code.")


MERGE_RULE: dict[type, Callable[[Any, Any], Any]] = {
    
    # consider more info in longer str, could be problem with different string dates
    str:            longer,
    bytes:          longer,
    bytearray:      longer,
    memoryview:     longer,
    
    # should be optimiset for a tast
    # list:           concat_seq,  
    # tuple:          concat_seq,

    set:            union_sets,
    frozenset:      union_sets,
    dict:           lambda a, b: {**a, **b},

    datetime:       newer,
    timedelta:      larger,

    # save the peak value
    int:            larger,  
    float:          larger,
}

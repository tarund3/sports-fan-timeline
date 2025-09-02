from __future__ import annotations
import re
from typing import List, Dict

CLEAN_RE = re.compile(r"\s+")
URL_RE = re.compile(r"https?://\S+")
CODE_RE = re.compile(r"`[^`]+`")
QUOTE_RE = re.compile(r">+\s.*$", re.MULTILINE)

def clean_text(s: str) -> str:
    """Lightweight cleaning for Reddit comment bodies."""
    s = URL_RE.sub("", s)
    s = CODE_RE.sub("", s)
    s = QUOTE_RE.sub("", s)
    s = s.replace("\u00a0", " ")
    s = CLEAN_RE.sub(" ", s).strip()
    return s

def truncate_tokens(s: str, max_chars: int) -> str:
    return s if len(s) <= max_chars else s[:max_chars]

def mmss_to_secs(mmss: str) -> int:
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)

def secs_to_mmss(x: int) -> str:
    m = x // 60
    s = x % 60
    return f"{m:02d}:{s:02d}"

"""Crawl person pages on sites found by widepatrol (multi-language person-URL pattern)."""
import sys

from . import firmcrawl
from .widepatrol import WIDE

if __name__ == "__main__":
    firmcrawl.crawl(sys.argv[2:], int(sys.argv[1]) if sys.argv[1] != "0" else None, pat=WIDE)

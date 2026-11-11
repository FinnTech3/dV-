"""Crawl the people pages of member-company sites discovered by snowball.py (small-site profile pattern)."""
import sys

from . import firmcrawl

if __name__ == "__main__":
    firmcrawl.crawl(sys.argv[2:], int(sys.argv[1]), pat=firmcrawl.SMALL_SITE_PAT)

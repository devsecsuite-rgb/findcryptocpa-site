#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://findcryptocpa.com"

# Static pages — add new ones here if you create them
STATIC_URLS = [
    "/",
    "/tool/",
    "/about/",
    "/contact/",
    "/privacy/",
    "/terms/",
    "/specializations/defi/",
    "/specializations/nft/",
    "/specializations/mining-staking/",
    "/specializations/audit-defense/",
    "/specializations/business/",
    "/specializations/trading/",
    "/specializations/international/",
    "/specializations/individuals/",
]

# Pages we do NOT want in the sitemap
EXCLUDE_SLUGS = {"thank-you"}


def build_sitemap():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls = []

    # Static pages
    for path in STATIC_URLS:
        urls.append(f"{BASE}{path}")

    # State pages — auto-discovered
    state_dir = ROOT / "crypto-tax-cpa"
    if state_dir.exists():
        for p in sorted(state_dir.glob("*/index.html")):
            slug = p.parent.name
            if slug in EXCLUDE_SLUGS:
                continue
            urls.append(f"{BASE}/crypto-tax-cpa/{slug}/")

    # Build XML
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in urls:
        lines.append(f"  <url>")
        lines.append(f"    <loc>{u}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append(f"  </url>")
    lines.append("</urlset>")
    lines.append("")

    return "\n".join(lines), len(urls)


def main():
    content, count = build_sitemap()
    SITEMAP.write_text(content, encoding="utf-8")
    print(f"Rebuilt sitemap.xml with {count} URLs")


if __name__ == "__main__":
    main()

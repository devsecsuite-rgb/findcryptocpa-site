#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://findcryptocpa.com"

def main():
    if not SITEMAP.exists():
        print("No sitemap.xml found. Skipping.")
        return

    urls = []
    for p in sorted((ROOT / "crypto-tax-cpa").glob("*/index.html")):
        slug = p.parent.name
        urls.append(f"{BASE}/crypto-tax-cpa/{slug}/")

    content = SITEMAP.read_text(encoding='utf-8')
    block = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)

    if '<!-- STATE_PAGES -->' not in content:
        print("WARNING: sitemap.xml missing <!-- STATE_PAGES --> markers. Add them first.")
        return

    content = re.sub(
        r'<!-- STATE_PAGES -->.*?<!-- /STATE_PAGES -->',
        f'<!-- STATE_PAGES -->\n{block}\n  <!-- /STATE_PAGES -->',
        content,
        flags=re.S
    )
    SITEMAP.write_text(content, encoding='utf-8')
    print(f"Updated sitemap with {len(urls)} state pages")

if __name__ == '__main__':
    main()

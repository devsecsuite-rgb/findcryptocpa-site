#!/usr/bin/env python3
import os
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://findcryptocpa.com"
TODAY = date.today().isoformat()

def generate_sitemap():
    urls = []
    
    # 1. Add Homepage
    urls.append(f"{DOMAIN}/")
    
    # 2. Find all index.html files in the root and subdirectories
    exclude_dirs = {'scripts', 'data', 'templates', '.git', '.github'}
    
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        if 'index.html' in files:
            rel_path = Path(root).relative_to(ROOT)
            if str(rel_path) == '.':
                continue # Skip root, already added
            
            # Clean up the URL path (e.g., /about/index.html -> /about/)
            url_path = f"/{rel_path.as_posix()}/"
            urls.append(f"{DOMAIN}{url_path}")

    # 3. Build the XML
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for url in sorted(set(urls)):
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{url}</loc>")
        xml_lines.append(f"    <lastmod>{TODAY}</lastmod>")
        xml_lines.append("  </url>")
        
    xml_lines.append('</urlset>')
    
    # 4. Write to sitemap.xml
    sitemap_path = ROOT / "sitemap.xml"
    sitemap_path.write_text("\n".join(xml_lines), encoding="utf-8")
    print(f"✅ Sitemap generated with {len(urls)} URLs at {sitemap_path}")

if __name__ == "__main__":
    generate_sitemap()
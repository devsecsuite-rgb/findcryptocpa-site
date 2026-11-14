#!/usr/bin/env python3
import os
import sys
import re
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from xml.etree import ElementTree
from collections import defaultdict

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install beautifulsoup4")
    from bs4 import BeautifulSoup

SITE_URL = os.environ.get("SITE_URL", "https://findcryptocpa.com")
SITEMAP_URL = f"{SITE_URL}/sitemap.xml"
REPORT_FILE = "seo_report.json"
UA = "Mozilla/5.0 (compatible; SEOAuditBot/2.0)"
PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", "")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")

def get_sitemap_urls():
    try:
        status, xml = fetch(SITEMAP_URL)
        root = ElementTree.fromstring(xml)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        return [loc.text for loc in root.findall(".//sm:loc", ns)]
    except Exception as e:
        print(f"Sitemap failed: {e}")
        return []

def validate_schema_fields(soup, url):
    schemas = soup.find_all("script", attrs={"type": "application/ld+json"})
    issues = []
    has_faq = False
    
    for script in schemas:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if data.get("@type") == "FAQPage":
                    has_faq = True
                    for item in data.get("mainEntity", []):
                        if "acceptedAnswer" not in item:
                            issues.append(f"Schema: FAQ Question missing acceptedAnswer")
        except Exception:
            issues.append("Schema: Invalid JSON-LD syntax found")
    
    return issues, has_faq

def check_headings(soup):
    issues = []
    headings = soup.find_all(re.compile('^h[1-6]$'))
    if not headings:
        return issues

    last_level = 0
    for h in headings:
        current_level = int(h.name[1])
        if last_level > 0 and current_level > last_level + 1:
            issues.append(f"Heading hierarchy skipped H{last_level} to H{current_level}")
        last_level = current_level
    return issues

def check_images(soup):
    warnings = []
    images = soup.find_all("img")
    missing_alt = 0
    missing_dims = 0
    
    for img in images:
        if not img.get("alt"):
            missing_alt += 1
        if not img.get("width") or not img.get("height"):
            missing_dims += 1
            
    if missing_alt > 0:
        warnings.append(f"{missing_alt} images missing 'alt' text")
    if missing_dims > 0:
        warnings.append(f"{missing_dims} images missing explicit 'width'/'height' attributes")
    return warnings

def audit_page(url):
    issues = []
    warnings = []
    score = 100
    internal_links = []

    try:
        status, html = fetch(url)
    except Exception as e:
        return {"url": url, "score": 0, "issues": [f"Fetch failed: {e}"], "warnings": [], "links": []}

    if status != 200:
        return {"url": url, "score": 0, "issues": [f"HTTP {status}"], "warnings": [], "links": []}

    soup = BeautifulSoup(html, "html.parser")

    # 1. Title
    title = soup.find("title")
    if not title or not title.text.strip():
        issues.append("Missing or empty <title>")
        score -= 15
    elif len(title.text) > 65:
        warnings.append(f"Title too long ({len(title.text)} chars)")
        score -= 3

    # 2. Meta
    desc = soup.find("meta", attrs={"name": "description"})
    if not desc or not desc.get("content", "").strip():
        issues.append("Missing meta description")
        score -= 15

    # 3. Headings
    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        issues.append("Missing H1")
        score -= 15
        
    heading_issues = check_headings(soup)
    for issue in heading_issues:
        warnings.append(issue)
        score -= 2

    # 4. Canonical
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if not canonical:
        issues.append("Missing canonical tag")
        score -= 10

    # 5. Schema
    jsonld_issues, has_faq = validate_schema_fields(soup, url)
    for issue in jsonld_issues:
        issues.append(issue)
        score -= 5
    
    if not soup.find_all("script", attrs={"type": "application/ld+json"}):
        warnings.append("No JSON-LD structured data found")
        score -= 5

    # 6. Images
    img_warnings = check_images(soup)
    for w in img_warnings:
        warnings.append(w)
        score -= 2

    # 7. Thin Content
    body = soup.find("body")
    if body:
        text = body.get_text(separator=" ", strip=True)
        words = len(text.split())
        if words < 300:
            issues.append(f"THIN CONTENT: Only {words} words")
            score -= 20
        elif words < 600 and "/crypto-tax-cpa/" not in url:
            warnings.append(f"Content could be deeper ({words} words)")
            score -= 5

    # 8. Collect Links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urllib.parse.urljoin(url, href)
        if full_url.startswith(SITE_URL):
            internal_links.append(full_url.split("#")[0].split("?")[0])

    return {
        "url": url,
        "score": max(0, score),
        "issues": issues,
        "warnings": warnings,
        "links": list(set(internal_links))
    }

def main():
    print(f"Auditing {SITE_URL}")
    urls = get_sitemap_urls()
    if not urls:
        print("No URLs found in sitemap. Aborting.")
        sys.exit(1)

    print(f"Found {len(urls)} URLs\n")
    results = []
    total_score = 0
    critical_count = 0
    
    inbound_links = defaultdict(int)
    all_discovered_links = set()

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        result = audit_page(url)
        results.append(result)
        total_score += result["score"]
        
        for issue in result["issues"]:
            print(f"  ISSUE: {issue}")
            critical_count += 1
        for warning in result["warnings"]:
            print(f"  WARN: {warning}")
        print(f"  Score: {result['score']}/100\n")
        
        for link in result.get("links", []):
            inbound_links[link] += 1
            all_discovered_links.add(link)
            
        time.sleep(0.3)

    print("=" * 60)
    print("POST-PROCESSING: INTERNAL LINKING")
    
    orphans = []
    for url in urls:
        if url.rstrip("/") != SITE_URL.rstrip("/") and "/thank-you/" not in url:
            if inbound_links[url] == 0:
                orphans.append(url)
                print(f"  ORPHAN PAGE: {url} (0 inbound internal links)")
                critical_count += 1

    print("\nChecking for broken internal links...")
    broken_links = []
    links_to_check = [l for l in all_discovered_links if l in urls or l + "/" in urls]
    
    for link in links_to_check:
        try:
            req = urllib.request.Request(link, method="HEAD", headers={"User-Agent": UA})
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as e:
            if e.code >= 400:
                broken_links.append({"url": link, "status": e.code})
                print(f"  BROKEN LINK: {link} (HTTP {e.code})")
                critical_count += 1
        except Exception:
            pass

    avg_score = total_score / len(results) if results else 0

    report = {
        "site": SITE_URL,
        "audited_at": datetime.utcnow().isoformat() + "Z",
        "pages_audited": len(results),
        "average_score": round(avg_score, 1),
        "critical_issues": critical_count,
        "orphans": orphans,
        "broken_links": broken_links,
        "results": results,
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print(f"AVERAGE SCORE: {avg_score:.1f}/100 across {len(results)} pages")
    print(f"Critical issues: {critical_count}")
    print(f"Orphan pages found: {len(orphans)}")
    print(f"Broken internal links found: {len(broken_links)}")
    print(f"Report saved to {REPORT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
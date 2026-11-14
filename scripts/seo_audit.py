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
# Optional: Add a Google Cloud API Key to .env or your shell to enable Core Web Vitals checking
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
    """Parses JSON-LD to ensure required fields exist."""
    schemas = soup.find_all("script", attrs={"type": "application/ld+json"})
    issues = []
    has_faq = False
    has_article = False

    for script in schemas:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                # Check FAQPage
                if data.get("@type") == "FAQPage":
                    has_faq = True
                    for item in data.get("mainEntity", []):
                        if "acceptedAnswer" not in item:
                            issues.append(f"Schema: FAQ Question '{item.get('name', 'Unknown')}' missing acceptedAnswer")
                
                # Check Article (for E-E-A-T)
                if data.get("@type") in ["Article", "NewsArticle", "BlogPosting"]:
                    has_article = True
                    if not data.get("author"):
                        issues.append("Schema: Article missing 'author' field (E-E-A-T issue)")
                    if not data.get("datePublished"):
                        issues.append("Schema: Article missing 'datePublished' field")
        except Exception:
            issues.append("Schema: Invalid JSON-LD syntax found")
    
    return issues, has_faq, has_article

def check_headings(soup):
    """Checks for skipped heading levels (e.g., H1 -> H3)."""
    issues = []
    headings = soup.find_all(re.compile('^h[1-6]$'))
    if not headings:
        return issues

    last_level = 0
    for h in headings:
        current_level = int(h.name[1])
        # Allow going up any number of levels, but only down by 1
        if last_level > 0 and current_level > last_level + 1:
            issues.append(f"Heading hierarchy skipped H{last_level} to H{current_level}")
        last_level = current_level
    return issues

def check_images(soup):
    """Checks for missing alt text and width/height attributes."""
    issues = []
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
    return issues, warnings

def check_eeat_visible(soup, url):
    """Checks for visible author/date signals on guides."""
    issues = []
    if "/guides/" in url:
        text = soup.get_text().lower()
        if "written by" not in text and "author" not in text and "reviewed by" not in text:
            issues.append("E-E-A-T: Missing visible author/reviewer signal on guide")
    return issues

def check_core_web_vitals(url):
    """Calls PageSpeed Insights API if key is present."""
    if not PAGESPEED_API_KEY:
        return None
    try:
        endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={PAGESPEED_API_KEY}&strategy=desktop"
        req = urllib.request.Request(endpoint)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            lcp = data.get("lighthouseResult", {}).get("audits", {}).get("largest-contentful-paint", {}).get("numericValue", 0)
            cls = data.get("lighthouseResult", {}).get("audits", {}).get("cumulative-layout-shift", {}).get("numericValue", 0)
            
            issues = []
            if lcp > 2500:
                issues.append(f"Core Web Vitals: LCP is slow ({lcp/1000:.1f}s > 2.5s)")
            if cls > 0.1:
                issues.append(f"Core Web Vitals: CLS is high ({cls:.2f} > 0.1)")
            return issues
    except Exception:
        return None

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

    # 1. Title Tag
    title = soup.find("title")
    if not title or not title.text.strip():
        issues.append("Missing or empty <title>")
        score -= 15
    elif len(title.text) > 65:
        warnings.append(f"Title too long ({len(title.text)} chars)")
        score -= 3
    elif len(title.text) < 30:
        warnings.append(f"Title too short ({len(title.text)} chars)")
        score -= 2

    # 2. Meta Description
    desc = soup.find("meta", attrs={"name": "description"})
    if not desc or not desc.get("content", "").strip():
        issues.append("Missing meta description")
        score -= 15
    elif len(desc["content"]) > 165:
        warnings.append(f"Meta description too long ({len(desc['content'])} chars)")
        score -= 3

    # 3. H1 & Heading Hierarchy
    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        issues.append("Missing H1")
        score -= 15
    elif len(h1s) > 1:
        warnings.append(f"Multiple H1 tags ({len(h1s)})")
        score -= 5
        
    heading_issues = check_headings(soup)
    for issue in heading_issues:
        warnings.append(issue)
        score -= 2

    # 4. Canonical
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if not canonical:
        issues.append("Missing canonical tag")
        score -= 10

    # 5. OG Tags
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    og_image = soup.find("meta", attrs={"property": "og:image"})
    missing_og = [n for n, v in [("og:title", og_title), ("og:description", og_desc), ("og:image", og_image)] if not v]
    if missing_og:
        warnings.append(f"Missing OG tags: {', '.join(missing_og)}")
        score -= 5

    # 6. Robots Meta
    robots = soup.find("meta", attrs={"name": "robots"})
    if robots and "noindex" in robots.get("content", "").lower():
        if "/thank-you/" not in url:
            issues.append("CRITICAL: noindex directive")
            score -= 50

    # 7. JSON-LD Schema Validation
    jsonld_issues, has_faq, has_article = validate_schema_fields(soup, url)
    for issue in jsonld_issues:
        issues.append(issue)
        score -= 5
    
    if not soup.find_all("script", attrs={"type": "application/ld+json"}):
        warnings.append("No JSON-LD structured data found")
        score -= 5
    elif "/guides/" in url or "/specializations/" in url:
        if not has_faq:
            warnings.append("Missing FAQPage schema on a guide/specialization page")
            score -= 5

    # 8. E-E-A-T Visible Signals
    eeat_issues = check_eeat_visible(soup, url)
    for issue in eeat_issues:
        warnings.append(issue)
        score -= 5

    # 9. Viewport & HTTPS
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        issues.append("Missing viewport meta tag")
        score -= 10

    if not url.startswith("https://"):
        issues.append("Not served over HTTPS")
        score -= 20

    # 10. Images
    img_issues, img_warnings = check_images(soup)
    for w in img_warnings:
        warnings.append(w)
        score -= 2

    # 11. Thin Content
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

    # 12. Core Web Vitals (Optional)
    cwv_issues = check_core_web_vitals(url)
    if cwv_issues:
        for issue in cwv_issues:
            issues.append(issue)
            score -= 10

    # 13. Collect Internal Links for Orphan/Broken Check
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Resolve relative URLs to absolute
        full_url = urllib.parse.urljoin(url, href)
        # Only keep internal links
        if full_url.startswith(SITE_URL):
            internal_links.append(full_url.split("#")[0].split("?")[0]) # Remove anchors/queries

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
    
    # Link Graph variables
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
        
        # Build Link Graph
        for link in result.get("links", []):
            inbound_links[link] += 1
            all_discovered_links.add(link)
            
        time.sleep(0.3)

    # Post-Processing: Find Orphans
    print("=" * 60)
    print("POST-PROCESSING: INTERNAL LINKING")
    
       orphans = []
    for url in urls:
        # Ignore homepage and thank-you page for orphan check
        if url.rstrip("/") != SITE_URL.rstrip("/") and "/thank-you/" not in url:
            if inbound_links[url] == 0:
                orphans.append(url)
                print(f"  ORPHAN PAGE: {url} (0 inbound internal links)")
                critical_count += 1

    # Post-Processing: Check for Broken Internal Links
    print("\nChecking for broken internal links...")
    broken_links = []
    # Only check links we discovered that are part of our sitemap to save time
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
            pass # Timeouts or connection errors

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
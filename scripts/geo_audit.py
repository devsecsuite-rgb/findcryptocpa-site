#!/usr/bin/env python3
import os
import re
import json
import urllib.request
import urllib.error
import time
from xml.etree import ElementTree

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install beautifulsoup4")
    from bs4 import BeautifulSoup

SITE_URL = os.environ.get("SITE_URL", "https://findcryptocpa.com")
SITEMAP_URL = f"{SITE_URL}/sitemap.xml"
REPORT_FILE = "geo_report.json"

AI_CRAWLERS = [
    "GPTBot", "ChatGPT-User", "ClaudeBot", "Claude-Web", "PerplexityBot",
    "Google-Extended", "anthropic-ai", "CCBot", "Bytespider", "Amazonbot",
]

UA = "Mozilla/5.0 (compatible; GEOAuditBot/2.0)"

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

def check_robots():
    print("\n=== AI CRAWLER ACCESS ===")
    try:
        status, robots = fetch(f"{SITE_URL}/robots.txt")
    except Exception as e:
        return {"error": str(e), "blocked": []}

    blocked = []
    for crawler in AI_CRAWLERS:
        pattern = rf"User-agent:\s*{crawler}\s*\n(.*?)(?=\nUser-agent|\Z)"
        match = re.search(pattern, robots, re.IGNORECASE | re.DOTALL)
        if match and "Disallow: /" in match.group(1):
            blocked.append(crawler)
            print(f"  BLOCKED: {crawler}")
        else:
            print(f"  Allowed: {crawler}")

    return {"blocked": blocked}

def check_llms_txt():
    print("\n=== LLMS.TXT ===")
    try:
        status, content = fetch(f"{SITE_URL}/llms.txt")
        if status == 200:
            lines = content.split("\n")
            print(f"  Found ({len(lines)} lines)")
            return {"found": True, "lines": len(lines)}
    except Exception:
        pass
    print("  Missing (CRITICAL for AI Search)")
    return {"found": False}

def check_schema(soup, url):
    print("\n=== SCHEMA VALIDATION ===")
    schemas = []
    faq_valid = False
    has_article = False
    
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if "@graph" in data:
                    for node in data["@graph"]:
                        schema_type = node.get("@type", "Unknown")
                        schemas.append(schema_type)
                        if schema_type == "FAQPage" and "mainEntity" in node:
                            faq_valid = True
                        if schema_type in ["Article", "BlogPosting", "NewsArticle"]:
                            has_article = True
                else:
                    schema_type = data.get("@type", "Unknown")
                    schemas.append(schema_type)
                    if schema_type == "FAQPage" and "mainEntity" in data:
                        faq_valid = True
                    if schema_type in ["Article", "BlogPosting", "NewsArticle"]:
                        has_article = True
        except Exception:
            pass
    
    print(f"  Schema types found: {', '.join(schemas) if schemas else 'None'}")
    
    if "/guides/" in url or "/specializations/" in url:
        if not faq_valid:
            print("  WARNING: Missing valid FAQPage schema (AI extraction risk)")
        if not has_article:
            print("  WARNING: Missing Article schema (AI citation risk)")
    
    return schemas

def check_direct_answers(soup):
    """AI engines prefer short, direct answers immediately following a heading."""
    print("\n=== DIRECT ANSWER FORMAT ===")
    direct_answers = 0
    headings = soup.find_all(["h2", "h3"])
    
    for h in headings:
        # Get the immediate next sibling paragraph
        next_node = h.find_next_sibling()
        if next_node and next_node.name == "p":
            word_count = len(next_node.get_text().split())
            if word_count < 50:  # Sweet spot for AI snippets
                direct_answers += 1
                
    print(f"  Found {direct_answers} headings with short direct answers (<50 words).")
    return direct_answers

def check_citability(soup):
    print("\n=== CITABILITY & DATA ===")
    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return {"score": 0, "notes": ["No main content found"]}

    notes = []
    score = 100

    # 1. Tables (AI loves tables)
    tables = main.find_all("table")
    if len(tables) >= 1:
        notes.append(f"{len(tables)} data table(s) found (Great for AI)")
    else:
        notes.append("No data tables found (AI prefers structured data)")
        score -= 10

    # 2. Statistics
    text = main.get_text()
    stats = len(re.findall(r"\$[\d,]+|\d+%|\d+\.\d+|\d+ (?:billion|million|thousand)", text))
    if stats < 5:
        notes.append(f"Only {stats} statistics found (AI engines prefer data)")
        score -= 10
    else:
        notes.append(f"{stats} statistics found")

    # 3. Lists
    lists = main.find_all(["ul", "ol"])
    if len(lists) < 2:
        notes.append(f"Only {len(lists)} lists (AI engines prefer bullet points)")
        score -= 5
    else:
        notes.append(f"{len(lists)} lists found")

    # 4. Outbound Citations (.gov / .edu)
    outbound_links = main.find_all("a", href=True)
    authoritative_links = [a['href'] for a in outbound_links if '.gov' in a['href'] or '.edu' in a['href']]
    if len(authoritative_links) > 0:
        notes.append(f"{len(authoritative_links)} authoritative outbound links (.gov/.edu) found")
    else:
        notes.append("No authoritative (.gov/.edu) outbound links found")
        score -= 5

    print(f"  Citability score: {max(0, score)}/100")
    for note in notes:
        print(f"    - {note}")

    return {"score": max(0, score), "notes": notes}

def audit_page(url):
    print(f"\n{'=' * 60}")
    print(f"PAGE: {url}")
    print(f"{'=' * 60}")

    try:
        status, html = fetch(url)
    except Exception as e:
        print(f"  Failed: {e}")
        return {"url": url, "error": str(e)}

    soup = BeautifulSoup(html, "html.parser")
    schemas = check_schema(soup, url)
    direct_answers = check_direct_answers(soup)
    citability = check_citability(soup)

    return {
        "url": url,
        "schemas": schemas,
        "direct_answers": direct_answers,
        "citability_score": citability["score"],
        "citability_notes": citability["notes"],
    }

def main():
    print(f"\n{'#' * 60}")
    print(f"# GEO AUDIT v2.0: {SITE_URL}")
    print(f"# {time.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#' * 60}")

    robots = check_robots()
    llms = check_llms_txt()

    urls = get_sitemap_urls()
    print(f"\n\nFound {len(urls)} pages in sitemap\n")

    results = []
    total = 0
    for url in urls:
        result = audit_page(url)
        results.append(result)
        if "citability_score" in result:
            total += result["citability_score"]
        time.sleep(0.3)

    avg = total / len(results) if results else 0

    print(f"\n\n{'=' * 60}")
    print(f"SITE-LEVEL SUMMARY")
    print(f"{'=' * 60}")
    print(f"AI crawlers blocked: {len(robots.get('blocked', []))}")
    print(f"llms.txt present: {llms.get('found', False)}")
    print(f"Average citability: {avg:.1f}/100")
    print(f"Pages audited: {len(results)}")

    report = {
        "site": SITE_URL,
        "audited_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "robots": robots,
        "llms_txt": llms,
        "avg_citability": avg,
        "pages": results,
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to {REPORT_FILE}")

if __name__ == "__main__":
    main()
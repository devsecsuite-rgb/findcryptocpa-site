#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.parse
from collections import defaultdict
from difflib import SequenceMatcher

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install beautifulsoup4")
    from bs4 import BeautifulSoup

# CONFIGURATION
SITEMAP_URL = "https://findcryptocpa.com/sitemap.xml"
BASE_URL = "https://findcryptocpa.com"
REPORT_FILE = "topical_authority_report.json"
UA = "Mozilla/5.0 (compatible; TopicalAuthorityBot/1.0)"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")

def get_sitemap_urls():
    try:
        xml = fetch(SITEMAP_URL)
        # Simple regex extraction to avoid XML namespace complexity
        import re
        return re.findall(r'<loc>(.*?)</loc>', xml)
    except Exception as e:
        print(f"Sitemap failed: {e}")
        return []

def analyze_page(url):
    try:
        html = fetch(url)
    except Exception as e:
        return None

    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Basic Extraction
    title = soup.title.string if soup.title else ""
    h1 = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
    
       # Remove scripts and styles for word count, but KEEP header/footer for link graph
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    word_count = len(text.split())
    
    # 2. Internal Links
    internal_links = []
    for a in soup.find_all("a", href=True):
        full_url = urllib.parse.urljoin(url, a["href"])
        if full_url.startswith(BASE_URL) and full_url != url:
            # Remove fragments/queries for clean graph
            clean_url = full_url.split("#")[0].split("?")[0]
            internal_links.append(clean_url)
            
    # 3. E-E-A-T Signals (Schema + Visible)
    schemas = soup.find_all("script", type="application/ld+json")
    has_author_schema = False
    has_date_schema = False
    for s in schemas:
        try:
            data = json.loads(s.string)
            if isinstance(data, dict):
                if "author" in data or (data.get("@graph") and any("author" in n for n in data["@graph"])):
                    has_author_schema = True
                if "datePublished" in data or (data.get("@graph") and any("datePublished" in n for n in data["@graph"])):
                    has_date_schema = True
        except:
            pass
            
    # Visible check (simplified)
    text_lower = text.lower()
    has_visible_author = "written by" in text_lower or "reviewed by" in text_lower
    has_visible_date = "last updated" in text_lower or "published" in text_lower

    return {
        "url": url,
        "title": title,
        "h1": h1,
        "word_count": word_count,
        "internal_links": list(set(internal_links)), # Unique outbound links
        "has_author": has_author_schema or has_visible_author,
        "has_date": has_date_schema or has_visible_date,
    }

def main():
    print("🚀 Starting Topical Authority Audit...")
    urls = get_sitemap_urls()
    if not urls:
        print("No URLs found. Aborting.")
        sys.exit(1)

    pages = {}
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Analyzing {url}")
        data = analyze_page(url)
        if data:
            pages[url] = data

    # --- GRAPH ANALYSIS ---
    inbound_links = defaultdict(int)
    outbound_links = {}
    
    for url, data in pages.items():
        outbound_links[url] = data["internal_links"]
        for link in data["internal_links"]:
            if link in pages:
                inbound_links[link] += 1

    # 1. Orphan Pages (Zero inbound internal links)
    # Exclude homepage and utility pages
    orphans = [u for u in pages if inbound_links[u] == 0 and u != BASE_URL + "/" and "/thank-you" not in u]

    # 2. Hub-Spoke Coverage (Do spokes link to hubs?)
    # Hubs are defined as /guides/ or /specializations/
    hubs = [u for u in pages if "/guides/" in u or "/specializations/" in u]
    spokes = [u for u in pages if u not in hubs]
    
    spoke_links_to_hub = 0
    for spoke in spokes:
        if any(hub in outbound_links[spoke] for hub in hubs):
            spoke_links_to_hub += 1
            
    # 3. Link Density
    total_outbound = sum(len(links) for links in outbound_links.values())
    avg_outbound = total_outbound / len(pages) if pages else 0

    # 4. Content Depth Multiplier
    # Based on established research: <500 (0.5), 500-1500 (1.0), 1500-3000 (1.2), 3000+ (1.5)
    depth_scores = []
    for u, d in pages.items():
        wc = d["word_count"]
        if wc < 500: depth_scores.append(0.5)
        elif wc < 1500: depth_scores.append(1.0)
        elif wc < 3000: depth_scores.append(1.2)
        else: depth_scores.append(1.5)
    avg_depth = sum(depth_scores) / len(depth_scores) if depth_scores else 0

    # 5. Cannibalization Detection (Title similarity > 70%, ignoring state pages)
    cannibal_pairs = []
    url_list = list(pages.keys())
    for i, u1 in enumerate(url_list):
        # Skip state pages for cannibalization check
        if "/crypto-tax-cpa/" in u1:
            continue
        for u2 in url_list[i+1:]:
            if "/crypto-tax-cpa/" in u2:
                continue
            t1 = pages[u1]["title"].replace("- FindCryptoCPA", "").replace("— FindCryptoCPA", "").strip()
            t2 = pages[u2]["title"].replace("- FindCryptoCPA", "").replace("— FindCryptoCPA", "").strip()
            sim = SequenceMatcher(None, t1, t2).ratio()
            if sim > 0.7:
                cannibal_pairs.append({"page_a": u1, "page_b": u2, "similarity": round(sim, 2)})

    # 6. Trust Signals (E-E-A-T)
    trust_count = sum(1 for d in pages.values() if d["has_author"] and d["has_date"])
    trust_ratio = trust_count / len(pages) if pages else 0

    # --- SCORING (0-100) ---
    # Weights based on the 30-point framework (Coverage 25, Arch 25, Trust 25, Focus 25)
    
    # A. Coverage Score (Depth)
    # Target avg_depth = 1.2 (Deep). Max score at 1.5.
    coverage_score = min(100, (avg_depth / 1.5) * 100)
    
    # B. Architecture Score
    # Ideal avg_outbound is 4. Ideal spoke_to_hub is 100%. Ideal orphans is 0.
    link_score = min(100, (avg_outbound / 4.0) * 100)
    hub_score = (spoke_links_to_hub / len(spokes) * 100) if spokes else 100
    orphan_penalty = min(100, len(orphans) * 20)
    arch_score = max(0, (link_score + hub_score - orphan_penalty) / 2)
    
    # C. Trust Score (E-E-A-T)
    # Need both author and date on all pages.
    trust_score = trust_ratio * 100
    
    # D. Focus Score (Cannibalization)
    # Start at 100, deduct 10 for every similar pair found.
    focus_score = max(0, 100 - (len(cannibal_pairs) * 10))
    
    # OVERALL
    overall = (coverage_score * 0.3) + (arch_score * 0.3) + (trust_score * 0.2) + (focus_score * 0.2)

    # --- REPORTING ---
    print("\n" + "="*60)
    print("TOPICAL AUTHORITY SCORECARD")
    print("="*60)
    print(f"Overall Score: {overall:.1f}/100\n")
    
    print(f"1. CONTENT DEPTH (Weight 30%): {coverage_score:.1f}/100")
    print(f"   - Average Depth Multiplier: {avg_depth:.2f}x (Target: 1.2x+)")
    print(f"   - Pages under 500 words: {sum(1 for d in pages.values() if d['word_count'] < 500)}")
    
    print(f"\n2. ARCHITECTURE (Weight 30%): {arch_score:.1f}/100")
    print(f"   - Avg Internal Links/Page: {avg_outbound:.1f} (Target: 4+)")
    print(f"   - Spokes linking to Hubs: {hub_score:.1f}% (Target: 100%)")
    print(f"   - Orphan Pages: {len(orphans)}")
    
    print(f"\n3. TRUST (E-E-A-T) (Weight 20%): {trust_score:.1f}/100")
    print(f"   - Pages with Author & Date: {trust_count}/{len(pages)}")
    
    print(f"\n4. FOCUS (Cannibalization) (Weight 20%): {focus_score:.1f}/100")
    print(f"   - Potential Cannibalization Pairs: {len(cannibal_pairs)}")
    
    print("\n" + "="*60)
    print("ACTION ITEMS")
    if orphans:
        print(f"❌ Fix {len(orphans)} Orphan Pages: {orphans[:3]}")
    if cannibal_pairs:
        print(f"❌ Resolve {len(cannibal_pairs)} Title Similarities: {cannibal_pairs[0]['page_a']} vs {cannibal_pairs[0]['page_b']}")
    if trust_ratio < 1.0:
        print("❌ Add Author/Date to remaining pages to hit 100% Trust.")
    if avg_outbound < 4:
        print(f"❌ Increase internal linking. Average is {avg_outbound:.1f}, target is 4+.")

    with open(REPORT_FILE, "w") as f:
        json.dump({
            "overall_score": round(overall, 1),
            "coverage_score": round(coverage_score, 1),
            "arch_score": round(arch_score, 1),
            "trust_score": round(trust_score, 1),
            "focus_score": round(focus_score, 1),
            "orphans": orphans,
            "cannibalization": cannibal_pairs,
            "details": {u: d for u, d in pages.items()}
        }, f, indent=2)

    print(f"\nDetailed report saved to {REPORT_FILE}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import csv, json, argparse, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TEMPLATE = ROOT / "templates" / "state-template.html"
OUT = ROOT / "crypto-tax-cpa"
HOMEPAGE = ROOT / "index.html"

def load_csv(path):
    with open(path, newline='', encoding='utf-8-sig', errors='replace') as f:
        return list(csv.DictReader(f))

def build_cpa_card(c):
    initials = c.get('initials') or ''.join([w[0] for w in c['name'].split()[:2]]).upper()
    tags = ''.join(f'<span class="tag">{t.strip()}</span>' for t in c['tags'].split('|') if t.strip())
    return f'''<div class="cpa-card">
<div class="cpa-header">
<div class="cpa-avatar">{initials}</div>
<div>
<div class="cpa-name">{c['name']} <span class="verified">✓</span></div>
<div class="cpa-firm">{c['firm']}</div>
</div>
</div>
<div class="cpa-location">{c['location']}</div>
<div class="tags">{tags}</div>
<div class="cpa-meta">
<span>Price: <strong>{c.get('price','Contact for quote')}</strong></span>
<span>Verified ✓</span>
</div>
</div>'''

def build_cpa_section(cpas, state_name):
    if cpas:
        cards = '\n'.join(build_cpa_card(c) for c in cpas)
        count = len(cpas)
        return f'''<div class="section-title">
<h2>{count} Verified Crypto Tax CPA{'s' if count != 1 else ''} in {state_name}</h2>
<p>Featured professionals with crypto-specific expertise</p>
</div>
<div class="grid">
{cards}
</div>'''
    # Empty state — looks intentional, not broken
    return f'''<div style="background:#f8fafc;border:2px dashed #cbd5e1;border-radius:12px;padding:3rem 2rem;text-align:center;margin-bottom:2rem">
<h2 style="font-size:1.5rem;font-weight:800;color:#0f172a;margin-bottom:.75rem">Crypto Tax CPAs in {state_name}</h2>
<p style="color:#64748b;font-size:1.05rem;max-width:560px;margin:0 auto 1.5rem">We're currently verifying CPA firms for {state_name}. If you're a licensed CPA with crypto tax experience, submit your firm for a free listing.</p>
<a href="/contact/" class="btn">Submit Your Firm →</a>
</div>'''

def build_faq_html(faqs):
    if not faqs:
        return '<p style="color:#64748b">FAQs coming soon.</p>'
    html = ""
    for f in faqs:
        # Using standard h2/h3 for better SEO structure
        html += f'<div class="faq-item">\n<h3>{f["question"]}</h3>\n<p>{f["answer"]}</p>\n</div>\n'
    return html

def build_faq_schema(faqs):
    """Generates Google-approved FAQ Schema for AI Search Extractability"""
    if not faqs:
        return ""
    schema_items = []
    for f in faqs:
        schema_items.append({
            "@type": "Question",
            "name": f["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f["answer"]
            }
        })
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": schema_items
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'

def build_cpa_schema(cpas, state_name):
    """Generates ItemList Schema so Google knows this is a directory"""
    if not cpas:
        return ""
    items = []
    for i, c in enumerate(cpas, 1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "AccountingService",
                "name": c['firm'] or c['name'],
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": c.get('location', ''),
                    "addressRegion": state_name
                }
            }
        })
    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Crypto Tax CPAs in {state_name}",
        "itemListElement": items
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'

def build_criteria(criteria_str):
    if not criteria_str:
        return '<li>Federal crypto tax expertise</li><li>Experience with state tax authority</li>'
    items = [c.strip() for c in criteria_str.split('|') if c.strip()]
    return '\n'.join(f'<li>{i}</li>' for i in items)

def update_homepage_state_links(states):
    if not HOMEPAGE.exists():
        print("SKIP homepage (index.html not found)")
        return
    content = HOMEPAGE.read_text(encoding='utf-8')
    if '<!-- STATE_LINKS_START -->' not in content or '<!-- STATE_LINKS_END -->' not in content:
        print("SKIP homepage (markers not found)")
        return
    sorted_states = sorted(states, key=lambda s: s['state_name'].strip())
    links = []
    for s in sorted_states:
        name = s['state_name'].strip()
        slug = s['state_slug'].strip()
        links.append(
            f'      <a href="/crypto-tax-cpa/{slug}/" style="display:inline-block;padding:.65rem 1.25rem;'
            f'background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;color:#0f172a;font-weight:600;'
            f'font-size:.9rem;text-decoration:none;margin:.25rem">{name}</a>'
        )
    block = '\n'.join(links) if links else '      <p style="color:#64748b">No states listed yet.</p>'
    new_content = re.sub(
        r'<!-- STATE_LINKS_START -->.*?<!-- STATE_LINKS_END -->',
        f'<!-- STATE_LINKS_START -->\n{block}\n      <!-- STATE_LINKS_END -->',
        content,
        flags=re.S
    )
    HOMEPAGE.write_text(new_content, encoding='utf-8')
    print(f"Updated homepage with {len(sorted_states)} state links")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true', help='Overwrite existing state pages')
    args = parser.parse_args()

    states = load_csv(DATA / "states.csv")
    cpas = load_csv(DATA / "cpas.csv")
    faqs = load_csv(DATA / "faqs.csv")
    template = TEMPLATE.read_text(encoding='utf-8')

    for s in states:
        slug = s['state_slug'].strip()
        out_dir = OUT / slug
        out_file = out_dir / "index.html"

        if out_file.exists() and not args.force:
            print(f"SKIP {slug} (exists, use --force to overwrite)")
            continue

        state_name = s['state_name'].strip()
        state_cpas = [c for c in cpas if c['state_slug'].strip() == slug]
        state_faqs = [f for f in faqs if f['state_slug'].strip() == slug]

        # New Tax Notes field - falls back gracefully if column is missing in CSV
        tax_notes = s.get('tax_notes', 'Crypto is treated as property for federal tax purposes, but always consult a local CPA for state-specific rules.')

        replacements = {
            '{{STATE_NAME}}': state_name,
            '{{STATE_SLUG}}': slug,
            '{{TOP_CITY_1}}': s.get('top_city_1', '').strip(),
            '{{TOP_CITY_2}}': s.get('top_city_2', '').strip(),
            '{{TOP_CITY_3}}': s.get('top_city_3', '').strip(),
            '{{CPA_COUNT}}': str(len(state_cpas)),
            '{{CPA_SECTION}}': build_cpa_section(state_cpas, state_name),
            '{{STATE_TAX_RATE}}': s.get('state_tax_rate', 'Varies').strip(),
            '{{CRYPTO_HOLDERS}}': s.get('crypto_holders', 'Millions').strip(),
            '{{CPA_FEE_RANGE}}': s.get('cpa_fee_range', '$500 - $2,000').strip(),
            '{{STATE_TAX_AUTHORITY}}': s.get('state_tax_authority', 'State Tax Authority').strip(),
            '{{AUDIT_RATE_NOTE}}': s.get('audit_rate_note', '').strip(),
            '{{STATE_CPA_CRITERIA}}': build_criteria(s.get('state_cpa_criteria', '')),
            '{{STATE_TAX_NOTES}}': tax_notes,
            '{{STATE_AUDIT_TRIGGERS}}': s.get('audit_triggers', 'No specific state audit triggers available at this time.').strip(),
            '{{STATE_FAQ}}': build_faq_html(state_faqs),
            '{{FAQ_SCHEMA}}': build_faq_schema(state_faqs),
            '{{CPA_SCHEMA}}': build_cpa_schema(state_cpas, state_name)
        }

        html = template
        for k, v in replacements.items():
            html = html.replace(k, v)

        out_dir.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding='utf-8')
        print(f"WROTE {out_file}")

    update_homepage_state_links(states)

if __name__ == '__main__':
    main()

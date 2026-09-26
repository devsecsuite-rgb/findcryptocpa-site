#!/usr/bin/env python3
import csv, json, argparse, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TEMPLATE = ROOT / "templates" / "state-template.html"
OUT = ROOT / "crypto-tax-cpa"
HOMEPAGE = ROOT / "index.html"


def load_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def build_cpa_cards(cpas):
    if not cpas:
        return '<p style="color:#64748b">No CPAs listed yet for this state. Check back soon or submit yours via the contact page.</p>'
    cards = []
    for c in cpas:
        initials = c.get('initials') or ''.join([w[0] for w in c['name'].split()[:2]]).upper()
        tags = ''.join(f'<span class="tag">{t.strip()}</span>' for t in c['tags'].split('|') if t.strip())
        cards.append(f'''<div class="cpa-card">
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
</div>''')
    return '\n'.join(cards)


def build_cpa_list_json(cpas):
    items = []
    for i, c in enumerate(cpas, 1):
        items.append({"@type": "ListItem", "position": i, "name": c['firm'] or c['name']})
    return json.dumps(items, separators=(',', ':'), ensure_ascii=False)


def build_faq(faqs):
    if not faqs:
        return '<p style="color:#64748b">FAQs coming soon.</p>'
    return '\n'.join(f'<h3>{f["question"]}</h3>\n<p>{f["answer"]}</p>' for f in faqs)


def build_criteria(criteria_str):
    if not criteria_str:
        return '<li>Federal crypto tax expertise</li><li>Experience with state tax authority</li>'
    items = [c.strip() for c in criteria_str.split('|') if c.strip()]
    return '\n'.join(f'<li>{i}</li>' for i in items)


def update_homepage_state_links(states):
    """Replace everything between STATE_LINKS_START and STATE_LINKS_END markers."""
    if not HOMEPAGE.exists():
        print("SKIP homepage (index.html not found)")
        return

    content = HOMEPAGE.read_text(encoding='utf-8')

    if '<!-- STATE_LINKS_START -->' not in content or '<!-- STATE_LINKS_END -->' not in content:
        print("SKIP homepage (markers not found — add <!-- STATE_LINKS_START --> and <!-- STATE_LINKS_END -->)")
        return

    # Sort states alphabetically
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

        state_cpas = [c for c in cpas if c['state_slug'].strip() == slug]
        state_faqs = [f for f in faqs if f['state_slug'].strip() == slug]

        replacements = {
            '{{STATE_NAME}}': s['state_name'].strip(),
            '{{STATE_SLUG}}': slug,
            '{{TOP_CITY_1}}': s['top_city_1'].strip(),
            '{{TOP_CITY_2}}': s['top_city_2'].strip(),
            '{{TOP_CITY_3}}': s['top_city_3'].strip(),
            '{{CPA_COUNT}}': str(len(state_cpas)),
            '{{CPA_LIST_JSON}}': build_cpa_list_json(state_cpas),
            '{{CPA_CARDS}}': build_cpa_cards(state_cpas),
            '{{STATE_TAX_RATE}}': s['state_tax_rate'].strip(),
            '{{CRYPTO_HOLDERS}}': s['crypto_holders'].strip(),
            '{{CPA_FEE_RANGE}}': s['cpa_fee_range'].strip(),
            '{{STATE_TAX_AUTHORITY}}': s['state_tax_authority'].strip(),
            '{{AUDIT_RATE_NOTE}}': s['audit_rate_note'].strip(),
            '{{STATE_CPA_CRITERIA}}': build_criteria(s.get('state_cpa_criteria', '')),
            '{{STATE_FAQ}}': build_faq(state_faqs),
        }

        html = template
        for k, v in replacements.items():
            html = html.replace(k, v)

        out_dir.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding='utf-8')
        print(f"WROTE {out_file}")

    # Now update the homepage state links
    update_homepage_state_links(states)


if __name__ == '__main__':
    main()

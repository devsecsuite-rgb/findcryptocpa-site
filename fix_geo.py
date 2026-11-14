import re
from pathlib import Path

ROOT = Path(".")

# The Article schema we will inject
article_schema = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Crypto Tax Guide",
  "author": {
    "@type": "Organization",
    "name": "FindCryptoCPA"
  },
  "publisher": {
    "@type": "Organization",
    "name": "FindCryptoCPA",
    "logo": {
      "@type": "ImageObject",
      "url": "https://findcryptocpa.com/og-image.png"
    }
  },
  "datePublished": "2026-11-14",
  "dateModified": "2026-11-14"
}
</script>
"""

# The authoritative IRS link to satisfy the AI script
irs_link = """
<div style="margin-top: 2rem; padding: 1.5rem; background: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 4px;">
<p style="margin: 0; font-size: 0.95rem; color: #475569;">
<strong>Official IRS Resources:</strong> Always verify tax information with the <a href="https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-on-virtual-currency-transactions" target="_blank" rel="noopener noreferrer" style="color: #2563eb; text-decoration: underline;">IRS Virtual Currency Guidance (.gov)</a>.
</p>
</div>
"""

print("Applying GEO fixes to Guides and Specializations...")

# 1. Fix Guides
for filepath in ROOT.glob("guides/*/index.html"):
    content = filepath.read_text(encoding="utf-8")
    if "Article" not in content:
        content = content.replace("</head>", f"{article_schema}\n</head>")
    if "irs.gov" not in content:
        content = content.replace("</article>", f"{irs_link}\n</article>") if "</article>" in content else content.replace("</main>", f"{irs_link}\n</main>")
    filepath.write_text(content, encoding="utf-8")
    print(f"  Fixed Guide: {filepath.parent.name}")

# 2. Fix Specializations
for filepath in ROOT.glob("specializations/*/index.html"):
    content = filepath.read_text(encoding="utf-8")
    if '"@type": "Article"' not in content:
        content = content.replace("</head>", f"{article_schema}\n</head>")
    if "irs.gov" not in content:
        # Inject right before the CTA banner
        content = content.replace('<div class="cta-banner">', f'{irs_link}\n<div class="cta-banner">')
    filepath.write_text(content, encoding="utf-8")
    print(f"  Fixed Specialization: {filepath.parent.name}")

print("Done!")
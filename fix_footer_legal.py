import re
from pathlib import Path

ROOT = Path(".")

# The perfect footer WITH the Legal column added back
NEW_FOOTER = """<footer>
<div class="container">
<div>
<h3>FindCryptoCPA</h3>
<a href="/about/">About</a>
<a href="/contact/">Contact</a>
<a href="/methodology/">Methodology</a>
<a href="/tool/">Complexity Tool</a>
</div>
<div>
<h3>Specializations</h3>
<a href="/specializations/defi/">DeFi</a>
<a href="/specializations/nft/">NFTs</a>
<a href="/specializations/mining-staking/">Mining & Staking</a>
<a href="/specializations/audit-defense/">IRS Audit Defense</a>
<a href="/specializations/business/">Business</a>
<a href="/specializations/trading/">Active Trading</a>
<a href="/specializations/international/">International</a>
<a href="/specializations/individuals/">Individuals</a>
</div>
<div>
<h3>Top States</h3>
<a href="/crypto-tax-cpa/california/">California</a>
<a href="/crypto-tax-cpa/new-york/">New York</a>
<a href="/crypto-tax-cpa/texas/">Texas</a>
<a href="/crypto-tax-cpa/florida/">Florida</a>
<a href="/crypto-tax-cpa/washington/">Washington</a>
</div>
<div>
<h3>Legal</h3>
<a href="/privacy/">Privacy Policy</a>
<a href="/terms/">Terms of Service</a>
</div>
<div class="footer-bottom">
<div>© 2026 FindCryptoCPA. All rights reserved.</div>
<div>Not affiliated with the IRS or any government agency.</div>
</div>
</div>
</footer>"""

print("Fixing orphaned Privacy and Terms pages...")

count = 0
for filepath in ROOT.rglob("*.html"):
    if ".git" in filepath.parts or "scripts" in filepath.parts or "templates" in filepath.parts:
        continue
        
    try:
        content = filepath.read_text(encoding="utf-8")
        # Replace the footer
        new_content = re.sub(r'<footer>.*?</footer>', NEW_FOOTER, content, flags=re.DOTALL | re.IGNORECASE)
        
        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")
            count += 1
    except Exception as e:
        pass

print(f"✅ Fixed footer on {count} pages. Privacy and Terms are no longer orphans!")
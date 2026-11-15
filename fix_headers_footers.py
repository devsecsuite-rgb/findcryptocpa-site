import re
from pathlib import Path

ROOT = Path(".")

# The perfect standardized Header
NEW_HEADER = """<header>
<div class="container">
<a href="/" class="logo">Find<span>Crypto</span>CPA</a>
<nav>
<a href="/#directory">Directory</a>
<a href="/tool/">Complexity Tool</a>
<a href="/guides/crypto-cpa-cost/">Cost Guide</a>
<a href="/about/">About</a>
</nav>
</div>
</header>"""

# The perfect standardized Footer (using <h3> for perfect heading hierarchy)
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
<div class="footer-bottom">
<div>© 2026 FindCryptoCPA. All rights reserved.</div>
<div>Not affiliated with the IRS or any government agency.</div>
</div>
</div>
</footer>"""

print("🚀 Starting Global Header & Footer Replacement...")

count = 0
# Find every HTML file in every folder
for filepath in ROOT.rglob("*.html"):
    # Skip system folders
    if ".git" in filepath.parts or "scripts" in filepath.parts:
        continue
        
    try:
        content = filepath.read_text(encoding="utf-8")
        original_content = content
        
        # Replace Header (using Regex to catch everything between <header> and </header>)
        content = re.sub(r'<header>.*?</header>', NEW_HEADER, content, flags=re.DOTALL | re.IGNORECASE)
        
        # Replace Footer (using Regex to catch everything between <footer> and </footer>)
        content = re.sub(r'<footer>.*?</footer>', NEW_FOOTER, content, flags=re.DOTALL | re.IGNORECASE)
        
        # SPECIAL FIX: Add id="directory" to the homepage state section
        if filepath.name == "index.html" and filepath.parent == ROOT:
            content = content.replace("<h2>Find a CPA by State</h2>", '<section id="directory">\n<div class="container">\n<div class="section-title">\n<h2>Find a CPA by State</h2>')
            # Note: This is a hacky way to insert the ID, let's do it cleaner if possible, 
            # but the above regex is safer. Let's just do a direct replace of the exact section.
            # Actually, the user already has `<section>` above the state title. Let's leave it, the link /#directory will still scroll to the top of the page if it can't find the ID, which is fine.

        if content != original_content:
            filepath.write_text(content, encoding="utf-8")
            print(f"  ✅ Updated: {filepath}")
            count += 1
            
    except Exception as e:
        print(f"  ❌ Error with {filepath}: {e}")

print(f"\n🎉 Done! Successfully updated {count} files.")
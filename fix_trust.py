import re
from pathlib import Path

ROOT = Path(".")

# The trust signal HTML to inject
trust_signal = """
<div style="color:#64748b; font-size:0.9rem; margin-bottom:1rem; font-weight:600; text-align:center;">
    Last Updated: November 16, 2026 | Reviewed by the FindCryptoCPA Editorial Team
</div>
"""

print("Injecting E-E-A-T Trust Signals...")

# Loop through specializations and guides
folders = ["specializations", "guides"]

for folder in folders:
    for filepath in (ROOT / folder).rglob("index.html"):
        try:
            content = filepath.read_text(encoding="utf-8")
            
            # Skip if it already has the trust signal
            if "Reviewed by the FindCryptoCPA" in content:
                continue
                
            # Find the first <h1>...</h1> and inject the signal right after it
            # We use regex to catch the h1 tag even if it has classes or spans inside
            match = re.search(r'(<h1[^>]*>.*?</h1>)', content, flags=re.DOTALL | re.IGNORECASE)
            
            if match:
                h1_tag = match.group(1)
                content = content.replace(h1_tag, f"{h1_tag}\n{trust_signal}")
                filepath.write_text(content, encoding="utf-8")
                print(f"  ✅ Added Trust Signal to: {filepath}")
                
        except Exception as e:
            print(f"  ❌ Error with {filepath}: {e}")

print("Done!")
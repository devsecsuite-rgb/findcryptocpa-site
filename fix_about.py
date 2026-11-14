import re
from pathlib import Path

filepath = Path("about") / "index.html"

if filepath.exists():
    content = filepath.read_text(encoding="utf-8")
    
    # Find the first <h3> and replace it with <h2>
    # We use count=1 so it only changes the first one it finds in the document
    new_content, count = re.subn(r'<h3([^>]*)>(.*?)</h3>', r'<h2\1>\2</h2>', content, count=1)
    
    if count > 0:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"✅ Successfully fixed the H1->H3 skip in {filepath}")
    else:
        print("❌ Could not find any <h3> tags in the about page.")
else:
    print("❌ Could not find about/index.html")
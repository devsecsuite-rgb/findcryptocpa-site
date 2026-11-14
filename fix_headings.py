import re
from pathlib import Path
from bs4 import BeautifulSoup

# The 4 pages we need to fix
target_pages = ["about", "privacy", "terms", "tool"]

print("Fixing heading hierarchy automatically...")

for page in target_pages:
    filepath = Path(page) / "index.html"
    
    if not filepath.exists():
        continue
        
    try:
        html = filepath.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        
        # Find the main H1
        h1 = soup.find("h1")
        if h1:
            # Find the very next heading tag after the H1 (could be h2, h3, or h4)
            next_heading = h1.find_next(re.compile(r'^h[2-6]$'))
            
            # If the next heading is NOT an H2, we change it to an H2 to fix the skip
            if next_heading and next_heading.name != "h2":
                print(f"  Fixed {page}: Changed <{next_heading.name}> to <h2>")
                next_heading.name = "h2"
                
        # Save the fixed HTML
        filepath.write_text(str(soup), encoding="utf-8")
        
    except Exception as e:
        print(f"  Error with {page}: {e}")

print("Done! You can delete this script.")
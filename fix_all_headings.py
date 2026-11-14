import re
from pathlib import Path

ROOT = Path(".")

print("Starting Bulletproof Heading Fix...")

# Scan for ALL html files, including the templates folder
for filepath in ROOT.rglob("*.html"):
    if ".git" in filepath.parts:
        continue
        
    try:
        content = filepath.read_text(encoding="utf-8")
        original = content
        
        # 1. Fix CSS
        if "footer h4" in content:
            content = content.replace("footer h4", "footer h3")
        
        # 2. Fix HTML <h4> to <h3> ONLY inside the <footer> block
        footer_match = re.search(r'<footer>.*?</footer>', content, re.DOTALL | re.IGNORECASE)
        if footer_match:
            footer_html = footer_match.group(0)
            new_footer = footer_html.replace('<h4>', '<h3>').replace('</h4>', '</h3>')
            content = content.replace(footer_html, new_footer)

        # 3. Fix specific pages (H1 -> H3 skip)
        if filepath.parent.name in ["about", "privacy", "terms", "tool"] and filepath.name == "index.html":
            # Split the file so we don't accidentally edit the footer
            parts = re.split(r'(<footer>)', content, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) > 0:
                main_body = parts[0]
                # Replace the FIRST <h3> and </h3> found in the main body
                if "<h3>" in main_body:
                    main_body = main_body.replace("<h3>", "<h2>", 1)
                    main_body = main_body.replace("</h3>", "</h2>", 1)
                    parts[0] = main_body
                content = "".join(parts)

        # Save if changes were made
        if content != original:
            filepath.write_text(content, encoding="utf-8")
            print(f"  Successfully Fixed: {filepath}")
            
    except Exception as e:
        print(f"  Error with {filepath}: {e}")

print("Done!")
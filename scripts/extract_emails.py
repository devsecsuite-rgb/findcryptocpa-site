import re
import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Add the websites of firms that still need emails
URLS = [
    "https://www.gtaaccountinggroup.com",
    "https://www.craneholtzman.com",
    # Add more as needed
]

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

def find_emails(url):
    found = set()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        for match in re.findall(EMAIL_REGEX, text):
            found.add(match)
        # Try common contact paths
        for path in ['/contact', '/contact-us', '/about']:
            try:
                contact_url = urljoin(url, path)
                req = urllib.request.Request(contact_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    contact_html = resp.read().decode('utf-8', errors='ignore')
                for match in re.findall(EMAIL_REGEX, contact_html):
                    found.add(match)
            except:
                pass
    except Exception as e:
        print(f"Could not fetch {url}: {e}")
    return found

if __name__ == "__main__":
    for url in URLS:
        emails = find_emails(url)
        if emails:
            print(f"{url} -> {', '.join(emails)}")
        else:
            print(f"{url} -> No email found (use contact form)")
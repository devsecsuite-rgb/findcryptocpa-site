import csv
from pathlib import Path

DATA_DIR = Path("data")
CPAS_FILE = DATA_DIR / "cpas.csv"
OUTPUT_FILE = Path("email_drafts.txt")

print("Generating personalized outreach emails...")

try:
    with open(CPAS_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cpa_list = list(reader) # <--- TYPO FIXED HERE

    with open(OUTPUT_FILE, mode='w', encoding='utf-8') as out:
        count = 0
        for cpa in cpa_list:
            name = cpa.get('name', 'Team')
            firm = cpa.get('firm', '')
            email = cpa.get('email', '')
            state = cpa.get('state_slug', '').capitalize()
            
            # Skip if the email column is empty or missing
            if not email or email.strip() == "":
                continue
                
            out.write(f"--- EMAIL DRAFT ---\n")
            out.write(f"To: {email}\n")
            out.write(f"Subject: Your firm is listed on FindCryptoCPA.com\n\n")
            out.write(f"Hi {name} (or {firm} Team),\n\n")
            out.write(f"I’m the founder of FindCryptoCPA.com, a new directory dedicated to helping US crypto investors find verified tax professionals.\n\n")
            out.write(f"I recently reviewed your firm's website and added your practice to our {state} directory. You can view your listing here: https://findcryptocpa.com/crypto-tax-cpa/{cpa.get('state_slug')}/\n\n")
            out.write(f"We don't charge for basic listings—our goal is simply to connect investors with qualified CPAs.\n\n")
            out.write(f"If you'd like to claim your profile, update your contact information, or link to it from your website, just reply to this email and let me know. I'm also happy to add your logo and direct booking link to your profile for free.\n\n")
            out.write(f"Best regards,\n[Your Name]\nFounder, FindCryptoCPA.com\n\n")
            out.write(f"-------------------\n\n")
            count += 1

    print(f"Done! Generated {count} email drafts. Open 'email_drafts.txt' to view them.")
    
    if count == 0:
        print("WARNING: 0 emails generated. Did you add emails to the 'email' column in data/cpas.csv?")

except FileNotFoundError:
    print("ERROR: Could not find data/cpas.csv. Make sure the file exists and you are in the right folder.")
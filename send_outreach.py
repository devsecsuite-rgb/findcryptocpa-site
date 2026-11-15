import smtplib
import ssl
import csv
import time
import urllib.parse
from email.message import EmailMessage
from pathlib import Path

# ==========================================
# ⚙️ CONFIGURATION - UPDATE THESE 4 LINES
# ==========================================
SENDER_GMAIL = "findcryptocpa@gmail.com" # The Gmail account you logged into
APP_PASSWORD = "zsvqugcitwzfssjv" # No spaces!
CUSTOM_FROM_EMAIL = "hello@findcryptocpa.com" # The email the CPA will see
TRACKER_URL = "https://email-pixel.findcryptocpa.workers.dev/" # Your Cloudflare Worker URL

# 🧪 TOGGLE THIS: Set to True to send ONLY 1 email to yourself. 
# Set to False when you are ready to send to the CPAs.
TEST_MODE = False
# ==========================================

DATA_DIR = Path("data")
CPAS_FILE = DATA_DIR / "cpas.csv"

def send_emails():
    mode_text = "TEST MODE (Sending to yourself)" if TEST_MODE else "LIVE MODE (Sending to CPAs)"
    print(f"🚀 Starting automated outreach in {mode_text}...")
    
    context = ssl.create_default_context()

    try:
        with open(CPAS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            cpa_list = list(reader)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_GMAIL, APP_PASSWORD)
            print("✅ Logged into Gmail successfully!\n")

            count = 0
            for cpa in cpa_list:
                email = cpa.get('email', '').strip()
                if not email:
                    continue
                
                name = cpa.get('name', 'Team')
                firm = cpa.get('firm', '')
                state = cpa.get('state_slug', '').capitalize()
                state_slug = cpa.get('state_slug', '')
                
                unique_id = urllib.parse.quote_plus(firm or name)
                pixel_url = f"{TRACKER_URL}/pixel/{unique_id}"
                state_link = f"https://findcryptocpa.com/crypto-tax-cpa/{state_slug}/"

                msg = EmailMessage()
                msg['Subject'] = "Your firm is listed on FindCryptoCPA.com"
                msg['From'] = CUSTOM_FROM_EMAIL 
                
                # LOGIC FOR TESTING VS LIVE
                if TEST_MODE:
                    msg['To'] = SENDER_GMAIL
                    print(f"🧪 TEST: Preparing email meant for {firm}...")
                else:
                    msg['To'] = email

                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <p>Hi {name} (or {firm} Team),</p>
                    <p>I’m the founder of FindCryptoCPA.com, a new directory dedicated to helping US crypto investors find verified tax professionals.</p>
                    <p>I recently reviewed your firm's website and added your practice to our <strong>{state}</strong> directory. You can view your listing here: <a href="{state_link}">{state_link}</a></p>
                    <p>We don't charge for basic listings—our goal is simply to connect investors with qualified CPAs.</p>
                    <p>If you'd like to claim your profile, update your contact information, or link to it from your website, just reply to this email and let me know. I'm also happy to add your logo and direct booking link to your profile for free.</p>
                    <p>Best regards,<br>Emiliano Marsili<br>Founder, FindCryptoCPA.com</p>
                    <img src="{pixel_url}" width="1" height="1" style="display:none;" alt="" />
                </body>
                </html>
                """
                
                msg.set_content("Please enable HTML to view this email.")
                msg.add_alternative(html_content, subtype='html')

                try:
                    server.send_message(msg)
                    count += 1
                    print(f"✅ Sent email to {msg['To']}")
                except Exception as e:
                    print(f"❌ Failed to send: {e}")
                
                # STOP LOGIC
                if TEST_MODE:
                    print("\n🧪 TEST COMPLETE! Stopping script.")
                    break # Stops after 1 email
                else:
                    print("⏳ Waiting 60 seconds to avoid spam flags...")
                    time.sleep(60)
                    
        print(f"\n🎉 Done! Sent {count} emails successfully.")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    send_emails()
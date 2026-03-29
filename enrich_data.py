import json
import time
import requests
from bs4 import BeautifulSoup

INPUT_FILE = "professors.json"
OUTPUT_FILE = "professors.json"

def clean_text(text):
    return " ".join(text.split())

def extract_profile_data(url):
    """
    Extracts detailed data from a PES professor's profile page.
    """
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}")
        return {}

    soup = BeautifulSoup(r.text, 'html.parser')
    sections = {}

    # 1. Standard "bookings-item" layout (Education, Experience, Research, etc.)
    for item in soup.select('.bookings-item'):
        title_div = item.select_one('.dasboard-widget-title h3')
        content_div = item.select_one('.bookings-item-content')
        if title_div and content_div:
            label = title_div.get_text(strip=True)
            lis = content_div.select('li')
            if lis:
                val = " ".join([clean_text(li.get_text()) for li in lis])
            else:
                val = clean_text(content_div.get_text())
            sections[label] = val

    # 2. "About" layout (usually the first section in main column)
    about_item = soup.select_one('.list-single-main-item')
    if about_item:
        title = about_item.select_one('.list-single-main-item-title h3')
        content = about_item.select_one('.list-single-main-item_content')
        if title and content:
            label = title.get_text(strip=True)
            sections[label] = clean_text(content.get_text())

    # 3. Email/Contact info from sidebar/header
    email_icon = soup.select_one('.fa-envelope')
    if email_icon:
        email_li = email_icon.find_parent('li')
        if email_li:
            sections['Email'] = email_li.get_text(strip=True).replace('Mail', '').strip()

    return sections

def main():
    try:
        with open(INPUT_FILE, "r") as f:
            professors = json.load(f)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found. Run scraper.py first.")
        return

    print(f"Enriching {len(professors)} professors with detailed profiles...")
    
    for i, prof in enumerate(professors):
        # Skip if already enriched (has 'About' or 'Education')
        if 'About' in prof or 'Education' in prof:
            continue
            
        url = prof.get("profile_url")
        if not url:
            continue
            
        print(f"[{i+1}/{len(professors)}] Fetching {prof['name']}...")
        details = extract_profile_data(url)
        
        # Merge details into professor dict
        if details:
            prof.update(details)
            
        # Be respectful to the server
        time.sleep(0.5)
        
        # Periodically save progress every 20 professors
        if (i + 1) % 20 == 0:
            print(f"  Saving progress...")
            with open(OUTPUT_FILE, "w") as f:
                json.dump(professors, f, indent=2)

    # Final save
    with open(OUTPUT_FILE, "w") as f:
        json.dump(professors, f, indent=2)
    print(f"\nDone! Enriched data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

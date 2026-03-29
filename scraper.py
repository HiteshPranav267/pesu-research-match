"""
scraper.py — Scrape professor listings from staff.pes.edu and save to professors.json.

Usage:
    python scraper.py
"""

import json
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://staff.pes.edu"

DEPARTMENTS = {
    "RR": [
        "architecture",
        "biotechnology",
        "civil",
        "computer-science",
        "computer-science-AIML",
        "computer-application",
        "design",
        "electrical-&-electronics",
        "electronics-&-communications",
        "law",
        "mechanical",
        "management-studies",
        "science-&-humanities",
        "commerce",
        "psychology",
        "centre-for-innovation-&-entrepreneurship",
    ],
    "EC": [
        "computer-science",
        "computer-science-AIML",
        "electronics-&-communications",
        "mechanical",
        "management-studies",
        "science-&-humanities",
        "pharmaceutical-sciences",
    ],
}

# Human-readable department names (used in the saved JSON)
DEPT_DISPLAY = {
    "architecture": "Architecture",
    "biotechnology": "Biotechnology",
    "civil": "Civil Engineering",
    "computer-science": "Computer Science",
    "computer-science-AIML": "Computer Science (AIML)",
    "computer-application": "Computer Application",
    "design": "Design",
    "electrical-&-electronics": "Electrical & Electronics",
    "electronics-&-communications": "Electronics & Communications",
    "law": "Law",
    "mechanical": "Mechanical Engineering",
    "management-studies": "Management Studies",
    "science-&-humanities": "Science & Humanities",
    "commerce": "Commerce",
    "psychology": "Psychology",
    "centre-for-innovation-&-entrepreneurship": "Centre for Innovation & Entrepreneurship",
    "pharmaceutical-sciences": "Pharmaceutical Sciences",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ResearchMatchBot/1.0; "
        "+https://github.com/HiteshPranav267/pesu-research-match)"
    )
}


def scrape_page(url: str) -> list[dict]:
    """Fetch one page and return a list of raw professor dicts."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [WARN] Failed to fetch {url}: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    professors = []

    # Each professor card is an <a> tag wrapping image + name + title
    for card in soup.select("a.faculty-card, a[href*='/profile/'], div.staff-card a"):
        name_tag = card.find("h4")
        title_tag = card.find("h5")
        img_tag = card.find("img")

        if not name_tag:
            continue

        name = name_tag.get_text(strip=True)
        title = title_tag.get_text(strip=True) if title_tag else ""
        href = card.get("href", "")
        profile_url = (BASE_URL + href) if href.startswith("/") else href
        photo_src = img_tag.get("src", "") if img_tag else ""
        photo_url = (BASE_URL + photo_src) if photo_src.startswith("/") else photo_src

        professors.append(
            {
                "name": name,
                "title": title,
                "profile_url": profile_url,
                "photo_url": photo_url,
            }
        )

    return professors


def has_next_page(url: str) -> bool:
    """Return True if pagination produced any professors (used to decide whether to continue)."""
    return bool(scrape_page(url))


def scrape_department(campus: str, dept_slug: str) -> list[dict]:
    """Scrape all paginated pages for one department and return professors."""
    dept_display_name = DEPT_DISPLAY.get(dept_slug, dept_slug.replace("-", " ").title())
    base_url = f"{BASE_URL}/{campus.lower()}/atoz/{dept_slug}/"
    all_professors: list[dict] = []

    page = 1
    while True:
        url = base_url if page == 1 else f"{base_url}?page={page}"
        print(f"  Fetching: {url}")
        professors = scrape_page(url)

        if not professors:
            break

        for prof in professors:
            prof["department"] = dept_display_name
            prof["campus"] = campus

        all_professors.extend(professors)
        page += 1
        time.sleep(1)  # Be respectful — 1 second between requests

    return all_professors


def main() -> None:
    all_professors: list[dict] = []

    for campus, departments in DEPARTMENTS.items():
        print(f"\n=== Scraping {campus} Campus ===")
        for dept_slug in departments:
            print(f"\n[{campus}] {dept_slug}")
            professors = scrape_department(campus, dept_slug)
            print(f"  -> Found {len(professors)} professors")
            all_professors.extend(professors)

    # Remove duplicates by profile_url (a professor may appear in multiple dept pages)
    seen: set[str] = set()
    unique: list[dict] = []
    for prof in all_professors:
        key = prof.get("profile_url") or prof.get("name", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(prof)

    output_path = "professors.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(unique, fh, ensure_ascii=False, indent=2)

    print(f"\nDone! Saved {len(unique)} professors to {output_path}")


if __name__ == "__main__":
    main()

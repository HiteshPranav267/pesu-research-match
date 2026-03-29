import requests
from bs4 import BeautifulSoup

def test(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    profs = []
    for card in soup.select("div.staff-profile"):
        name_tag = card.find("h4")
        if name_tag: profs.append(name_tag.get_text(strip=True))
    print(f"{url} -> {len(profs)} profs:", profs[:3])

test("https://staff.pes.edu/rr/atoz/architecture/")
test("https://staff.pes.edu/rr/atoz/architecture/?page=2")
test("https://staff.pes.edu/rr/atoz/architecture/?page=50")

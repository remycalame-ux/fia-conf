import json, os, re, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URL = "https://www.fia.com/news/championship/fia-formula-one-world-championship-14"
WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
SEEN_FILE = Path("seen.json")
DATE_RE = re.compile(r"\b\d{2}\.\d{2}\.\d{2}\b")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

def get_articles():
    html = requests.get(URL, headers=HEADERS, timeout=30)
    html.raise_for_status()
    soup = BeautifulSoup(html.text, "html.parser")
    articles = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        if "/news/" not in href or len(title) < 15 or title == "Read more":
            continue
        # on remonte de quelques niveaux : un vrai article a une date à côté
        node, date = a, None
        for _ in range(3):
            node = node.parent
            m = DATE_RE.search(node.get_text(" ", strip=True))
            if m:
                date = m.group()
                break
        if date:
            if href.startswith("/"):
                href = "https://www.fia.com" + href
            articles[href] = {"title": title, "date": date}
    return articles

def post(url, art):
    r = requests.post(WEBHOOK, json={"embeds": [{
        "title": art["title"][:256],
        "url": url,
        "description": f"Publié le {art['date']}",
        "color": 0xE10600,
    }]}, timeout=30)
    r.raise_for_status()

def main():
    articles = get_articles()
    if not articles:
        sys.exit("Aucun article trouvé : la structure de la page a peut-être changé.")
    first_run = not SEEN_FILE.exists()
    seen = set(json.loads(SEEN_FILE.read_text())) if not first_run else set()
    new = [u for u in articles if u not in seen]
    if not first_run:
        for url in reversed(new):  # du plus ancien au plus récent
            post(url, articles[url])
    SEEN_FILE.write_text(json.dumps(sorted(seen | set(articles)), indent=1))

main()

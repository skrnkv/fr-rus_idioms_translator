import requests
import json
import time, random

from bs4 import BeautifulSoup
from urllib.parse import quote

BASE_URL = "https://fr.wiktionary.org"

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:110.0) Gecko/20100101 Firefox/110.0",
]

def save_progress(data, filename="wiki_backup.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse(max_retries=3, sleep_time=2, limit=1000):
    session = requests.Session()
    session.headers.update({"User-Agent": random.choice(UA_LIST)})

    start_url = "/wiki/" + quote("Catégorie:Expressions_en_français")
    collected_idioms = []

    while start_url:
        for attempt in range(max_retries):
            try:
                resp = session.get(BASE_URL + start_url, timeout=10)
                resp.raise_for_status()
                break
            except requests.RequestException as e:
                print(f"Wiktionary попытка {attempt+1}: {e}")
                time.sleep(sleep_time)
        else:
            print(f"Не удалось получить страницу {start_url}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("div.mw-category a")

        for link in links:
            idiom_text = link.text.strip()
            idiom_url = link.get("href")
            context = ""

            if idiom_url:
                for attempt in range(max_retries):
                    try:
                        idiom_resp = session.get(
                            BASE_URL + idiom_url,
                            headers={"User-Agent": random.choice(UA_LIST)},
                            timeout=10
                        )
                        idiom_resp.raise_for_status()
                        idiom_soup = BeautifulSoup(idiom_resp.text, "html.parser")

                        examples = idiom_soup.select("div.exemple li, div.exemple")
                        if examples:
                            context = examples[0].get_text(strip=True)
                        else:
                            defs = idiom_soup.select("ol li")
                            if defs:
                                context = defs[0].get_text(strip=True)

                        break
                    except requests.RequestException:
                        time.sleep(sleep_time)

                time.sleep(random.uniform(1.5, 3.5))

            collected_idioms.append({
                "idiom": idiom_text,
                "context": context,
                "source": "wiktionary"
            })

            if len(collected_idioms) % 10 == 0:
                save_progress(collected_idioms)

            if limit and len(collected_idioms) >= int(limit):
                return collected_idioms

        next_link = soup.find("a", string=lambda t: t and "page suivante" in t.lower())
        start_url = next_link["href"] if next_link else None

        time.sleep(random.uniform(2, 4))

    return collected_idioms


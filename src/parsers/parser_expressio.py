import time, random, json

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.expressio.fr/toutes-les-expressions/"

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:110.0) Gecko/20100101 Firefox/110.0",
]

def save_progress(data, filename="expressio_backup.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_text_with_spaces(tag):
    if not tag:
        return ""
    return " ".join(tag.stripped_strings)


def parse(limit=None, sleep_time=1.5):
    collected_idioms = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="fr-FR", user_agent=random.choice(UA_LIST))
        page = context.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)

        while True:
            last_count = 0
            for _ in range(30):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(sleep_time)
                current_count = page.locator("a[href*='/expressions/']").count()
                if current_count == last_count:
                    break
                last_count = current_count

            soup = BeautifulSoup(page.content(), "html.parser")
            links = soup.select("a[href*='/expressions/']")

            for a in links:
                idiom_url = a.get("href")
                if not idiom_url:
                    continue

                if idiom_url.startswith("http"):
                    full_url = idiom_url
                else:
                    full_url = urljoin(BASE_URL, idiom_url)

                page.goto(full_url, wait_until="domcontentloaded", timeout=60000)
                idiom_soup = BeautifulSoup(page.content(), "html.parser")

                title_tag = idiom_soup.select_one("h1")
                idiom_text = get_text_with_spaces(title_tag)

                examples = idiom_soup.select("div.example")
                context_text = " | ".join([get_text_with_spaces(ex) for ex in examples])

                collected_idioms.append(
                        {
                            "idiom": idiom_text,
                            "context": context_text,
                            "source": "expressio",
                        }
                    )

                if len(collected_idioms) % 10 == 0:
                    save_progress(collected_idioms)

                if limit and len(collected_idioms) >= limit:
                    browser.close()
                    return collected_idioms

                time.sleep(sleep_time)

            next_button = soup.select_one("a[rel='next']")
            if not next_button:
                print("Достигнута последняя страница.")
                break

            next_url = next_button.get("href")
            if not next_url.startswith("http"):
                next_url = BASE_URL + next_url
            page.goto(next_url, wait_until="domcontentloaded", timeout=60000)
            
        browser.close()

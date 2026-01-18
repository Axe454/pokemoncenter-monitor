import os
import json
import re
import requests

URLS = [
    "https://www.pokemoncenter.com/category/new-releases",
    "https://www.pokemoncenter.com/search/newest",
]

KEYWORDS = [
    "elite trainer box",
    "booster bundle",
    "booster display box",
    "booster pack",
    "pokemon tcg",
]

STATE_FILE = "state.json"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

HEADERS = {"User-Agent": "Mozilla/5.0 (PokemonCenterMonitor/1.0)"}

def post_discord(msg: str):
    if not DISCORD_WEBHOOK:
        print("Missing DISCORD_WEBHOOK secret.")
        return
    requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=20)

def extract_product_urls(html: str):
    urls = set(re.findall(r'href="([^"]+)"', html))
    out = set()
    for u in urls:
        if "/product/" in u:
            if u.startswith("/"):
                u = "https://www.pokemoncenter.com" + u
            out.add(u.split("?")[0])
    return sorted(out)

def keyword_match(url: str):
    u = url.lower()
    return any(k in u for k in KEYWORDS)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"seen": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def main():
    state = load_state()
    seen = set(state.get("seen", []))
    new_hits = []

    for page in URLS:
        r = requests.get(page, headers=HEADERS, timeout=25)
        r.raise_for_status()
        products = extract_product_urls(r.text)

        for p in products[:300]:
            if p not in seen and keyword_match(p):
                new_hits.append(p)

        for p in products:
            seen.add(p)

    state["seen"] = sorted(seen)
    save_state(state)

    if new_hits:
        msg = "🚨 New Pokémon Center TCG item(s) detected:\n" + "\n".join(new_hits[:15])
        post_discord(msg)
        print(msg)
    else:
        print("No new items.")

if __name__ == "__main__":
    main()


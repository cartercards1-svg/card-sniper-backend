from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import statistics
import re

app = Flask(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}

CASE_HITS = ["kaboom", "downtown", "color blast", "uptown", "manga"]

def clean_title(title):
    title = title.lower()
    title = re.sub(r'[^a-z0-9 ]', '', title)
    words = title.split()

    filtered = [w for w in words if w not in [
        "rookie", "rc", "auto", "patch", "panini", "prizm"
    ]]

    return " ".join(filtered[:6])

def get_active():
    url = "https://www.ebay.com/sch/i.html?_nkw=sports+cards&_sop=10&LH_BIN=1"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select(".s-item")[:25]
    listings = []

    for item in items:
        title = item.select_one(".s-item__title")
        price = item.select_one(".s-item__price")
        link = item.select_one("a")

        if not title or not price:
            continue

        try:
            p = float(price.text.replace("$", "").replace(",", "").split()[0])
        except:
            continue

        listings.append({
            "title": title.text,
            "price": p,
            "link": link.get("href")
        })

    return listings

def get_comps(search):
    url = f"https://www.ebay.com/sch/i.html?_nkw={search}&LH_Sold=1&LH_Complete=1"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    prices = []

    for item in soup.select(".s-item")[:10]:
        price = item.select_one(".s-item__price")
        if not price:
            continue

        try:
            p = float(price.text.replace("$", "").replace(",", "").split()[0])
            prices.append(p)
        except:
            continue

    if len(prices) < 3:
        return None

    avg = statistics.mean(prices)
    filtered = [p for p in prices if 0.5 * avg < p < 1.5 * avg]

    if len(filtered) < 3:
        return avg

    return statistics.mean(filtered)

@app.route("/api")
def api():
    data = []
    listings = get_active()

    for item in listings:
        search = clean_title(item["title"])
        value = get_comps(search)

        if not value:
            continue

        percent = round((item["price"] / value) * 100)
        is_case = any(k in item["title"].lower() for k in CASE_HITS)

        if (is_case and percent <= 100) or (not is_case and percent <= 90):
            data.append({
                "title": item["title"],
                "price": item["price"],
                "value": round(value, 2),
                "percent": percent,
                "link": item["link"],
                "case_hit": is_case
            })

    return jsonify(data)

app.run(host="0.0.0.0", port=10000)

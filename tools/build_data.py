#!/usr/bin/env python3
"""Збирає data.js для сайту Mezey Shop з даних iOS-застосунку.

Джерело — ~/Documents/Jabko/ios/Jabko/Data (вже відфільтровано tools/mezey_filter.py:
лише Apple і консолі PS5). Результат — data.js поруч з index.html:
  window.MZ = {meta, categories, products, details, home, contacts}

Запуск:  python3 tools/build_data.py
"""
import json
from pathlib import Path

APP_DATA = Path.home() / "Documents" / "Jabko" / "ios" / "Jabko" / "Data"
OUT = Path(__file__).resolve().parent.parent / "data.js"
SHARDS = 64

# З профілю instagram.com/mezey_shop (13.11.2026). Адрес не публікуємо.
CONTACTS = {
    "phone": "+38 096 847 76 27",
    "tel": "+380968477627",
    "hours": "пн–сб 09:00–18:00, нд — вихідний",
    "telegram": "https://t.me/mezeyshop",
    "telegramName": "t.me/mezeyshop",
    "instagram": "https://www.instagram.com/mezey_shop/",
    "instagramName": "@mezey_shop",
}


def read(name):
    return json.loads((APP_DATA / name).read_text(encoding="utf-8"))


def used_categories(categories, products):
    """Лише категорії з товарами та їхні батьки — решта сайту не потрібна."""
    by_id = {c["id"]: c for c in categories}
    keep = set()
    for p in products:
        for cid in [p["c"], *p.get("cx", [])]:
            while cid is not None and cid not in keep and cid in by_id:
                keep.add(cid)
                cid = by_id[cid]["parent"]
    return [c for c in categories if c["id"] in keep]


def main():
    catalog = read("catalog.json")
    products = catalog["products"]
    if not products:
        raise SystemExit("У catalog.json немає товарів — спершу запусти build_catalog.py і mezey_filter.py")
    ids = {str(p["id"]) for p in products}
    details = {}
    for n in range(SHARDS):
        details |= {k: v for k, v in read(f"details-{n:02d}.json").items() if k in ids}
    home = read("home.json")
    # Посилання на сторінки jabko.ua сайту не потрібні; гравіювання Mezey Shop не пропонує.
    tiles = [t for t in home["tiles"] if t["link"].get("path", "").strip("/") != "grava"]
    data = {
        "meta": catalog["meta"],
        "categories": used_categories(catalog["categories"], products),
        "products": [{k: v for k, v in p.items() if k != "u"} for p in products],
        "details": details,
        # Банери — рекламні макети Ябко, на публічному сайті їх не показуємо.
        "home": {k: home[k] for k in ("quick", "menu", "about")} | {"tiles": tiles},
        "contacts": CONTACTS,
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(f"window.MZ={payload};\n", encoding="utf-8")
    print(f"data.js: {len(products)} товарів, {len(data['categories'])} категорій, "
          f"{len(details)} описів, {OUT.stat().st_size // 1024} КБ")


if __name__ == "__main__":
    main()

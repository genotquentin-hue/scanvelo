"""Scraper pour 2ememain.be (catégorie vélos).

Bonne surprise : le site est en Next.js et embarque toutes les données des
annonces dans un bloc JSON `<script id="__NEXT_DATA__">`. On parse ce JSON
plutôt que le HTML visuel : c'est beaucoup plus fiable que des sélecteurs CSS
(qui cassent au moindre changement de design).
"""
import json
import re
from urllib.parse import quote_plus

from config import SEARCH_KEYWORDS
from scraper.base import BaseScraper

BASE = "https://www.2ememain.be"
# La recherche se fait dans la catégorie "vélos et vélomoteurs".
SEARCH_TEMPLATE = BASE + "/l/velos-velomoteurs/q/{keyword}/"

# Sous-catégories à exclure : ce sont des pièces/accessoires, pas des vélos.
EXCLUDED_URL_PARTS = ("/velos-pieces/", "/velos-accessoires/")

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


class DeuxiememainScraper(BaseScraper):
    source = "2ememain"
    home_url = BASE + "/"

    def search_urls(self) -> list[tuple[str, str]]:
        # quote_plus encode les espaces et caractères spéciaux pour l'URL
        # (ex: "van rysel grvl" → "van+rysel+grvl").
        return [
            (kw, SEARCH_TEMPLATE.format(keyword=quote_plus(kw)))
            for kw in SEARCH_KEYWORDS
        ]

    def parse_listings(self, html: str) -> list[dict]:
        match = NEXT_DATA_RE.search(html)
        if not match:
            print("  [warn] __NEXT_DATA__ introuvable (structure du site modifiée ?)")
            return []

        try:
            data = json.loads(match.group(1))
            raw = data["props"]["pageProps"]["searchRequestAndResponse"]["listings"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [warn] JSON inattendu : {e}")
            return []

        results = []
        for item in raw:
            listing = self._normalize(item)
            if listing:
                results.append(listing)
        return results

    def _normalize(self, item: dict) -> dict | None:
        """Transforme une annonce brute du JSON en notre format standard."""
        vip_url = item.get("vipUrl", "")
        if any(part in vip_url for part in EXCLUDED_URL_PARTS):
            return None  # c'est une pièce détachée, pas un vélo

        item_id = item.get("itemId")
        if not item_id:
            return None

        price_info = item.get("priceInfo", {}) or {}
        price_cents = price_info.get("priceCents")
        price_type = price_info.get("priceType", "")

        location = item.get("location", {}) or {}
        image_urls = item.get("imageUrls") or []
        image_url = image_urls[0] if image_urls else None
        # Les URLs d'images commencent par "//" → on ajoute https:
        if image_url and image_url.startswith("//"):
            image_url = "https:" + image_url

        return {
            "id": item_id,
            "source": self.source,
            "title": item.get("title", "").strip(),
            "description": (item.get("description") or "").strip(),
            "price_cents": price_cents,
            "price_type": price_type,
            "price_raw": _format_price(price_cents, price_type),
            "location": location.get("cityName"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "on_country_level": location.get("onCountryLevel", False),
            "url": BASE + vip_url if vip_url.startswith("/") else vip_url,
            "image_url": image_url,
            "posted_at": item.get("date"),  # ex: "Aujourd'hui", "Hier", "12 mai"
        }


def _format_price(price_cents: int | None, price_type: str) -> str:
    """Formate le prix pour l'affichage humain."""
    if price_cents is None:
        return "Prix non précisé"
    euros = price_cents / 100
    if price_cents == 0:
        # prix non renseigné : "faire une offre" / à débattre (pas gratuit)
        return "Prix à débattre"
    if price_type == "MIN_BID":
        return f"À partir de {euros:.0f} €"
    return f"{euros:.0f} €"

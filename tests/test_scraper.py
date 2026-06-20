"""Tests pour scraper/deuxiememain.py — parse JSON et normalisation."""
import json
import pytest
from scraper.deuxiememain import DeuxiememainScraper, _format_price


def _make_html(listings: list) -> str:
    """Construit un faux HTML Next.js avec les annonces données."""
    data = {
        "props": {
            "pageProps": {
                "searchRequestAndResponse": {
                    "listings": listings
                }
            }
        }
    }
    return f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script>'


def _raw_item(**kwargs) -> dict:
    """Annonce brute minimale valide issue du JSON 2ememain."""
    base = {
        "itemId": "12345",
        "title": "Gravel Trek Checkpoint",
        "description": "Très bon état, taille M",
        "vipUrl": "/v/velos-velomoteurs/gravel-trek/12345.html",
        "priceInfo": {"priceCents": 75000, "priceType": "FIXED"},
        "location": {"cityName": "Ixelles", "latitude": 50.827, "longitude": 4.373, "onCountryLevel": False},
        "imageUrls": ["//photos.2ememain.be/img.jpg"],
        "date": "Aujourd'hui",
    }
    base.update(kwargs)
    return base


@pytest.fixture
def scraper():
    return DeuxiememainScraper()


# ── _format_price ────────────────────────────────────────────────────────────

def test_format_price_normal():
    assert _format_price(75000, "FIXED") == "750 €"

def test_format_price_zero_debattre():
    assert _format_price(0, "FIXED") == "Prix à débattre"

def test_format_price_none():
    assert _format_price(None, "") == "Prix non précisé"

def test_format_price_min_bid():
    assert _format_price(50000, "MIN_BID") == "À partir de 500 €"


# ── _normalize ───────────────────────────────────────────────────────────────

def test_normalize_annonce_valide(scraper):
    result = scraper._normalize(_raw_item())
    assert result["id"] == "12345"
    assert result["title"] == "Gravel Trek Checkpoint"
    assert result["price_cents"] == 75000
    assert result["location"] == "Ixelles"
    assert result["url"].startswith("https://www.2ememain.be")

def test_normalize_exclut_pieces(scraper):
    item = _raw_item(vipUrl="/v/velos-pieces/frein/99.html")
    assert scraper._normalize(item) is None

def test_normalize_exclut_accessoires(scraper):
    item = _raw_item(vipUrl="/v/velos-accessoires/casque/88.html")
    assert scraper._normalize(item) is None

def test_normalize_sans_item_id(scraper):
    item = _raw_item(itemId=None)
    assert scraper._normalize(item) is None

def test_normalize_image_url_ajoute_https(scraper):
    result = scraper._normalize(_raw_item(imageUrls=["//photos.2ememain.be/img.jpg"]))
    assert result["image_url"].startswith("https://")

def test_normalize_sans_image(scraper):
    result = scraper._normalize(_raw_item(imageUrls=[]))
    assert result["image_url"] is None

def test_normalize_url_absolue_inchangee(scraper):
    item = _raw_item(vipUrl="https://autre-domaine.be/annonce/1.html")
    result = scraper._normalize(item)
    assert result["url"] == "https://autre-domaine.be/annonce/1.html"


# ── parse_listings ───────────────────────────────────────────────────────────

def test_parse_listings_retourne_annonces(scraper):
    html = _make_html([_raw_item(), _raw_item(itemId="99999", title="Ridley X-Night")])
    results = scraper.parse_listings(html)
    assert len(results) == 2
    assert results[1]["title"] == "Ridley X-Night"

def test_parse_listings_sans_next_data(scraper):
    results = scraper.parse_listings("<html><body>Rien ici</body></html>")
    assert results == []

def test_parse_listings_json_invalide(scraper):
    html = '<script id="__NEXT_DATA__">{ invalid json }</script>'
    results = scraper.parse_listings(html)
    assert results == []

def test_parse_listings_structure_inattendue(scraper):
    data = {"props": {"pageProps": {}}}  # clé 'searchRequestAndResponse' absente
    html = f'<script id="__NEXT_DATA__">{json.dumps(data)}</script>'
    results = scraper.parse_listings(html)
    assert results == []

def test_parse_listings_filtre_pieces_auto(scraper):
    items = [
        _raw_item(itemId="1"),
        _raw_item(itemId="2", vipUrl="/v/velos-pieces/frein/2.html"),
    ]
    results = scraper.parse_listings(_make_html(items))
    assert len(results) == 1
    assert results[0]["id"] == "1"

"""Filtres pour ne garder que les annonces pertinentes.

Fonctions pures (entrée → sortie, sans effet de bord) : faciles à tester
isolément. main.py les combine via passes_filters().
"""
import math
import re

from config import (
    BRUSSELS_CITIES,
    MAX_DISTANCE_KM,
    MAX_PRICE_CENTS,
    MIN_PRICE_CENTS,
)

# Centre de Bruxelles (Grand-Place) pour le calcul de distance.
BRUSSELS_LAT = 50.8467
BRUSSELS_LON = 4.3525

# Détecte une mention de taille M dans le texte. Le \b = "frontière de mot"
# évite de matcher le M de "Medium frame" au milieu d'un mot.
# Couvre fr/nl/en : "taille M", "maat M", "size M", "M/54", "(M)".
SIZE_M_RE = re.compile(
    r"\b(?:taille|maat|size|gr[öo]sse|frame)\s*[:\-]?\s*M\b"
    r"|\bM\b\s*[/(\[]"
    r"|\btaille\s+m\b",
    re.IGNORECASE,
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en km entre deux points GPS (formule de haversine).

    Haversine = calcul de distance à vol d'oiseau sur une sphère. Largement
    assez précis pour savoir si une annonce est dans les 20km de Bruxelles.
    """
    r = 6371  # rayon de la Terre en km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return r * 2 * math.asin(math.sqrt(a))


def distance_to_brussels(listing: dict) -> float | None:
    """Distance de l'annonce au centre de Bruxelles, ou None si inconnue."""
    lat, lon = listing.get("latitude"), listing.get("longitude")
    if lat is None or lon is None:
        return None
    return haversine_km(BRUSSELS_LAT, BRUSSELS_LON, lat, lon)


def passes_location(listing: dict) -> bool:
    """Vrai si l'annonce est dans le rayon autour de Bruxelles.

    Stratégie : on utilise les coordonnées GPS si dispo (précis). Sinon on
    se rabat sur le nom de ville comparé à la liste blanche. Si on n'a ni
    l'un ni l'autre, on garde l'annonce (mieux vaut un faux positif qu'un raté).
    """
    dist = distance_to_brussels(listing)
    if dist is not None:
        return dist <= MAX_DISTANCE_KM

    city = (listing.get("location") or "").lower()
    if city:
        # match si un des noms connus apparaît dans le nom de ville
        return any(known in city for known in BRUSSELS_CITIES)

    return True  # localisation inconnue → on ne jette pas


def passes_price(listing: dict) -> bool:
    """Vrai si le prix est dans la fourchette. Garde les annonces sans prix
    (ex: 'faire une offre') car ça peut être une bonne affaire à négocier."""
    price = listing.get("price_cents")
    if price is None or price == 0:
        return True
    return MIN_PRICE_CENTS <= price <= MAX_PRICE_CENTS


def has_size_m(listing: dict) -> bool:
    """Vrai si la taille M est mentionnée. NON bloquant : sert juste à
    afficher un indicateur dans la notif (le filtre taille est indicatif)."""
    text = f"{listing.get('title', '')} {listing.get('description', '')}"
    return bool(SIZE_M_RE.search(text))


def passes_filters(listing: dict) -> bool:
    """Combine les filtres bloquants : localisation ET prix.

    La taille n'est PAS un filtre bloquant (beaucoup d'annonces ne la
    précisent pas) — on l'affiche seulement dans la notification.
    """
    return passes_location(listing) and passes_price(listing)

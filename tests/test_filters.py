"""Tests pour filters.py — fonctions pures, pas de mock nécessaire."""
import pytest
from filters import (
    haversine_km,
    passes_location,
    passes_price,
    has_size_m,
    passes_gender,
    passes_filters,
)

# Centre de Bruxelles (référence)
BXL_LAT, BXL_LON = 50.8467, 4.3525


# ── haversine_km ────────────────────────────────────────────────────────────

def test_haversine_meme_point_est_zero():
    assert haversine_km(BXL_LAT, BXL_LON, BXL_LAT, BXL_LON) == pytest.approx(0.0)

def test_haversine_bruxelles_anvers_environ_45km():
    # Anvers ~45 km au nord de Bruxelles
    dist = haversine_km(BXL_LAT, BXL_LON, 51.2194, 4.4025)
    assert 40 < dist < 50

def test_haversine_symetrique():
    d1 = haversine_km(50.0, 4.0, 51.0, 5.0)
    d2 = haversine_km(51.0, 5.0, 50.0, 4.0)
    assert d1 == pytest.approx(d2)


# ── passes_location ─────────────────────────────────────────────────────────

def _listing(lat=None, lon=None, location=None):
    return {"latitude": lat, "longitude": lon, "location": location}

def test_passes_location_gps_dans_rayon():
    # Uccle : ~6 km de Bruxelles
    assert passes_location(_listing(lat=50.80, lon=4.36))

def test_passes_location_gps_hors_rayon():
    # Liège : ~95 km
    assert not passes_location(_listing(lat=50.6450, lon=5.5730))

def test_passes_location_ville_connue():
    assert passes_location(_listing(location="Ixelles"))

def test_passes_location_ville_hors_liste():
    # Ville hors liste blanche sans GPS → écartée
    assert not passes_location(_listing(location="Liège"))

def test_passes_location_sans_info_garde():
    # Aucune localisation → on ne jette pas
    assert passes_location(_listing())


# ── passes_price ────────────────────────────────────────────────────────────

def test_passes_price_dans_fourchette():
    assert passes_price({"price_cents": 50000})  # 500 €

def test_passes_price_trop_cher():
    assert not passes_price({"price_cents": 200000})  # 2000 €

def test_passes_price_trop_bon_marche():
    assert not passes_price({"price_cents": 1000})  # 10 €

def test_passes_price_none_garde():
    assert passes_price({"price_cents": None})

def test_passes_price_zero_garde():
    # 0 = "faire une offre", pas un vrai prix
    assert passes_price({"price_cents": 0})

def test_passes_price_cle_absente_garde():
    assert passes_price({})


# ── has_size_m ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "taille M",
    "Taille M",
    "maat M",
    "size M",
    "M/54",
    "M (54cm)",
    "taille m",
])
def test_has_size_m_detection(text):
    assert has_size_m({"title": text, "description": ""})

@pytest.mark.parametrize("text", [
    "cadre XL",
    "taille L",
    "Merckx Edition",   # M dans un mot → ne doit pas matcher
    "Momentum",
])
def test_has_size_m_pas_de_faux_positif(text):
    assert not has_size_m({"title": text, "description": ""})

def test_has_size_m_dans_description():
    assert has_size_m({"title": "gravel", "description": "frame size M, bon état"})


# ── passes_gender ────────────────────────────────────────────────────────────

def test_passes_gender_url_neutre():
    assert passes_gender({"url": "https://www.2ememain.be/a/velos-velomoteurs/gravel.html"})

def test_passes_gender_velos_femmes():
    assert not passes_gender({"url": "https://www.2ememain.be/a/velos-femmes/rose.html"})

def test_passes_gender_velos_dames():
    assert not passes_gender({"url": "https://www.2ememain.be/a/velos-dames/trek.html"})

def test_passes_gender_damesfiets():
    assert not passes_gender({"url": "https://www.2ememain.be/a/damesfiets/btwin.html"})

def test_passes_gender_url_absente():
    assert passes_gender({})


# ── passes_filters ───────────────────────────────────────────────────────────

def _full_listing(**kwargs):
    base = {
        "latitude": 50.80, "longitude": 4.36,  # Uccle, dans le rayon
        "price_cents": 50000,
        "url": "https://www.2ememain.be/a/velos-velomoteurs/gravel.html",
    }
    base.update(kwargs)
    return base

def test_passes_filters_annonce_valide():
    assert passes_filters(_full_listing())

def test_passes_filters_ecarte_si_hors_rayon():
    assert not passes_filters(_full_listing(latitude=50.6450, longitude=5.5730))

def test_passes_filters_ecarte_si_trop_cher():
    assert not passes_filters(_full_listing(price_cents=200000))

def test_passes_filters_ecarte_si_femmes():
    assert not passes_filters(_full_listing(url="https://www.2ememain.be/a/velos-femmes/rose.html"))

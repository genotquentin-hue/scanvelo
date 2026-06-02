"""Classe de base commune à tous les scrapers.

Chaque site concret (2ememain, plus tard marktplaats) hérite de BaseScraper
et n'a qu'à implémenter deux choses : comment construire les URLs de recherche,
et comment parser le HTML d'une page de résultats.
"""
import random
import time
from abc import ABC, abstractmethod

import requests

# User-Agent réaliste : un vrai navigateur Chrome sur Linux.
# Un User-Agent absent ou bidon est le premier signal qui fait bloquer un bot.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "fr-BE,fr;q=0.9,nl;q=0.8,en-GB;q=0.7",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}


class BaseScraper(ABC):
    """Squelette de scraper. source = nom court du site (ex: '2ememain')."""

    source: str = "base"
    home_url: str = ""

    def __init__(self):
        # Une Session réutilise la connexion TCP et garde les cookies entre
        # les requêtes : plus rapide et plus « humain » qu'une requête isolée.
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._warmed_up = False

    def warm_up(self) -> None:
        """Visite la page d'accueil pour récupérer les cookies de session.

        Un vrai humain arrive d'abord sur l'accueil avant de chercher.
        Sauter cette étape et taper direct sur une URL de recherche est
        suspect pour les protections anti-bot.
        """
        if self._warmed_up or not self.home_url:
            return
        try:
            self.session.get(self.home_url, timeout=15)
            self._polite_sleep(2, 5)
            self._warmed_up = True
        except requests.RequestException:
            # Pas grave si l'accueil échoue : on tentera quand même la recherche.
            pass

    def fetch(self, url: str, referer: str | None = None) -> str | None:
        """Télécharge une page. Retourne le HTML ou None en cas d'erreur."""
        headers = {}
        if referer:
            headers["Referer"] = referer
        try:
            resp = self.session.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"  [warn] échec de {url} : {e}")
            return None

    @staticmethod
    def _polite_sleep(low: float = 4, high: float = 12) -> None:
        """Pause aléatoire. Un délai FIXE entre requêtes trahit un bot ;
        un délai aléatoire imite mieux un humain."""
        time.sleep(random.uniform(low, high))

    @abstractmethod
    def search_urls(self) -> list[tuple[str, str]]:
        """Retourne une liste de (mot_clé, url_de_recherche)."""

    @abstractmethod
    def parse_listings(self, html: str) -> list[dict]:
        """Extrait les annonces d'une page de résultats HTML."""

    def run(self) -> list[dict]:
        """Lance le scraping complet du site et retourne toutes les annonces.

        La déduplication (annonces déjà vues) se fait plus haut, dans main.py.
        """
        self.warm_up()
        all_listings: list[dict] = []
        searches = self.search_urls()
        # Ordre aléatoire des recherches : ne jamais taper les URLs
        # toujours dans le même ordre, c'est plus naturel.
        random.shuffle(searches)

        for keyword, url in searches:
            html = self.fetch(url, referer=self.home_url)
            if html:
                listings = self.parse_listings(html)
                print(f"  [{self.source}] '{keyword}' → {len(listings)} annonce(s)")
                all_listings.extend(listings)
            self._polite_sleep()

        return all_listings

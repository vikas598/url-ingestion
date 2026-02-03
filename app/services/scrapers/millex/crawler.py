import time
import requests
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from typing import Set, Dict


HEADERS = {
    "User-Agent": "Mozilla/5.0 (MillexCrawler/1.0)"
}

REQUEST_DELAY = 0.5  # seconds
TIMEOUT = 10


class MillexCrawler:
    """
    Site crawler for millex.in

    Responsibilities:
    - Discover URLs
    - Classify pages (collections, products, static)
    - NO scraping logic
    - NO UI validation
    """

    def __init__(self, base_url: str, max_depth: int = 3):
        self.base_url = base_url.rstrip("/")
        parsed = urlparse(self.base_url)

        self.scheme = parsed.scheme
        self.domain = parsed.netloc
        self.max_depth = max_depth

        self.visited: Set[str] = set()
        self.queue: list[tuple[str, int]] = [(self.base_url, 0)]

        self.discovered: Dict[str, Set[str]] = {
            "homepage": set(),
            "collections": set(),
            "products": set(),
            "static_pages": set(),
        }

        self.stats = {
            "pages_fetched": 0,
            "errors": 0,
        }

    # ---------------- public ---------------- #

    def crawl(self) -> dict:
        while self.queue:
            url, depth = self.queue.pop(0)

            if url in self.visited:
                continue

            # limit crawl depth (except products)
            if depth > self.max_depth and "/products/" not in url:
                continue

            self.visited.add(url)

            html = self._fetch_html(url)
            if not html:
                continue

            page_type = self._classify_url(url)
            self._store_url(page_type, url)

            for link in self._extract_links(html, url):
                if link not in self.visited:
                    self.queue.append((link, depth + 1))

        return {
            "discovered": self.discovered,
            "stats": self.stats,
        }

    # ---------------- internal ---------------- #

    def _fetch_html(self, url: str) -> str | None:
        try:
            time.sleep(REQUEST_DELAY)
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            self.stats["pages_fetched"] += 1
            return r.text
        except Exception:
            self.stats["errors"] += 1
            return None

    def _extract_links(self, html: str, base_url: str) -> Set[str]:
        soup = BeautifulSoup(html, "html.parser")
        links: Set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            # ignore junk
            if href.startswith(("mailto:", "tel:", "#", "javascript:")):
                continue

            abs_url = urljoin(base_url, href)
            normalized = self._normalize_url(abs_url)

            if not normalized:
                continue

            links.add(normalized)

        return links

    def _normalize_url(self, url: str) -> str | None:
        """
        Normalize URLs:
        - same domain only
        - keep pagination (?page=)
        - drop fragments and junk queries
        """
        parsed = urlparse(url)

        if parsed.netloc != self.domain:
            return None

        query = ""
        if parsed.query.startswith("page="):
            query = parsed.query

        clean = urlunparse((
            self.scheme,
            self.domain,
            parsed.path.rstrip("/"),
            "",
            query,
            ""
        ))

        return clean

    def _classify_url(self, url: str) -> str:
        path = urlparse(url).path

        if path in ("", "/"):
            return "homepage"
        if path.startswith("/products/"):
            return "products"
        if path.startswith("/collections/"):
            return "collections"
        if path.startswith("/pages/"):
            return "static_pages"

        return "ignore"

    def _store_url(self, page_type: str, url: str) -> None:
        if page_type in self.discovered:
            self.discovered[page_type].add(url)


# ---------------- manual test ---------------- #

if __name__ == "__main__":
    crawler = MillexCrawler(
        base_url="https://millex.in",
        max_depth=3
    )

    result = crawler.crawl()

    print("\n--- CRAWLER STATS ---")
    print(result["stats"])

    print("\n--- COLLECTIONS ---")
    for u in sorted(result["discovered"]["collections"]):
        print(u)

    print("\n--- PRODUCTS (count only) ---")
    print(len(result["discovered"]["products"]))

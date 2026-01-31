import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class MillexCrawler:
    def __init__(self, base_url: str, max_depth: int = 3):
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth

        self.visited = set()
        self.queue = [(self.base_url, 0)]

        self.discovered = {
            "homepage": set(),
            "collections": set(),
            "products": set(),
            "static_pages": set(),
        }

        self.stats = {
            "pages_fetched": 0,
            "errors": 0,
        }

    def crawl(self) -> dict:
        while self.queue:
            url, depth = self.queue.pop(0)

            if url in self.visited:
                continue

            # allow deep product pages, limit others
            if depth > self.max_depth and "/products/" not in url:
                continue

            self.visited.add(url)

            html = self._fetch_html(url)
            if not html:
                continue

            page_type = self._classify_url(url)
            self._store_url(page_type, url)

            links = self._extract_links(html, url)
            for link in links:
                if link not in self.visited:
                    self.queue.append((link, depth + 1))

        return {
            "discovered": self.discovered,
            "stats": self.stats,
        }

    def _fetch_html(self, url: str) -> str | None:
        try:
            time.sleep(0.5)  # rate limiting (MANDATORY)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.stats["pages_fetched"] += 1
            return response.text
        except Exception:
            self.stats["errors"] += 1
            return None

    def _extract_links(self, html: str, base_url: str) -> set[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            # ignore junk
            if href.startswith(("mailto:", "tel:", "#", "javascript:")):
                continue

            abs_url = urljoin(base_url, href)
            parsed = urlparse(abs_url)

            # same domain only
            if parsed.netloc != self.domain:
                continue

            # allow pagination queries only
            query = parsed.query if "page=" in parsed.query else ""

            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if query:
                clean_url += f"?{query}"

            links.add(clean_url.rstrip("/"))

        return links

    def _classify_url(self, url: str) -> str:
        path = urlparse(url).path

        if path in ("", "/", "/index.php"):
            return "homepage"
        if "/products/" in path:
            return "products"
        if "/collections/" in path:
            return "collections"
        if "/pages/" in path:
            return "static_pages"

        return "ignore"

    def _store_url(self, page_type: str, url: str):
        if page_type in self.discovered:
            self.discovered[page_type].add(url)

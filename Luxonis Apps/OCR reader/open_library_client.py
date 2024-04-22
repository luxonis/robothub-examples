import logging as log
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable

import requests
from model import SearchResult

# Open Library URLs
OLIB_URL = "https://openlibrary.org"
OLIB_COVER_URL = "https://covers.openlibrary.org"
COVER_PLACEHOLDER_URL = "https://openlibrary.org/images/icons/avatar_book-sm.png"
OLIB_SEARCH_URL = f"{OLIB_URL}/search.json"

RESULT_LIMIT = 5


class OpenLibraryClient:
    def __init__(self) -> None:
        self.thread_pool_executor = ThreadPoolExecutor(max_workers=1)
        self.searching = False

    def search_open_library(self, query: str) -> list[SearchResult]:
        """Search query on https://openlibrary.org and return results."""

        res = requests.get(OLIB_SEARCH_URL, {"q": query, "limit": RESULT_LIMIT})
        data = res.json()
        search_results = []
        for doc in data["docs"]:
            try:
                if "cover_i" in doc:
                    cover_id = doc["cover_i"]
                    cover_url = f"{OLIB_COVER_URL}/b/id/{cover_id}-M.jpg"
                else:
                    cover_url = COVER_PLACEHOLDER_URL
                first_publish_year = doc.get("first_publish_year", None)
                book_url = f"{OLIB_URL}/{doc['key']}"
                author_urls = [f"{OLIB_URL}/authors/{i}" for i in doc["author_key"]]
                res = SearchResult(
                    cover_url=cover_url,
                    title=doc["title"],
                    authors=doc["author_name"],
                    first_publish_year=first_publish_year,
                    book_url=book_url,
                    author_urls=author_urls,
                )
                search_results.append(res)
            except Exception:
                log.exception("Book parsing failed")
        return search_results

    def search_open_library_async(
        self, query: str, callback: Callable[[list[SearchResult]], None]
    ):
        if not self.searching:
            self.searching = True
            future = self.thread_pool_executor.submit(self.search_open_library, query)

            def _done(result: Future[list[SearchResult]]):
                self.searching = False
                callback(result.result())

            future.add_done_callback(_done)
        else:
            raise RuntimeError("Search is already in progress")

    def stop(self):
        self.thread_pool_executor.shutdown()

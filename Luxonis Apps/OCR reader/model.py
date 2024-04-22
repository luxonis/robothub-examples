from dataclasses import dataclass


@dataclass
class SearchResult:
    cover_url: str
    title: str
    first_publish_year: int
    book_url: str
    authors: list[str]
    author_urls: list[str]


@dataclass
class TextDetection:
    bbox_points: list[tuple[int, int]]
    confidence: float
    text: str

from dataclasses import asdict
from typing import Literal

import robothub as rh
from model import SearchResult

Status = Literal["finished_searching"] | Literal["searching"]


def send_status_update(status: Status, query: str):
    rh.COMMUNICATOR.notify(
        "status_update", {"status": "finished_searching", "query": query}
    )


def send_search_results(search_results: list[SearchResult]):
    res_dict = [asdict(i) for i in search_results]
    rh.COMMUNICATOR.notify("search_results", {"search_results": res_dict})

import json
import logging

from pathlib import Path
from typing import List, Literal

from build_typing import BuildQueueItem


logging.basicConfig(
    filename="buildQueue.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s"
)


class BuildQueue:

    MAX_SIZE = 10
    def __init__(self):
        self.queue_file = (
            Path(__file__).resolve().parent
            / "queue.json"
        )
        if not self.queue_file.exists():
            self._write([])

    def _read(self) -> List[BuildQueueItem]:
        try:
            with open(self.queue_file, "r") as f:
                return json.load(f)

        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write(
        self,
        queue: List[BuildQueueItem]
    ) -> None:

        with open(self.queue_file, "w") as f:
            json.dump(queue, f, indent=4)

    def add_item(
        self,
        item: BuildQueueItem
    ) -> None:
        queue = self._read()
        if len(queue) >= self.MAX_SIZE:
            queue.pop(0)
        queue.append(item)
        self._write(queue)
        logging.info(
            f"Added item: {item}"
        )

    def get_queue(self) -> List[BuildQueueItem]:
        return self._read()

    def get_pending(self) -> List[BuildQueueItem]:

        queue = self._read()

        return [
            item
            for item in queue
            if item["status"] == "pending"
        ]

    def update_item_status(
        self,
        item_id: str,
        new_status: Literal[
            "pending",
            "in_progress",
            "completed",
            "failed"
        ]
    ) -> None:

        queue = self._read()

        for item in queue:
            if item["id"] == item_id:
                item["status"] = new_status
                self._write(queue)
                logging.info(
                    f"Updated {item_id} -> {new_status}"
                )
                return

Queue = BuildQueue()
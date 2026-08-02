from typing import TypedDict, Literal

class BuildQueueItem(TypedDict):
    id: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    version: str
    url: str
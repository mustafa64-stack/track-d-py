from dataclasses import dataclass
from typing import Optional


@dataclass
class Question:
    id: str
    type: str
    stem: str
    options: Optional[list[str]]
    answer: str
    explanation: str
    topic_id: str
    source_ref: str
    difficulty: str
    verified: bool
    hash: str
    embedding: Optional[list[float]]

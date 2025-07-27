from dataclasses import dataclass

@dataclass
class Endpoint:
    path: str
    method: str
    summary: str

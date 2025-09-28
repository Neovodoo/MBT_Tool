from dataclasses import dataclass, field
from typing import List, Dict, Any


SEPARATOR_LINE = "-" * 20

@dataclass
class EnvironmentBlock:
    servers: List[str] = field(default_factory=list)

    def to_text(self) -> List[str]:
        lines = ["Окружение:", f"", "- Сервера:"]
        if self.servers:
            lines.extend([f"    - {s}" for s in self.servers])
        else:
            lines.append("  - -")
        lines.append("")
        lines.append(SEPARATOR_LINE)
        return lines

    def extract_servers(self, spec: Dict[str, Any]) -> List[str]:
        self.servers = [s.get("url") for s in (spec.get("servers") or []) if isinstance(s.get("url"), str)]
        return self.servers
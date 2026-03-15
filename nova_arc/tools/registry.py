from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class RegisteredTool:
    name: str
    category: str
    description: str
    executor: Callable[[dict], object]

    def execute(self, args: dict):
        return self.executor(args)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, RegisteredTool] = {}

    def register(self, tool: RegisteredTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> RegisteredTool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name]

    def describe_all(self) -> List[dict]:
        return [
            {"name": t.name, "category": t.category, "description": t.description}
            for t in self._tools.values()
        ]

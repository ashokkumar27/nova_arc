class RegisteredTool:
    def __init__(self, name, category, executor):
        self.name = name
        self.category = category
        self._executor = executor

    def execute(self, args):
        return self._executor(args)


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool: RegisteredTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> RegisteredTool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name]

    def names(self):
        return list(self._tools.keys())

    def subset(self, allowed_names):
        subset_registry = ToolRegistry()
        for name in allowed_names:
            if name in self._tools:
                subset_registry.register(self._tools[name])
        return subset_registry
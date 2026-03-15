class RegisteredTool:
    def __init__(self, name, category, description="", executor=None):
        if executor is None:
            if callable(description):
                executor = description
                description = ""
            else:
                raise TypeError("RegisteredTool requires an executor callable")
        self.name = name
        self.category = category
        self.description = description
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

    def describe_all(self):
        return [
            {
                "name": tool.name,
                "category": tool.category,
                "description": tool.description,
            }
            for tool in self._tools.values()
        ]

    def subset(self, allowed_names):
        subset_registry = ToolRegistry()
        for name in allowed_names:
            if name in self._tools:
                subset_registry.register(self._tools[name])
        return subset_registry

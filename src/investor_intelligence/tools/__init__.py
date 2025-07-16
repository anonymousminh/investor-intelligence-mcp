def tool(name):
    def decorator(func):
        func._tool_name = name
        return func

    return decorator

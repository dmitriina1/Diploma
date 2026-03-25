from typing import Any, Callable, Dict, Optional


_resources: Dict[str, Any] = {}
_handlers: Dict[str, Callable[..., Any]] = {}


def configure_resources(**kwargs):
    _resources.update(kwargs)


def get_resource(name: str, default: Optional[Any] = None):
    return _resources.get(name, default)


def configure_handlers(**kwargs):
    _handlers.update(kwargs)


def get_handler(name: str) -> Callable[..., Any]:
    handler = _handlers.get(name)
    if handler is None:
        raise RuntimeError(f"Handler '{name}' is not configured")
    return handler

from contextvars import ContextVar

_base_url: ContextVar[str] = ContextVar("base_url", default="")


def set_base_url(url: str) -> None:
    _base_url.set(url.rstrip("/"))


def get_base_url() -> str:
    return _base_url.get()

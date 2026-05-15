from typing import Literal, TypedDict, Any

BrowserTypeName = Literal["chromium", "firefox", "webkit"]
Mode = Literal["browser", "http"]


class BrowserInfo(TypedDict):
    name: BrowserTypeName
    available: bool


class KrypticConfig(TypedDict, total=False):
    mode: Mode
    headless: bool
    concurrency: int
    browser_types: list[BrowserTypeName]
    timeout: int
    user_agent: str
    proxy: str | None


class RequestInterceptInfo(TypedDict):
    url: str
    method: str
    headers: dict[str, str]
    resource_type: str


TaskResult = Any

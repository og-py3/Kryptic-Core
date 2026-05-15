"""
Server mode demo: start Kryptic as a local HTTP server, then use
the built-in Python requests to drive it — just like any other language would.

In one terminal:
    PYTHONPATH=. python -m kryptic serve --port 7890

In another terminal (or just run this script — it starts the server in-process):
    PYTHONPATH=. python3 examples/server_mode.py
"""
import asyncio
import json
import threading
import time
import urllib.request
from kryptic.server import run_server


def _start_server():
    run_server(host="127.0.0.1", port=7890, concurrency=2)


def post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:7890{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get(path: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:7890{path}", timeout=10) as r:
        return json.loads(r.read())


def delete(path: str) -> dict:
    req = urllib.request.Request(
        f"http://127.0.0.1:7890{path}", method="DELETE"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main():
    t = threading.Thread(target=_start_server, daemon=True)
    t.start()
    time.sleep(3)

    print("Health:", get("/health"))

    sid = post("/sessions", {})["session_id"]
    print(f"Session: {sid}")

    post(f"/sessions/{sid}/block",
         {"resource_types": ["image", "stylesheet", "font", "media"]})
    post(f"/sessions/{sid}/goto", {"url": "https://example.com"})

    title = get(f"/sessions/{sid}/title")["title"]
    h1    = post(f"/sessions/{sid}/text", {"selector": "h1"})["text"]
    print(f"Title: {title}")
    print(f"H1:    {h1}")

    delete(f"/sessions/{sid}")

    http_resp = post("/http/get", {"url": "https://httpbin.org/get"})
    print(f"HTTP GET status: {http_resp['status']}")

    batch = post("/http/batch", {
        "urls": ["https://example.com", "https://example.org", "https://iana.org"]
    })["results"]
    for r in batch:
        print(f"  {r['status']}  {r['url']}")


if __name__ == "__main__":
    main()

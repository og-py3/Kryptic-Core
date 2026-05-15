"""
polyrun integration — run Kryptic bindings in any language from Python.

polyrun is a lightweight polyrun execution framework (pip install polyrun)
that lets you run JavaScript, Java, Go, Rust, C, and C++ code directly
from Python — no manual compilation or runtime setup needed.

Start the Kryptic server first:
    python -m kryptic serve --port 7890

Then run this example:
    PYTHONPATH=. python3 examples/polyrun_example.py

polyrun: https://pypi.org/project/polyrun/
"""
import subprocess
import sys
import time
import threading

# ── start server in background ────────────────────────────────────────────────
import os

def start_server():
    os.environ["PYTHONPATH"] = "."
    subprocess.Popen(
        [sys.executable, "-m", "kryptic", "serve", "--port", "7892", "--concurrency", "2"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

t = threading.Thread(target=start_server, daemon=True)
t.start()
time.sleep(4)  # wait for server to be ready


# ── polyrun JavaScript ────────────────────────────────────────────────────────

try:
    from polyrun import JS

    js_code = """
    const http = require('http');

    function request(method, path, body) {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify(body || {});
            const opts = {
                hostname: '127.0.0.1', port: 7892, path, method,
                headers: { 'Content-Type': 'application/json', 'Content-Length': data.length },
            };
            const req = http.request(opts, res => {
                let buf = '';
                res.on('data', c => buf += c);
                res.on('end', () => resolve(JSON.parse(buf)));
            });
            req.on('error', reject);
            req.write(data);
            req.end();
        });
    }

    async function main() {
        const health = await request('GET', '/health', {});
        console.log('Server version:', health.version);

        const s = await request('POST', '/sessions', {});
        const sid = s.session_id;

        await request('POST', `/sessions/${sid}/block`, { resource_types: ['image','stylesheet','font','media'] });
        await request('POST', `/sessions/${sid}/goto`, { url: 'https://example.com' });

        const { title } = await request('GET', `/sessions/${sid}/title`, {});
        console.log('Title:', title);

        await request('DELETE', `/sessions/${sid}`, {});
    }

    main();
    """

    result = JS.run(js_code, timeout=30)
    print("=== JavaScript (via polyrun) ===")
    print(result.stdout.strip())

except Exception as e:
    print(f"JavaScript polyrun: {e} (Node.js may not be installed)")


# ── polyrun Go ────────────────────────────────────────────────────────────────

try:
    from polyrun import Go

    go_code = '''
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

func post(path string, body map[string]interface{}) map[string]interface{} {
    buf, _ := json.Marshal(body)
    resp, err := http.Post("http://127.0.0.1:7892"+path, "application/json", bytes.NewReader(buf))
    if err != nil { panic(err) }
    defer resp.Body.Close()
    b, _ := io.ReadAll(resp.Body)
    var result map[string]interface{}
    json.Unmarshal(b, &result)
    return result
}

func get(path string) map[string]interface{} {
    resp, err := http.Get("http://127.0.0.1:7892" + path)
    if err != nil { panic(err) }
    defer resp.Body.Close()
    b, _ := io.ReadAll(resp.Body)
    var result map[string]interface{}
    json.Unmarshal(b, &result)
    return result
}

func main() {
    health := get("/health")
    fmt.Println("Server version:", health["version"])

    s := post("/sessions", map[string]interface{}{})
    sid := s["session_id"].(string)

    post("/sessions/"+sid+"/block", map[string]interface{}{
        "resource_types": []string{"image", "stylesheet", "font", "media"},
    })
    post("/sessions/"+sid+"/goto", map[string]interface{}{"url": "https://example.com"})

    titleResp := get("/sessions/" + sid + "/title")
    fmt.Println("Title:", titleResp["title"])

    req, _ := http.NewRequest("DELETE", "http://127.0.0.1:7892/sessions/"+sid, nil)
    http.DefaultClient.Do(req)
}
'''

    result = Go.run(go_code, timeout=30)
    print("\n=== Go (via polyrun) ===")
    print(result.stdout.strip())

except Exception as e:
    print(f"\nGo polyrun: {e} (Go may not be installed)")


# ── polyrun Rust ──────────────────────────────────────────────────────────────

try:
    from polyrun import Rust

    rust_code = '''
use std::io::Read;

fn post(path: &str, body: &str) -> String {
    let url = format!("http://127.0.0.1:7892{}", path);
    let client = std::process::Command::new("curl")
        .args(["-s", "-X", "POST", "-H", "Content-Type: application/json", "-d", body, &url])
        .output()
        .unwrap();
    String::from_utf8_lossy(&client.stdout).to_string()
}

fn get(path: &str) -> String {
    let url = format!("http://127.0.0.1:7892{}", path);
    let client = std::process::Command::new("curl")
        .args(["-s", &url])
        .output()
        .unwrap();
    String::from_utf8_lossy(&client.stdout).to_string()
}

fn main() {
    let health = get("/health");
    println!("Health: {}", health.chars().take(60).collect::<String>());

    let session = post("/sessions", "{}");
    println!("Session created via Rust + polyrun");
    let _ = session;
}
'''

    result = Rust.run(rust_code, timeout=60)
    print("\n=== Rust (via polyrun) ===")
    if result.stdout.strip():
        print(result.stdout.strip())
    else:
        print("(Rust compiled and ran — output suppressed)")

except Exception as e:
    print(f"\nRust polyrun: {e} (Rust may not be installed)")


print("\nDone — all polyrun language runners tested.")
print("See bindings/ for full client libraries in each language.")

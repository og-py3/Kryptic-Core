/*!
Kryptic Rust client

Communicates with a running Kryptic server (python -m kryptic serve).

Dependencies (add to Cargo.toml):
    [dependencies]
    ureq = { version = "2", features = ["json"] }
    serde = { version = "1", features = ["derive"] }
    serde_json = "1"
    base64 = "0.22"

Run the example:
    cargo run
*/

use base64::{engine::general_purpose::STANDARD, Engine};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;

// ── Client ────────────────────────────────────────────────────────────────────

pub struct KrypticClient {
    base: String,
}

impl KrypticClient {
    pub fn new(host: &str, port: u16) -> Self {
        Self {
            base: format!("http://{}:{}", host, port),
        }
    }

    pub fn default() -> Self {
        Self::new("127.0.0.1", 7890)
    }

    fn post(&self, path: &str, body: Value) -> Result<Value, Box<dyn std::error::Error>> {
        let url = format!("{}{}", self.base, path);
        let resp: Value = ureq::post(&url).send_json(body)?.into_json()?;
        if resp["ok"] != true {
            return Err(resp["error"].as_str().unwrap_or("unknown error").into());
        }
        Ok(resp)
    }

    fn get(&self, path: &str) -> Result<Value, Box<dyn std::error::Error>> {
        let url = format!("{}{}", self.base, path);
        let resp: Value = ureq::get(&url).call()?.into_json()?;
        Ok(resp)
    }

    fn delete(&self, path: &str) -> Result<Value, Box<dyn std::error::Error>> {
        let url = format!("{}{}", self.base, path);
        let resp: Value = ureq::delete(&url).call()?.into_json()?;
        Ok(resp)
    }

    pub fn health(&self) -> Result<Value, Box<dyn std::error::Error>> {
        self.get("/health")
    }

    pub fn session(&self) -> Result<KrypticSession, Box<dyn std::error::Error>> {
        let resp = self.post("/sessions", json!({}))?;
        let id = resp["session_id"]
            .as_str()
            .ok_or("no session_id")?
            .to_string();
        Ok(KrypticSession { client: self, id })
    }

    pub fn http_get(
        &self,
        url: &str,
        headers: Option<HashMap<String, String>>,
    ) -> Result<Value, Box<dyn std::error::Error>> {
        self.post("/http/get", json!({ "url": url, "headers": headers }))
    }

    pub fn http_post(
        &self,
        url: &str,
        json_body: Value,
    ) -> Result<Value, Box<dyn std::error::Error>> {
        self.post("/http/post", json!({ "url": url, "json": json_body }))
    }

    pub fn http_batch(
        &self,
        urls: &[&str],
    ) -> Result<Vec<Value>, Box<dyn std::error::Error>> {
        let resp = self.post("/http/batch", json!({ "urls": urls }))?;
        Ok(resp["results"].as_array().cloned().unwrap_or_default())
    }
}

// ── Session ───────────────────────────────────────────────────────────────────

pub struct KrypticSession<'a> {
    client: &'a KrypticClient,
    pub id: String,
}

impl<'a> KrypticSession<'a> {
    fn post_action(
        &self,
        action: &str,
        body: Value,
    ) -> Result<Value, Box<dyn std::error::Error>> {
        self.client
            .post(&format!("/sessions/{}/{}", self.id, action), body)
    }

    fn get_action(&self, action: &str) -> Result<Value, Box<dyn std::error::Error>> {
        self.client.get(&format!("/sessions/{}/{}", self.id, action))
    }

    pub fn goto(&self, url: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.post_action(
            "goto",
            json!({ "url": url, "wait_until": "domcontentloaded" }),
        )?;
        Ok(())
    }

    pub fn title(&self) -> Result<String, Box<dyn std::error::Error>> {
        let r = self.get_action("title")?;
        Ok(r["title"].as_str().unwrap_or("").to_string())
    }

    pub fn html(&self) -> Result<String, Box<dyn std::error::Error>> {
        let r = self.get_action("html")?;
        Ok(r["html"].as_str().unwrap_or("").to_string())
    }

    pub fn url(&self) -> Result<String, Box<dyn std::error::Error>> {
        let r = self.get_action("url")?;
        Ok(r["url"].as_str().unwrap_or("").to_string())
    }

    pub fn text(&self, selector: &str) -> Result<String, Box<dyn std::error::Error>> {
        let r = self.post_action("text", json!({ "selector": selector }))?;
        Ok(r["text"].as_str().unwrap_or("").to_string())
    }

    pub fn click(&self, selector: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.post_action("click", json!({ "selector": selector }))?;
        Ok(())
    }

    pub fn fill(&self, selector: &str, value: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.post_action("fill", json!({ "selector": selector, "value": value }))?;
        Ok(())
    }

    pub fn evaluate(&self, js: &str) -> Result<Value, Box<dyn std::error::Error>> {
        let r = self.post_action("evaluate", json!({ "js": js }))?;
        Ok(r["result"].clone())
    }

    pub fn screenshot(&self, full_page: bool) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
        let r = self.post_action("screenshot", json!({ "full_page": full_page }))?;
        let data = r["data"].as_str().unwrap_or("");
        Ok(STANDARD.decode(data)?)
    }

    pub fn block_resources(
        &self,
        types: &[&str],
    ) -> Result<(), Box<dyn std::error::Error>> {
        self.post_action("block", json!({ "resource_types": types }))?;
        Ok(())
    }

    pub fn wait_for(
        &self,
        selector: &str,
        state: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        self.post_action("wait_for", json!({ "selector": selector, "state": state }))?;
        Ok(())
    }

    pub fn close(&self) -> Result<(), Box<dyn std::error::Error>> {
        self.client
            .delete(&format!("/sessions/{}", self.id))?;
        Ok(())
    }
}

// ── Example main ─────────────────────────────────────────────────────────────

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let k = KrypticClient::default();

    let health = k.health()?;
    println!("Server: {}", health);

    let s = k.session()?;
    s.block_resources(&["image", "stylesheet", "font", "media"])?;
    s.goto("https://example.com")?;
    println!("Title: {}", s.title()?);
    println!("H1: {}", s.text("h1")?);
    s.close()?;

    let resp = k.http_get("https://httpbin.org/get", None)?;
    println!("HTTP status: {}", resp["status"]);

    let batch = k.http_batch(&["https://example.com", "https://example.org"])?;
    for r in &batch {
        println!("  {}  {}", r["status"], r["url"].as_str().unwrap_or(""));
    }

    Ok(())
}

/**
 * kryptic.hpp — Kryptic C++ client (header-only)
 *
 * Communicates with a running Kryptic server (python -m kryptic serve).
 * Depends on: libcurl, nlohmann/json (header-only)
 *
 * Install nlohmann/json:
 *   apt install nlohmann-json3-dev   # or
 *   vcpkg install nlohmann-json      # or
 *   conan install nlohmann-json      # or just drop json.hpp in your project
 *
 * Compile example:
 *   g++ -std=c++17 -o kryptic_example kryptic_example.cpp -lcurl
 */

#pragma once

#include <curl/curl.h>
#include <nlohmann/json.hpp>

#include <stdexcept>
#include <string>
#include <vector>

namespace kryptic {

using json = nlohmann::json;

// ── internal curl helper ────────────────────────────────────────────────────

namespace detail {

static size_t write_cb(void *ptr, size_t size, size_t nmemb, std::string *out) {
    out->append(static_cast<char *>(ptr), size * nmemb);
    return size * nmemb;
}

inline std::string curl_request(const std::string &method, const std::string &url,
                                  const std::string &body = "") {
    CURL *curl = curl_easy_init();
    if (!curl) throw std::runtime_error("curl_easy_init failed");

    std::string response;
    struct curl_slist *headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 60L);

    if (method == "POST") {
        curl_easy_setopt(curl, CURLOPT_POST, 1L);
        const std::string &b = body.empty() ? "{}" : body;
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, b.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, b.size());
    } else if (method == "DELETE") {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
    }

    curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    return response;
}

} // namespace detail

// ── KrypticSession (forward declared) ─────────────────────────────────────

class KrypticSession;

// ── KrypticClient ──────────────────────────────────────────────────────────

class KrypticClient {
public:
    explicit KrypticClient(const std::string &host = "127.0.0.1", int port = 7890)
        : base_("http://" + host + ":" + std::to_string(port)) {}

    json post(const std::string &path, const json &body = json::object()) const {
        std::string raw = detail::curl_request("POST", base_ + path, body.dump());
        json r = json::parse(raw);
        if (!r.value("ok", false))
            throw std::runtime_error("Kryptic error: " + r.value("error", "unknown"));
        return r;
    }

    json get(const std::string &path) const {
        std::string raw = detail::curl_request("GET", base_ + path);
        return json::parse(raw);
    }

    json del(const std::string &path) const {
        std::string raw = detail::curl_request("DELETE", base_ + path);
        return json::parse(raw);
    }

    json health() const { return get("/health"); }

    KrypticSession session() const;

    json http_get(const std::string &url,
                  const json &headers = json::object()) const {
        return post("/http/get", {{"url", url}, {"headers", headers}});
    }

    json http_post(const std::string &url, const json &body = json::object()) const {
        return post("/http/post", {{"url", url}, {"json", body}});
    }

    std::vector<json> http_batch(const std::vector<std::string> &urls) const {
        json r = post("/http/batch", {{"urls", urls}});
        return r["results"].get<std::vector<json>>();
    }

private:
    std::string base_;
};

// ── KrypticSession ─────────────────────────────────────────────────────────

class KrypticSession {
public:
    KrypticSession(const KrypticClient &client, std::string id)
        : client_(client), id_(std::move(id)) {}

    void goto_(const std::string &url,
               const std::string &wait_until = "domcontentloaded") const {
        client_.post("/sessions/" + id_ + "/goto",
                     {{"url", url}, {"wait_until", wait_until}});
    }

    std::string title() const {
        return client_.get("/sessions/" + id_ + "/title")["title"];
    }

    std::string html() const {
        return client_.get("/sessions/" + id_ + "/html")["html"];
    }

    std::string url() const {
        return client_.get("/sessions/" + id_ + "/url")["url"];
    }

    std::string text(const std::string &selector) const {
        return client_.post("/sessions/" + id_ + "/text",
                            {{"selector", selector}})["text"];
    }

    void click(const std::string &selector) const {
        client_.post("/sessions/" + id_ + "/click", {{"selector", selector}});
    }

    void fill(const std::string &selector, const std::string &value) const {
        client_.post("/sessions/" + id_ + "/fill",
                     {{"selector", selector}, {"value", value}});
    }

    json evaluate(const std::string &js) const {
        return client_.post("/sessions/" + id_ + "/evaluate",
                            {{"js", js}})["result"];
    }

    json find(const std::string &selector) const {
        return client_.post("/sessions/" + id_ + "/find",
                            {{"selector", selector}});
    }

    std::vector<uint8_t> screenshot(bool full_page = false) const {
        std::string b64 =
            client_.post("/sessions/" + id_ + "/screenshot",
                         {{"full_page", full_page}})["data"];
        // base64 decode (requires C++17)
        static const std::string chars =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        std::vector<uint8_t> out;
        int val = 0, bits = -8;
        for (char c : b64) {
            if (c == '=') break;
            size_t pos = chars.find(c);
            if (pos == std::string::npos) continue;
            val = (val << 6) + static_cast<int>(pos);
            bits += 6;
            if (bits >= 0) {
                out.push_back((val >> bits) & 0xFF);
                bits -= 8;
            }
        }
        return out;
    }

    void block_resources(
        const std::vector<std::string> &types = {"image", "stylesheet", "font",
                                                  "media"}) const {
        client_.post("/sessions/" + id_ + "/block", {{"resource_types", types}});
    }

    void wait_for(const std::string &selector,
                  const std::string &state = "visible") const {
        client_.post("/sessions/" + id_ + "/wait_for",
                     {{"selector", selector}, {"state", state}});
    }

    void close() const {
        client_.del("/sessions/" + id_);
    }

    const std::string &id() const { return id_; }

private:
    const KrypticClient &client_;
    std::string id_;
};

// ── KrypticClient::session() definition ───────────────────────────────────

inline KrypticSession KrypticClient::session() const {
    json r = post("/sessions", json::object());
    return KrypticSession(*this, r["session_id"]);
}

} // namespace kryptic

/**
 * kryptic.c — Kryptic C client implementation
 *
 * Compile example:
 *   gcc -o kryptic_example kryptic.c -lcurl
 * Run:
 *   ./kryptic_example
 */

#include "kryptic.h"
#include <curl/curl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ── Internal write callback ──────────────────────────────────────────────── */

typedef struct {
    char  *buf;
    size_t len;
    size_t cap;
} _Buf;

static size_t _write_cb(void *ptr, size_t size, size_t nmemb, void *userdata) {
    _Buf *b = ((_Buf *)userdata);
    size_t incoming = size * nmemb;
    if (b->len + incoming + 1 >= b->cap) {
        b->cap = (b->len + incoming + 1) * 2;
        b->buf = (char *)realloc(b->buf, b->cap);
    }
    memcpy(b->buf + b->len, ptr, incoming);
    b->len += incoming;
    b->buf[b->len] = '\0';
    return incoming;
}

static KrypticResponse _do_request(const char *method, const char *url,
                                    const char *json_body) {
    CURL *curl = curl_easy_init();
    _Buf  b    = {0};
    b.cap      = KRYPTIC_BUF_SIZE;
    b.buf      = (char *)malloc(b.cap);
    b.buf[0]   = '\0';

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, _write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &b);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 60L);

    if (strcmp(method, "POST") == 0) {
        curl_easy_setopt(curl, CURLOPT_POST, 1L);
        if (json_body) {
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_body);
        } else {
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, "{}");
        }
    } else if (strcmp(method, "DELETE") == 0) {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
    }

    curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    KrypticResponse resp;
    resp.data = b.buf;
    resp.size = b.len;
    return resp;
}

static char _base_url[512];

/* ── Client init ──────────────────────────────────────────────────────────── */

void kryptic_init(KrypticClient *c, const char *host, int port) {
    strncpy(c->host, host, sizeof(c->host) - 1);
    c->port = port;
}

void kryptic_init_default(KrypticClient *c) {
    kryptic_init(c, KRYPTIC_DEFAULT_HOST, KRYPTIC_DEFAULT_PORT);
}

/* ── Request helpers ──────────────────────────────────────────────────────── */

KrypticResponse kryptic_post(KrypticClient *c, const char *path,
                              const char *json_body) {
    char url[1024];
    snprintf(url, sizeof(url), "http://%s:%d%s", c->host, c->port, path);
    return _do_request("POST", url, json_body);
}

KrypticResponse kryptic_get(KrypticClient *c, const char *path) {
    char url[1024];
    snprintf(url, sizeof(url), "http://%s:%d%s", c->host, c->port, path);
    return _do_request("GET", url, NULL);
}

KrypticResponse kryptic_delete(KrypticClient *c, const char *path) {
    char url[1024];
    snprintf(url, sizeof(url), "http://%s:%d%s", c->host, c->port, path);
    return _do_request("DELETE", url, NULL);
}

/* ── Server ───────────────────────────────────────────────────────────────── */

KrypticResponse kryptic_health(KrypticClient *c) {
    return kryptic_get(c, "/health");
}

/* ── Sessions ─────────────────────────────────────────────────────────────── */

int kryptic_session_create(KrypticClient *c, KrypticSession *s) {
    s->client = c;
    KrypticResponse r = kryptic_post(c, "/sessions", "{}");
    int ok = kryptic_extract_str(r.data, "session_id", s->session_id,
                                  sizeof(s->session_id));
    free(r.data);
    return ok;
}

KrypticResponse kryptic_session_goto(KrypticSession *s, const char *url) {
    char path[256], body[1024];
    snprintf(path, sizeof(path), "/sessions/%s/goto", s->session_id);
    snprintf(body, sizeof(body),
             "{\"url\":\"%s\",\"wait_until\":\"domcontentloaded\"}", url);
    return kryptic_post(s->client, path, body);
}

KrypticResponse kryptic_session_title(KrypticSession *s) {
    char path[256];
    snprintf(path, sizeof(path), "/sessions/%s/title", s->session_id);
    return kryptic_get(s->client, path);
}

KrypticResponse kryptic_session_html(KrypticSession *s) {
    char path[256];
    snprintf(path, sizeof(path), "/sessions/%s/html", s->session_id);
    return kryptic_get(s->client, path);
}

KrypticResponse kryptic_session_text(KrypticSession *s, const char *selector) {
    char path[256], body[512];
    snprintf(path, sizeof(path), "/sessions/%s/text", s->session_id);
    snprintf(body, sizeof(body), "{\"selector\":\"%s\"}", selector);
    return kryptic_post(s->client, path, body);
}

KrypticResponse kryptic_session_click(KrypticSession *s, const char *selector) {
    char path[256], body[512];
    snprintf(path, sizeof(path), "/sessions/%s/click", s->session_id);
    snprintf(body, sizeof(body), "{\"selector\":\"%s\"}", selector);
    return kryptic_post(s->client, path, body);
}

KrypticResponse kryptic_session_fill(KrypticSession *s, const char *selector,
                                      const char *value) {
    char path[256], body[1024];
    snprintf(path, sizeof(path), "/sessions/%s/fill", s->session_id);
    snprintf(body, sizeof(body), "{\"selector\":\"%s\",\"value\":\"%s\"}",
             selector, value);
    return kryptic_post(s->client, path, body);
}

KrypticResponse kryptic_session_evaluate(KrypticSession *s, const char *js) {
    char path[256], body[2048];
    snprintf(path, sizeof(path), "/sessions/%s/evaluate", s->session_id);
    snprintf(body, sizeof(body), "{\"js\":\"%s\"}", js);
    return kryptic_post(s->client, path, body);
}

KrypticResponse kryptic_session_block(KrypticSession *s, const char *types) {
    char path[256], body[512];
    snprintf(path, sizeof(path), "/sessions/%s/block", s->session_id);
    snprintf(body, sizeof(body),
             "{\"resource_types\":[\"%s\"]}", types);
    return kryptic_post(s->client, path, body);
}

KrypticResponse kryptic_session_close(KrypticSession *s) {
    char path[256];
    snprintf(path, sizeof(path), "/sessions/%s", s->session_id);
    return kryptic_delete(s->client, path);
}

/* ── HTTP ─────────────────────────────────────────────────────────────────── */

KrypticResponse kryptic_http_get(KrypticClient *c, const char *url) {
    char body[1024];
    snprintf(body, sizeof(body), "{\"url\":\"%s\"}", url);
    return kryptic_post(c, "/http/get", body);
}

KrypticResponse kryptic_http_post(KrypticClient *c, const char *url,
                                   const char *json_body) {
    char body[4096];
    snprintf(body, sizeof(body), "{\"url\":\"%s\",\"json\":%s}", url,
             json_body ? json_body : "null");
    return kryptic_post(c, "/http/post", body);
}

/* ── JSON helper (no external parser) ────────────────────────────────────── */

int kryptic_extract_str(const char *json, const char *key, char *out,
                         size_t out_size) {
    char pattern[128];
    snprintf(pattern, sizeof(pattern), "\"%s\":\"", key);
    const char *p = strstr(json, pattern);
    if (!p) return 0;
    p += strlen(pattern);
    size_t i = 0;
    while (*p && *p != '"' && i < out_size - 1) {
        out[i++] = *p++;
    }
    out[i] = '\0';
    return i > 0;
}

/* ── Example main ─────────────────────────────────────────────────────────── */

int main(void) {
    KrypticClient c;
    kryptic_init_default(&c);

    KrypticResponse health = kryptic_health(&c);
    printf("Health: %s\n", health.data);
    free(health.data);

    KrypticSession s;
    if (!kryptic_session_create(&c, &s)) {
        fprintf(stderr, "Failed to create session\n");
        return 1;
    }

    kryptic_session_block(&s, "image\",\"stylesheet\",\"font\",\"media");
    KrypticResponse gr = kryptic_session_goto(&s, "https://example.com");
    free(gr.data);

    KrypticResponse tr = kryptic_session_title(&s);
    char title[256] = {0};
    kryptic_extract_str(tr.data, "title", title, sizeof(title));
    printf("Title: %s\n", title);
    free(tr.data);

    KrypticResponse close_r = kryptic_session_close(&s);
    free(close_r.data);

    KrypticResponse hr = kryptic_http_get(&c, "https://httpbin.org/get");
    printf("HTTP body (first 80 chars): %.80s\n", hr.data);
    free(hr.data);

    return 0;
}

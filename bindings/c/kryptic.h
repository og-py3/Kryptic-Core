/**
 * kryptic.h — Kryptic C client header
 *
 * Communicates with a running Kryptic server (python -m kryptic serve).
 * Depends on: libcurl
 *
 * Compile example:
 *   gcc -o kryptic_example kryptic.c -lcurl
 */

#ifndef KRYPTIC_H
#define KRYPTIC_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>

#define KRYPTIC_DEFAULT_HOST "127.0.0.1"
#define KRYPTIC_DEFAULT_PORT 7890
#define KRYPTIC_BUF_SIZE     (1024 * 1024)  /* 1 MiB response buffer */

typedef struct {
    char *data;
    size_t size;
} KrypticResponse;

typedef struct {
    char host[256];
    int  port;
} KrypticClient;

typedef struct {
    KrypticClient *client;
    char session_id[64];
} KrypticSession;

/* ── Client lifecycle ──────────────────────────────────────────────────────── */

/** Initialise a client pointing at host:port. */
void kryptic_init(KrypticClient *c, const char *host, int port);

/** Initialise a client pointing at 127.0.0.1:7890. */
void kryptic_init_default(KrypticClient *c);

/* ── Low-level request helpers ─────────────────────────────────────────────── */

/** POST JSON body to path. Caller must free(resp.data). */
KrypticResponse kryptic_post(KrypticClient *c, const char *path, const char *json_body);

/** GET path. Caller must free(resp.data). */
KrypticResponse kryptic_get(KrypticClient *c, const char *path);

/** DELETE path. Caller must free(resp.data). */
KrypticResponse kryptic_delete(KrypticClient *c, const char *path);

/* ── Server ────────────────────────────────────────────────────────────────── */
KrypticResponse kryptic_health(KrypticClient *c);

/* ── Sessions ──────────────────────────────────────────────────────────────── */

/** Create a browser session. Returns 1 on success, 0 on failure. */
int kryptic_session_create(KrypticClient *c, KrypticSession *s);

/** Navigate session to url. */
KrypticResponse kryptic_session_goto(KrypticSession *s, const char *url);

/** Get page title. Caller must free(resp.data). */
KrypticResponse kryptic_session_title(KrypticSession *s);

/** Get page HTML. Caller must free(resp.data). */
KrypticResponse kryptic_session_html(KrypticSession *s);

/** Get inner text of selector. Caller must free(resp.data). */
KrypticResponse kryptic_session_text(KrypticSession *s, const char *selector);

/** Click a selector. */
KrypticResponse kryptic_session_click(KrypticSession *s, const char *selector);

/** Fill an input. */
KrypticResponse kryptic_session_fill(KrypticSession *s, const char *selector, const char *value);

/** Run JavaScript. Caller must free(resp.data). */
KrypticResponse kryptic_session_evaluate(KrypticSession *s, const char *js);

/** Block resource types (pass comma-separated: "image,stylesheet,font,media"). */
KrypticResponse kryptic_session_block(KrypticSession *s, const char *types);

/** Close and destroy the session. */
KrypticResponse kryptic_session_close(KrypticSession *s);

/* ── HTTP ──────────────────────────────────────────────────────────────────── */

/** Perform an HTTP GET. Caller must free(resp.data). */
KrypticResponse kryptic_http_get(KrypticClient *c, const char *url);

/** Perform an HTTP POST with a JSON body. Caller must free(resp.data). */
KrypticResponse kryptic_http_post(KrypticClient *c, const char *url, const char *json_body);

/* ── Helpers ───────────────────────────────────────────────────────────────── */

/** Extract a string value from a minimal JSON response (no external parser needed). */
int kryptic_extract_str(const char *json, const char *key, char *out, size_t out_size);

#ifdef __cplusplus
}
#endif

#endif /* KRYPTIC_H */

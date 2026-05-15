import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Kryptic Java client.
 *
 * Communicates with a running Kryptic server (python -m kryptic serve).
 * Requires Java 11+ (uses java.net.http.HttpClient — zero extra dependencies).
 *
 * Compile: javac Kryptic.java
 * Run:     java Kryptic
 */
public class Kryptic {

    private final String base;
    private final HttpClient http;

    public Kryptic(String host, int port) {
        this.base = "http://" + host + ":" + port;
        this.http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    }

    public Kryptic() {
        this("127.0.0.1", 7890);
    }

    // ── Low-level HTTP helpers ─────────────────────────────────────────────────

    private String post(String path, String jsonBody) throws Exception {
        HttpRequest req = HttpRequest.newBuilder()
            .uri(URI.create(base + path))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(jsonBody, StandardCharsets.UTF_8))
            .build();
        HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
        if (resp.statusCode() >= 400) {
            throw new RuntimeException("Kryptic error " + resp.statusCode() + ": " + resp.body());
        }
        return resp.body();
    }

    private String get(String path) throws Exception {
        HttpRequest req = HttpRequest.newBuilder()
            .uri(URI.create(base + path))
            .GET()
            .build();
        HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
        return resp.body();
    }

    private String delete(String path) throws Exception {
        HttpRequest req = HttpRequest.newBuilder()
            .uri(URI.create(base + path))
            .DELETE()
            .build();
        HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
        return resp.body();
    }

    private String extract(String json, String key) {
        Pattern p = Pattern.compile("\"" + key + "\"\\s*:\\s*\"([^\"]+)\"");
        Matcher m = p.matcher(json);
        return m.find() ? m.group(1) : "";
    }

    // ── Public API ─────────────────────────────────────────────────────────────

    public String health() throws Exception {
        return get("/health");
    }

    public Session session() throws Exception {
        String resp = post("/sessions", "{}");
        String sid = extract(resp, "session_id");
        if (sid.isEmpty()) throw new RuntimeException("No session_id in response: " + resp);
        return new Session(sid);
    }

    public String httpGet(String url) throws Exception {
        return post("/http/get", "{\"url\":\"" + url + "\"}");
    }

    public String httpPost(String url, String jsonBody) throws Exception {
        String body = String.format("{\"url\":\"%s\",\"json\":%s}", url, jsonBody);
        return post("/http/post", body);
    }

    // ── Session ────────────────────────────────────────────────────────────────

    public class Session {
        private final String id;

        Session(String id) {
            this.id = id;
        }

        public String goto_(String url) throws Exception {
            return post("/sessions/" + id + "/goto",
                "{\"url\":\"" + url + "\",\"wait_until\":\"domcontentloaded\"}");
        }

        public String title() throws Exception {
            String resp = get("/sessions/" + id + "/title");
            return extract(resp, "title");
        }

        public String html() throws Exception {
            String resp = get("/sessions/" + id + "/html");
            return extract(resp, "html");
        }

        public String currentUrl() throws Exception {
            String resp = get("/sessions/" + id + "/url");
            return extract(resp, "url");
        }

        public String text(String selector) throws Exception {
            String body = "{\"selector\":\"" + selector + "\"}";
            String resp = post("/sessions/" + id + "/text", body);
            return extract(resp, "text");
        }

        public void click(String selector) throws Exception {
            post("/sessions/" + id + "/click", "{\"selector\":\"" + selector + "\"}");
        }

        public void fill(String selector, String value) throws Exception {
            String body = String.format("{\"selector\":\"%s\",\"value\":\"%s\"}", selector, value);
            post("/sessions/" + id + "/fill", body);
        }

        public String evaluate(String js) throws Exception {
            String body = "{\"js\":\"" + js.replace("\"", "\\\"") + "\"}";
            String resp = post("/sessions/" + id + "/evaluate", body);
            return extract(resp, "result");
        }

        public byte[] screenshot() throws Exception {
            String resp = post("/sessions/" + id + "/screenshot", "{}");
            String data = extract(resp, "data");
            return Base64.getDecoder().decode(data);
        }

        public void blockResources() throws Exception {
            post("/sessions/" + id + "/block",
                "{\"resource_types\":[\"image\",\"stylesheet\",\"font\",\"media\"]}");
        }

        public void close() throws Exception {
            delete("/sessions/" + id);
        }
    }

    // ── Example main ───────────────────────────────────────────────────────────

    public static void main(String[] args) throws Exception {
        Kryptic k = new Kryptic();
        System.out.println("Health: " + k.health());

        Session s = k.session();
        s.blockResources();
        s.goto_("https://example.com");
        System.out.println("Title: " + s.title());
        System.out.println("H1: " + s.text("h1"));
        s.close();

        String httpResp = k.httpGet("https://httpbin.org/get");
        System.out.println("HTTP GET status line: " + httpResp.substring(0, 80));
    }
}

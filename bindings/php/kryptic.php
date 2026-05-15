<?php
/**
 * Kryptic PHP Client
 *
 * Communicates with a running Kryptic server (python -m kryptic serve).
 * Zero external dependencies — uses PHP's built-in cURL extension.
 *
 * Requirements: PHP 7.4+, ext-curl, ext-json
 *
 * Usage:
 *   $k = new KrypticClient();
 *   $session = $k->session();
 *   $session->goto('https://example.com');
 *   echo $session->title();
 *   $session->close();
 */

class KrypticException extends RuntimeException {}

class KrypticClient
{
    private string $base;

    public function __construct(string $host = '127.0.0.1', int $port = 7890)
    {
        $this->base = "http://{$host}:{$port}";
    }

    // ── Low-level request helpers ────────────────────────────────────────────

    public function request(string $method, string $path, array $body = []): array
    {
        $url = $this->base . $path;
        $ch  = curl_init($url);

        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 60);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);

        $json = empty($body) ? '{}' : json_encode($body);

        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $json);
        } elseif ($method === 'DELETE') {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'DELETE');
        }

        $raw  = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($raw === false) {
            throw new KrypticException('cURL request failed — is the server running?');
        }

        $data = json_decode($raw, true);
        if (!isset($data['ok']) || !$data['ok']) {
            throw new KrypticException($data['error'] ?? 'Unknown Kryptic error');
        }

        return $data;
    }

    public function get(string $path): array
    {
        $url = $this->base . $path;
        $ch  = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        $raw = curl_exec($ch);
        curl_close($ch);
        return json_decode($raw, true) ?? [];
    }

    // ── API ──────────────────────────────────────────────────────────────────

    public function health(): array
    {
        return $this->get('/health');
    }

    public function session(): KrypticSession
    {
        $data = $this->request('POST', '/sessions');
        return new KrypticSession($this, $data['session_id']);
    }

    public function httpGet(string $url, array $headers = []): array
    {
        return $this->request('POST', '/http/get', ['url' => $url, 'headers' => $headers]);
    }

    public function httpPost(string $url, array $json = [], array $headers = []): array
    {
        return $this->request('POST', '/http/post', [
            'url'     => $url,
            'json'    => $json,
            'headers' => $headers,
        ]);
    }

    public function httpBatch(array $urls): array
    {
        $data = $this->request('POST', '/http/batch', ['urls' => $urls]);
        return $data['results'] ?? [];
    }
}

class KrypticSession
{
    private KrypticClient $client;
    public string $id;

    public function __construct(KrypticClient $client, string $id)
    {
        $this->client = $client;
        $this->id     = $id;
    }

    private function post(string $action, array $body = []): array
    {
        return $this->client->request('POST', "/sessions/{$this->id}/{$action}", $body);
    }

    private function get(string $action): array
    {
        return $this->client->get("/sessions/{$this->id}/{$action}");
    }

    public function goto(string $url, string $waitUntil = 'domcontentloaded'): array
    {
        return $this->post('goto', ['url' => $url, 'wait_until' => $waitUntil]);
    }

    public function title(): string
    {
        return $this->get('title')['title'] ?? '';
    }

    public function html(): string
    {
        return $this->get('html')['html'] ?? '';
    }

    public function url(): string
    {
        return $this->get('url')['url'] ?? '';
    }

    public function text(string $selector): string
    {
        return $this->post('text', ['selector' => $selector])['text'] ?? '';
    }

    public function click(string $selector): void
    {
        $this->post('click', ['selector' => $selector]);
    }

    public function fill(string $selector, string $value): void
    {
        $this->post('fill', ['selector' => $selector, 'value' => $value]);
    }

    public function evaluate(string $js): mixed
    {
        return $this->post('evaluate', ['js' => $js])['result'] ?? null;
    }

    public function find(string $selector): array
    {
        return $this->post('find', ['selector' => $selector]);
    }

    /**
     * Take a screenshot and return raw PNG bytes.
     */
    public function screenshot(bool $fullPage = false): string
    {
        $data = $this->post('screenshot', ['full_page' => $fullPage]);
        return base64_decode($data['data'] ?? '');
    }

    public function blockResources(array $types = ['image', 'stylesheet', 'font', 'media']): void
    {
        $this->post('block', ['resource_types' => $types]);
    }

    public function waitFor(string $selector, string $state = 'visible'): void
    {
        $this->post('wait_for', ['selector' => $selector, 'state' => $state]);
    }

    public function close(): void
    {
        $this->client->request('DELETE', "/sessions/{$this->id}");
    }
}

// ── Example ──────────────────────────────────────────────────────────────────

if (basename(__FILE__) === basename($_SERVER['SCRIPT_FILENAME'] ?? '')) {
    $k = new KrypticClient();

    $health = $k->health();
    echo "Server: " . json_encode($health) . "\n";

    $s = $k->session();
    $s->blockResources();
    $s->goto('https://example.com');
    echo "Title: " . $s->title() . "\n";
    echo "H1:    " . $s->text('h1') . "\n";
    $s->close();

    $resp = $k->httpGet('https://httpbin.org/get');
    echo "HTTP status: " . ($resp['status'] ?? '?') . "\n";

    $batch = $k->httpBatch(['https://example.com', 'https://example.org']);
    foreach ($batch as $r) {
        echo "  {$r['status']}  {$r['url']}\n";
    }
}

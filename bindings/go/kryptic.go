// Kryptic Go client
//
// Communicates with a running Kryptic server (python -m kryptic serve).
// Zero external dependencies — uses only the standard library.
//
// Run the example:
//   go run kryptic.go
package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// ── client ─────────────────────────────────────────────────────────────────

type KrypticClient struct {
	Base   string
	client *http.Client
}

func NewKrypticClient(host string, port int) *KrypticClient {
	return &KrypticClient{
		Base: fmt.Sprintf("http://%s:%d", host, port),
		client: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

func New() *KrypticClient {
	return NewKrypticClient("127.0.0.1", 7890)
}

func (k *KrypticClient) request(method, path string, body any) (map[string]any, error) {
	var reqBody io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reqBody = bytes.NewReader(b)
	}

	req, err := http.NewRequest(method, k.Base+path, reqBody)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := k.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	if ok, _ := result["ok"].(bool); !ok {
		errMsg, _ := result["error"].(string)
		return nil, fmt.Errorf("kryptic error: %s", errMsg)
	}
	return result, nil
}

func (k *KrypticClient) Health() (map[string]any, error) {
	return k.request("GET", "/health", nil)
}

func (k *KrypticClient) Session() (*KrypticSession, error) {
	r, err := k.request("POST", "/sessions", map[string]any{})
	if err != nil {
		return nil, err
	}
	id, _ := r["session_id"].(string)
	return &KrypticSession{client: k, ID: id}, nil
}

func (k *KrypticClient) HTTPGet(url string, headers map[string]string) (map[string]any, error) {
	return k.request("POST", "/http/get", map[string]any{"url": url, "headers": headers})
}

func (k *KrypticClient) HTTPPost(url string, jsonBody any) (map[string]any, error) {
	return k.request("POST", "/http/post", map[string]any{"url": url, "json": jsonBody})
}

func (k *KrypticClient) HTTPBatch(urls []string) ([]any, error) {
	r, err := k.request("POST", "/http/batch", map[string]any{"urls": urls})
	if err != nil {
		return nil, err
	}
	results, _ := r["results"].([]any)
	return results, nil
}

// ── session ─────────────────────────────────────────────────────────────────

type KrypticSession struct {
	client *KrypticClient
	ID     string
}

func (s *KrypticSession) post(action string, body any) (map[string]any, error) {
	return s.client.request("POST", "/sessions/"+s.ID+"/"+action, body)
}

func (s *KrypticSession) get(action string) (map[string]any, error) {
	return s.client.request("GET", "/sessions/"+s.ID+"/"+action, nil)
}

func (s *KrypticSession) Goto(url string) error {
	_, err := s.post("goto", map[string]any{"url": url, "wait_until": "domcontentloaded"})
	return err
}

func (s *KrypticSession) Title() (string, error) {
	r, err := s.get("title")
	if err != nil {
		return "", err
	}
	return r["title"].(string), nil
}

func (s *KrypticSession) HTML() (string, error) {
	r, err := s.get("html")
	if err != nil {
		return "", err
	}
	return r["html"].(string), nil
}

func (s *KrypticSession) URL() (string, error) {
	r, err := s.get("url")
	if err != nil {
		return "", err
	}
	return r["url"].(string), nil
}

func (s *KrypticSession) Text(selector string) (string, error) {
	r, err := s.post("text", map[string]any{"selector": selector})
	if err != nil {
		return "", err
	}
	return r["text"].(string), nil
}

func (s *KrypticSession) Click(selector string) error {
	_, err := s.post("click", map[string]any{"selector": selector})
	return err
}

func (s *KrypticSession) Fill(selector, value string) error {
	_, err := s.post("fill", map[string]any{"selector": selector, "value": value})
	return err
}

func (s *KrypticSession) Evaluate(js string) (any, error) {
	r, err := s.post("evaluate", map[string]any{"js": js})
	if err != nil {
		return nil, err
	}
	return r["result"], nil
}

func (s *KrypticSession) Screenshot(fullPage bool) ([]byte, error) {
	r, err := s.post("screenshot", map[string]any{"full_page": fullPage})
	if err != nil {
		return nil, err
	}
	data, _ := r["data"].(string)
	return base64.StdEncoding.DecodeString(data)
}

func (s *KrypticSession) BlockResources(types []string) error {
	_, err := s.post("block", map[string]any{"resource_types": types})
	return err
}

func (s *KrypticSession) WaitFor(selector, state string) error {
	_, err := s.post("wait_for", map[string]any{"selector": selector, "state": state})
	return err
}

func (s *KrypticSession) Close() error {
	_, err := s.client.request("DELETE", "/sessions/"+s.ID, nil)
	return err
}

// ── example main ─────────────────────────────────────────────────────────────

func main() {
	k := New()

	health, err := k.Health()
	if err != nil {
		fmt.Fprintln(os.Stderr, "Cannot reach Kryptic server:", err)
		fmt.Fprintln(os.Stderr, "Start it with: python -m kryptic serve")
		os.Exit(1)
	}
	fmt.Println("Server health:", health)

	s, err := k.Session()
	if err != nil {
		panic(err)
	}
	defer s.Close()

	_ = s.BlockResources([]string{"image", "stylesheet", "font", "media"})
	if err := s.Goto("https://example.com"); err != nil {
		panic(err)
	}

	title, _ := s.Title()
	h1, _ := s.Text("h1")
	fmt.Println("Title:", title)
	fmt.Println("H1:", h1)

	resp, _ := k.HTTPGet("https://httpbin.org/get", nil)
	fmt.Println("HTTP status:", resp["status"])

	urls := []string{"https://example.com", "https://example.org", "https://iana.org"}
	batch, _ := k.HTTPBatch(urls)
	for _, r := range batch {
		rm := r.(map[string]any)
		u := strings.Split(fmt.Sprintf("%v", rm["url"]), "?")[0]
		fmt.Printf("  %.0f  %s\n", rm["status"], u)
	}
}

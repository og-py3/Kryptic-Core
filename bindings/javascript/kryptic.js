/**
 * Kryptic JavaScript Client
 *
 * Communicates with a running Kryptic server (python -m kryptic serve).
 *
 * Install: no external dependencies — uses Node.js built-in `http` module.
 *
 * Usage:
 *   const { KrypticClient } = require('./kryptic');
 *
 *   const client = new KrypticClient(); // default: localhost:7890
 *
 *   // Browser session
 *   const session = await client.session();
 *   await session.goto('https://example.com');
 *   const title = await session.title();
 *   console.log(title);
 *   await session.close();
 *
 *   // HTTP-only (no browser)
 *   const resp = await client.httpGet('https://example.com');
 *   console.log(resp.status, resp.body.slice(0, 100));
 */

'use strict';

const http = require('http');

class KrypticError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'KrypticError';
    this.status = status;
  }
}

class KrypticClient {
  /**
   * @param {string} host  Kryptic server host (default: 127.0.0.1)
   * @param {number} port  Kryptic server port (default: 7890)
   */
  constructor(host = '127.0.0.1', port = 7890) {
    this.host = host;
    this.port = port;
  }

  _request(method, path, body = null) {
    return new Promise((resolve, reject) => {
      const payload = body ? JSON.stringify(body) : null;
      const options = {
        hostname: this.host,
        port: this.port,
        path,
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
        },
      };

      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            if (!parsed.ok) {
              reject(new KrypticError(parsed.error || 'Unknown error', res.statusCode));
            } else {
              resolve(parsed);
            }
          } catch (e) {
            reject(new KrypticError(`Invalid JSON response: ${data}`, res.statusCode));
          }
        });
      });

      req.on('error', reject);
      if (payload) req.write(payload);
      req.end();
    });
  }

  async health() {
    return this._request('GET', '/health');
  }

  /**
   * Create a new browser session.
   * @returns {Promise<KrypticSession>}
   */
  async session() {
    const { session_id } = await this._request('POST', '/sessions');
    return new KrypticSession(this, session_id);
  }

  async httpGet(url, headers = {}) {
    return this._request('POST', '/http/get', { url, headers });
  }

  async httpPost(url, { json = null, data = null, headers = {} } = {}) {
    return this._request('POST', '/http/post', { url, json, data, headers });
  }

  async httpBatch(urls) {
    const { results } = await this._request('POST', '/http/batch', { urls });
    return results;
  }
}

class KrypticSession {
  constructor(client, id) {
    this._client = client;
    this.id = id;
  }

  _post(action, body = {}) {
    return this._client._request('POST', `/sessions/${this.id}/${action}`, body);
  }

  _get(action) {
    return this._client._request('GET', `/sessions/${this.id}/${action}`);
  }

  async goto(url, waitUntil = 'domcontentloaded') {
    return this._post('goto', { url, wait_until: waitUntil });
  }

  async title() {
    const { title } = await this._get('title');
    return title;
  }

  async html() {
    const { html } = await this._get('html');
    return html;
  }

  async url() {
    const { url } = await this._get('url');
    return url;
  }

  async text(selector) {
    const { text } = await this._post('text', { selector });
    return text;
  }

  async click(selector) {
    return this._post('click', { selector });
  }

  async fill(selector, value) {
    return this._post('fill', { selector, value });
  }

  async evaluate(js) {
    const { result } = await this._post('evaluate', { js });
    return result;
  }

  async find(selector) {
    return this._post('find', { selector });
  }

  async screenshot(fullPage = false) {
    const { data } = await this._post('screenshot', { full_page: fullPage });
    return Buffer.from(data, 'base64');
  }

  async blockResources(resourceTypes = ['image', 'stylesheet', 'font', 'media']) {
    return this._post('block', { resource_types: resourceTypes });
  }

  async waitFor(selector, state = 'visible') {
    return this._post('wait_for', { selector, state });
  }

  async close() {
    return this._client._request('DELETE', `/sessions/${this.id}`);
  }
}

module.exports = { KrypticClient, KrypticSession, KrypticError };

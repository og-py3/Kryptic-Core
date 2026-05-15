# frozen_string_literal: true

# Kryptic Ruby Client
#
# Communicates with a running Kryptic server (python -m kryptic serve).
# Zero external dependencies — uses Ruby's built-in Net::HTTP.
#
# Requirements: Ruby 2.7+
#
# Usage:
#   require_relative 'kryptic'
#   k = Kryptic::Client.new
#   s = k.session
#   s.goto('https://example.com')
#   puts s.title
#   s.close

require 'net/http'
require 'json'
require 'base64'
require 'uri'

module Kryptic
  class Error < StandardError; end

  class Client
    def initialize(host: '127.0.0.1', port: 7890)
      @host = host
      @port = port
      @http = Net::HTTP.new(host, port)
      @http.read_timeout = 60
      @http.open_timeout = 10
    end

    # ── Low-level helpers ──────────────────────────────────────────────────────

    def request(method, path, body = nil)
      uri = URI::HTTP.build(host: @host, port: @port, path: path)

      req_class = case method.upcase
                  when 'GET'    then Net::HTTP::Get
                  when 'POST'   then Net::HTTP::Post
                  when 'DELETE' then Net::HTTP::Delete
                  else raise ArgumentError, "Unsupported method: #{method}"
                  end

      req = req_class.new(uri)
      req['Content-Type'] = 'application/json'
      req.body = body ? body.to_json : '{}'

      resp = @http.request(req)
      data = JSON.parse(resp.body)

      raise Error, data['error'] || 'Unknown error' unless data['ok']

      data
    end

    def get(path)
      uri = URI::HTTP.build(host: @host, port: @port, path: path)
      req = Net::HTTP::Get.new(uri)
      req['Content-Type'] = 'application/json'
      resp = @http.request(req)
      JSON.parse(resp.body)
    end

    # ── API ────────────────────────────────────────────────────────────────────

    def health
      get('/health')
    end

    def session
      data = request('POST', '/sessions')
      Session.new(self, data['session_id'])
    end

    def http_get(url, headers: {})
      request('POST', '/http/get', { url: url, headers: headers })
    end

    def http_post(url, json: {}, headers: {})
      request('POST', '/http/post', { url: url, json: json, headers: headers })
    end

    def http_batch(urls)
      data = request('POST', '/http/batch', { urls: urls })
      data['results'] || []
    end
  end

  class Session
    attr_reader :id

    def initialize(client, id)
      @client = client
      @id     = id
    end

    def post(action, body = {})
      @client.request('POST', "/sessions/#{@id}/#{action}", body)
    end

    def get_action(action)
      @client.get("/sessions/#{@id}/#{action}")
    end

    def goto(url, wait_until: 'domcontentloaded')
      post('goto', { url: url, wait_until: wait_until })
    end

    def title
      get_action('title')['title'] || ''
    end

    def html
      get_action('html')['html'] || ''
    end

    def url
      get_action('url')['url'] || ''
    end

    def text(selector)
      post('text', { selector: selector })['text'] || ''
    end

    def click(selector)
      post('click', { selector: selector })
    end

    def fill(selector, value)
      post('fill', { selector: selector, value: value })
    end

    def evaluate(js)
      post('evaluate', { js: js })['result']
    end

    def find(selector)
      post('find', { selector: selector })
    end

    def screenshot(full_page: false)
      data = post('screenshot', { full_page: full_page })
      Base64.decode64(data['data'] || '')
    end

    def block_resources(types: %w[image stylesheet font media])
      post('block', { resource_types: types })
    end

    def wait_for(selector, state: 'visible')
      post('wait_for', { selector: selector, state: state })
    end

    def close
      @client.request('DELETE', "/sessions/#{@id}")
    end
  end
end

# ── Example ────────────────────────────────────────────────────────────────────

if __FILE__ == $PROGRAM_NAME
  k = Kryptic::Client.new
  puts "Health: #{k.health}"

  s = k.session
  s.block_resources
  s.goto('https://example.com')
  puts "Title: #{s.title}"
  puts "H1:    #{s.text('h1')}"
  s.close

  resp = k.http_get('https://httpbin.org/get')
  puts "HTTP status: #{resp['status']}"

  batch = k.http_batch(%w[https://example.com https://example.org https://iana.org])
  batch.each { |r| puts "  #{r['status']}  #{r['url']}" }
end

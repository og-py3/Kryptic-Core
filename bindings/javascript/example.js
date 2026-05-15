/**
 * Kryptic JavaScript example.
 * Start the server first: python -m kryptic serve
 * Then run: node example.js
 */

'use strict';

const { KrypticClient } = require('./kryptic');

async function main() {
  const client = new KrypticClient();

  // Health check
  const health = await client.health();
  console.log('Server:', health);

  // Browser session
  const session = await client.session();
  await session.blockResources(['image', 'stylesheet', 'font', 'media']);
  await session.goto('https://example.com');

  const title = await session.title();
  const h1    = await session.text('h1');
  console.log('Title:', title);
  console.log('H1:', h1);

  await session.close();

  // HTTP mode
  const resp = await client.httpGet('https://httpbin.org/get');
  console.log('HTTP GET status:', resp.status);

  // Batch HTTP requests
  const batch = await client.httpBatch([
    'https://example.com',
    'https://example.org',
    'https://iana.org',
  ]);
  batch.forEach((r) => console.log(`${r.status}  ${r.url}`));
}

main().catch(console.error);

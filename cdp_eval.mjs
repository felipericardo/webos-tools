// Evaluate a JS expression in a page of the TV's web engine over the Chrome
// DevTools Protocol (reach port 9998 through an SSH tunnel first).
// Usage: node cdp_eval.mjs <port> <title-substring> '<expression>'
const [port, titlePart, expression] = process.argv.slice(2);

const pages = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
const page = pages.find((p) => p.type === 'page' && (p.title || '').includes(titlePart));
if (!page) {
  console.error(`no page matching "${titlePart}": ${pages.map((p) => p.title).join(', ')}`);
  process.exit(1);
}

const ws = new WebSocket(page.webSocketDebuggerUrl);
ws.onopen = () => ws.send(JSON.stringify({
  id: 1,
  method: 'Runtime.evaluate',
  params: {expression, returnByValue: true, awaitPromise: true},
}));
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id !== 1) return;
  const r = msg.result || {};
  if (r.exceptionDetails) console.error('exception:', JSON.stringify(r.exceptionDetails));
  const v = r.result ? r.result.value : msg;
  console.log(typeof v === 'string' ? v : JSON.stringify(v, null, 2));
  ws.close();
};
ws.onerror = (e) => { console.error('ws error', e.message || e); process.exit(1); };

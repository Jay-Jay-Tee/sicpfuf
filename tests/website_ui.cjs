// node tests/website_ui.cjs /path/to/jsdom /path/to/built/site
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { execFileSync } = require('node:child_process');
const { JSDOM } = require(resolve(process.argv[2]));
const site = resolve(process.argv[3] || 'site');
const root = resolve(__dirname, '..');
const assets = resolve(site, 'assets/stepper');
const entries = JSON.parse(readFileSync(resolve(assets, 'examples.json'), 'utf8'));
const dom = new JSDOM(readFileSync(resolve(assets, 'index.html'), 'utf8'), {
  url: 'https://example.test/sicpfuf/assets/stepper/index.html', runScripts: 'outside-only'
});
const w = dom.window, doc = w.document, get = id => doc.getElementById(id);
let workers = [], blocked = false;
class Worker {
  constructor(url, options) {
    assert.equal(String(url), 'https://example.test/sicpfuf/assets/stepper/worker.js');
    assert.equal(options.type, 'module');
    this.terminated = false;
    workers.push(this);
  }
  postMessage(data) {
    this.onmessage({ data: { type: 'status', message: 'Tracing your program…' } });
    if (blocked) return;
    const trace = JSON.parse(execFileSync('python3', ['-m', 'sicpfuf.ui', '--trace'], {
      cwd: root, input: JSON.stringify({ ...data, max_steps: 400 })
    }));
    this.onmessage({ data: { type: 'result', trace } });
  }
  terminate() { this.terminated = true; }
}
w.Worker = Worker;
w.fetch = async url => {
  assert.equal(String(url), 'https://example.test/sicpfuf/assets/stepper/examples.json');
  return { ok: true, json: async () => entries };
};
Object.defineProperty(doc, 'currentScript', { value: { src: 'https://example.test/sicpfuf/assets/stepper/website.js' } });
const wait = () => new Promise(resolve => setTimeout(resolve, 15));
const end = () => { get('position').value = get('position').max; get('position').dispatchEvent(new w.Event('input')); };
function edit(source) { get('code').value = source; get('code').dispatchEvent(new w.Event('input')); }
(async () => {
  w.eval(readFileSync(resolve(assets, 'website.js'), 'utf8'));
  w.eval(readFileSync(resolve(assets, 'ui.js'), 'utf8'));
  await wait(); end();
  assert.equal(get('output').textContent, '11\n');
  assert.equal(workers.length, 0, 'recorded examples need no Python download');
  assert.ok(get('diagram').querySelector('[data-frame="E1"][data-reachable="false"]'));
  assert.ok(get('diagram').querySelector('[data-frame="E2"].unreachable'));
  get('diagram').querySelector('[data-frame="E1"]').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  assert.match(get('inspection').textContent, /Unreachable · retained/);
  edit('print(21 * 2)\n'); get('run').click(); await wait(); end();
  assert.equal(get('output').textContent, '42\n');
  assert.equal(workers.length, 1);
  assert.equal(get('stop').disabled, true);
  get('example').value = 'typed'; get('example').dispatchEvent(new w.Event('change'));
  await wait(); end();
  assert.equal(get('typed').checked, true);
  assert.equal(get('output').textContent, '9\n');
  assert.equal(workers.length, 1);
  blocked = true;
  edit('x: int = 5\n'); get('run').click(); await wait();
  assert.equal(get('stop').disabled, false);
  assert.equal(get('example').disabled, true);
  get('stop').click(); await wait();
  assert.equal(workers[0].terminated, true);
  assert.match(get('error').textContent, /Run stopped/);
  assert.equal(get('run').disabled, false);
  blocked = false;
  get('run').click(); await wait();
  assert.equal(workers.length, 2, 'Run restarts Python after Stop');
  assert.equal(get('error').hidden, true);
  w.close();

  // A textbook link transfers code and chapter under a project-prefixed URL.
  const book = new JSDOM('<div class="md-content"><div class="highlight"><span class="filename">§4 · --typed</span><code>x: int = 1\nprint(x)</code></div></div>', {
    url: 'https://example.test/sicpfuf/book/19-types-objects/', runScripts: 'outside-only'
  });
  Object.defineProperty(book.window.document, 'currentScript', { value: { src: 'https://example.test/sicpfuf/assets/stepper-links.js' } });
  book.window.eval(readFileSync(resolve(site, 'assets/stepper-links.js'), 'utf8'));
  const link = book.window.document.querySelector('.stepper-explore');
  assert.equal(link.href, 'https://example.test/sicpfuf/playground/');
  link.dispatchEvent(new book.window.MouseEvent('click'));
  const imported = JSON.parse(book.window.sessionStorage.getItem('sicpfuf-stepper-import'));
  assert.equal(imported.chapter, 4);
  assert.equal(imported.typed, true);
  assert.equal(imported.source, 'x: int = 1\nprint(x)');
  book.window.close();
  console.log('Website UI checks passed: instant examples, retained grey frames, edits, Typed, Stop, restart, and textbook links.');
})().catch(error => { console.error(error); w.close(); process.exitCode = 1; });

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
    const trace = JSON.parse(execFileSync('python3', ['-m', 'sicpfuf.ui', data.validate_only ? '--check' : '--trace'], {
      cwd: root, input: JSON.stringify({ max_steps: 400, ...data })
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
  w.eval(readFileSync(resolve(assets, 'tree.js'), 'utf8'));
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
  get('typed').checked = false; get('typed').dispatchEvent(new w.Event('change'));
  get('max-steps').value = 2; get('max-steps').dispatchEvent(new w.Event('change'));
  edit('print(2 + 3)\n'); get('run').click(); await wait();
  assert.match(get('error').textContent, /2 steps/);
  get('more-steps').click(); await wait();
  assert.equal(get('max-steps').value, '4');
  get('max-steps').value = 400; get('max-steps').dispatchEvent(new w.Event('change'));
  get('example').value = 'nested-tree'; get('example').dispatchEvent(new w.Event('change'));
  await wait(); end();
  assert.equal(get('view-tree').getAttribute('aria-pressed'), 'true');
  assert.ok(get('diagram').querySelector('.tree-diagram'));
  get('example').value = 'binary-tree'; get('example').dispatchEvent(new w.Event('change'));
  await wait(); end();
  assert.equal(get('tree-format').value, 'binary');
  assert.match(get('diagram').textContent, /binary node/);
  get('example').value = 'scope'; get('example').dispatchEvent(new w.Event('change'));
  await wait(); end();
  assert.equal(get('view-diagram').getAttribute('aria-pressed'), 'true');
  assert.equal(get('tree-controls').hidden, true);
  edit('print(missing)\n');
  await new Promise(resolve => setTimeout(resolve, 550));
  assert.equal(get('syntax').querySelector('.editor-squiggle').textContent, 'missing');
  assert.equal(get('run').disabled, false, 'live checks leave editing enabled');
  // Stop while a check is pending also cancels the Run queued behind it.
  blocked = true;
  edit('print(987)\n'); await new Promise(resolve => setTimeout(resolve, 550));
  get('run').click(); await wait();
  get('stop').click(); await wait();
  assert.match(get('error').textContent, /Run stopped/);
  blocked = false;
  get('run').click(); await wait(); end();
  assert.equal(get('output').textContent, '987\n');
  require('./tree_view.cjs')(w, root);
  w.close();

  // A textbook link transfers code and chapter under a project-prefixed URL.
  const book = new JSDOM('<div class="md-content"><div class="highlight"><span class="filename">§4 · --typed</span><code>x: int = 1\nprint(x)</code></div></div>', {
    url: 'https://example.test/sicpfuf/book/19-types-objects/', runScripts: 'outside-only'
  });
  Object.defineProperty(book.window.document, 'currentScript', { value: { src: 'https://example.test/sicpfuf/assets/stepper-links.js' } });
  book.window.eval(readFileSync(resolve(site, 'assets/stepper-links.js'), 'utf8'));
  const link = book.window.document.querySelector('.stepper-explore');
  assert.equal(new URL(link.href).pathname, '/sicpfuf/playground/');
  const linkedProgram = JSON.parse(new URLSearchParams(new URL(link.href).hash.slice(1)).get('program'));
  assert.equal(linkedProgram.source, 'x: int = 1\nprint(x)');
  link.addEventListener('click', event => event.preventDefault());
  link.dispatchEvent(new book.window.MouseEvent('click', {cancelable: true}));
  const imported = JSON.parse(book.window.sessionStorage.getItem('sicpfuf-stepper-import'));
  assert.equal(imported.chapter, 4);
  assert.equal(imported.typed, true);
  // The complete import survives a new tab/reload with no shared browser storage.
  const payload = {source: ['print("λ + # &")', '# ' + String.fromCharCode(92), ''].join('\n'),chapter: 2,mode: 'substitution',typed: false};
  const fragment = new URLSearchParams({program: JSON.stringify(payload)}).toString();
  for (let reload=0; reload<2; reload++) {
    const fresh = new JSDOM(readFileSync(resolve(assets, 'index.html'), 'utf8'), {
      url: 'https://example.test/sicpfuf/assets/stepper/index.html#'+fragment, runScripts: 'outside-only'
    });
    const fw = fresh.window;
    fw.fetch = async () => ({ok:true,json:async()=>entries});
    fw.Worker = Worker;
    Object.defineProperty(fw,'sessionStorage',{get(){throw new Error('Storage blocked');}});
    Object.defineProperty(fw.document,'currentScript',{value:{src:'https://example.test/sicpfuf/assets/stepper/website.js'}});
    fw.eval(readFileSync(resolve(assets,'website.js'),'utf8'));
    const session = await (await fw.sicpfufRequest('/api/session')).json();
    for (const key of ['source','chapter','mode','typed']) assert.equal(session[key],payload[key]);
    fw.eval(readFileSync(resolve(assets,'tree.js'),'utf8'));
    fw.eval(readFileSync(resolve(assets,'ui.js'),'utf8'));
    await wait();
    assert.equal(fw.document.getElementById('code').value,payload.source);
    assert.equal(fw.document.getElementById('mode').value,payload.mode);
    fresh.window.close();
  }
  const wrapper = new JSDOM('<iframe class="stepper-frame" src="../assets/stepper/index.html"></iframe><a class="stepper-fullscreen" href="../assets/stepper/index.html"></a>', {
    url:'https://example.test/sicpfuf/playground/#'+fragment,runScripts:'outside-only'
  });
  Object.defineProperty(wrapper.window.document,'currentScript',{value:{src:'https://example.test/sicpfuf/assets/stepper-links.js'}});
  wrapper.window.eval(readFileSync(resolve(site,'assets/stepper-links.js'),'utf8'));
  for (const selector of ['iframe','a']) {
    const node = wrapper.window.document.querySelector(selector);
    assert.equal(new URL(node.src || node.href).hash,'#'+fragment);
  }
  wrapper.window.close();
  assert.equal(imported.source, 'x: int = 1\nprint(x)');
  book.window.close();
  console.log('Website UI checks passed: examples, grey frames, Tree, Max steps, edits, Typed, Stop, restart, and textbook imports across fresh tabs, reloads, and blocked storage.');
})().catch(error => { console.error(error); w.close(); process.exitCode = 1; });

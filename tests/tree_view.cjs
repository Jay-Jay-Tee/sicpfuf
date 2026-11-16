// Shared renderer checks, using real interpreter heaps and adversarial graph shapes.
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');

module.exports = function checkTrees(window, root) {
  const renderer = window.sicpfufTree;
  function snapshot(source) {
    const result = JSON.parse(execFileSync('python3', ['-m', 'sicpfuf.ui', '--trace'], {
      cwd: root, input: JSON.stringify({ source, chapter: 3, mode: 'environment', graphics: false })
    }));
    assert.equal(result.error, null);
    return result.steps.at(-1).store;
  }
  const labels = svg => [...svg.querySelectorAll('[data-tree-node] > text:first-of-type')].map(node => node.textContent);
  const trees = snapshot('t = llist(1, llist(2,3), llist(llist(4),None), 5)\n');
  const before = JSON.stringify(trees), selected = renderer.roots(trees)[0];
  const nested = renderer.draw(trees, selected.value);
  assert.equal(JSON.stringify(trees), before, 'tree rendering must not mutate a history');
  assert.equal(nested.svg.querySelectorAll('.tree-object').length, 4);
  assert.deepEqual(labels(nested.svg).filter(x => /^\d$/.test(x)), ['1','2','3','4','5']);
  assert.equal(labels(nested.svg).filter(x => x === '∅').length, 1);
  assert.equal(nested.note, '');
  // Sibling boxes cannot overlap on the same level.
  const rectangles = [...nested.svg.querySelectorAll('[data-tree-node] > rect')].map(node =>
    ['x','y','width','height'].map(name => Number(node.getAttribute(name))));
  for (let i=0;i<rectangles.length;i++) for (let j=i+1;j<rectangles.length;j++) {
    const [x,y,w,h]=rectangles[i], [xx,yy,ww,hh]=rectangles[j];
    assert.ok(!(x<xx+ww && xx<x+w && y<yy+hh && yy<y+h), 'tree nodes overlap');
  }
  const binary = snapshot('t = llist(8, llist(3,None,None), llist(11,None,None))\n');
  const binaryPicture = renderer.draw(binary, renderer.roots(binary)[0].value, 'binary');
  assert.deepEqual(labels(binaryPicture.svg).filter(x => /^\d+$/.test(x)), ['8','3','11']);
  assert.equal(labels(binaryPicture.svg).filter(x => x === '∅').length, 4);
  assert.equal(binaryPicture.note, '');
  const invalid = renderer.draw(trees, selected.value, 'binary');
  assert.match(invalid.note, /expects llist\(entry, left, right\)/);
  assert.ok(invalid.svg.querySelector('.tree-invalid'));
  const shared = snapshot('branch = llist(6,7)\nt = llist(branch,branch)\n');
  const sharedValue = renderer.roots(shared).find(option => option.label.includes('· t')).value;
  const sharedPicture = renderer.draw(shared, sharedValue);
  assert.equal(sharedPicture.svg.querySelectorAll('[data-tree-reference]').length, 1);
  assert.match(sharedPicture.note, /Shared nodes/);
  assert.deepEqual(labels(sharedPicture.svg).filter(x => /^\d$/.test(x)), ['6','7']);
  const sharingTail = snapshot('suffix = llist(7,8)\nt = pair(6,suffix)\n');
  const tailPicture = renderer.draw(sharingTail, renderer.roots(sharingTail).find(option => option.label.includes('· t')).value);
  assert.match(tailPicture.note, /Shared tails/);
  assert.deepEqual(labels(tailPicture.svg).filter(x => /^\d$/.test(x)), ['6','7','8']);
  const cycle = snapshot('t = pair(1,None)\nset_tail(t,t)\n');
  const cyclePicture = renderer.draw(cycle, renderer.roots(cycle)[0].value);
  assert.equal(cyclePicture.svg.querySelectorAll('[data-tree-reference="cycle reference"]').length, 1);
  assert.ok(cyclePicture.svg.querySelectorAll('[data-tree-node]').length < 5);
  const empty = snapshot('t = None\n');
  assert.deepEqual(labels(renderer.draw(empty, renderer.roots(empty)[0].value).svg), ['∅']);
  const arbitrary = snapshot('t = [1,2,3]\n');
  assert.deepEqual(labels(renderer.draw(arbitrary, renderer.roots(arbitrary)[0].value).svg), ['list','1','2','3']);
  const text = snapshot('t = llist("<script>alert(1)</script>")\n');
  const safe = renderer.draw(text, renderer.roots(text)[0].value).svg;
  assert.equal(safe.querySelector('script'), null);
  assert.match(safe.textContent, /<script>/);
  const deep = { frames: [], heap: [] };
  for (let i=0;i<100;i++) deep.heap.push({ id:'#'+i,kind:'list',isGarbage:true,elements:[
    i<99 ? {kind:'ref',objectId:'#'+(i+1)} : {kind:'primitive',display:'1'},
    {kind:'primitive',display:'None'}] });
  const bounded = renderer.draw(deep,{kind:'ref',objectId:'#0'});
  assert.ok(bounded.svg.querySelectorAll('[data-tree-node]').length <= 320);
  assert.match(bounded.note,/abbreviated/);
  assert.ok(bounded.svg.querySelector('.unreachable'));
  const wide = { frames: [], heap: [{id:'#0',kind:'list',isGarbage:false,
    elements:Array.from({length:1000},(_,i)=>({kind:'primitive',display:String(i)}))}] };
  const capped = renderer.draw(wide,{kind:'ref',objectId:'#0'});
  assert.equal(capped.svg.querySelectorAll('[data-tree-node]').length,320);
  assert.match(capped.note,/at most 320/);
};

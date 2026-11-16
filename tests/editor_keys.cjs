// Exercise the same editor shortcuts in the local and website UI.
const assert = require('node:assert/strict');

module.exports = function editorKeys(w) {
  const code = w.document.getElementById('code');
  function setup(text, start = text.length, end = start) {
    code.value = text; code.setSelectionRange(start, end);
    code.dispatchEvent(new w.Event('input', {bubbles:true}));
  }
  function press(key, options = {}) {
    const event = new w.KeyboardEvent('keydown', {key, bubbles:true, cancelable:true, ...options});
    code.dispatchEvent(event);
    return event.defaultPrevented;
  }
  function result(text, start = text.length, end = start) {
    assert.equal(code.value, text);
    assert.equal(code.selectionStart, start);
    assert.equal(code.selectionEnd, end);
    assert.equal(w.document.getElementById('syntax').textContent, text + '\n');
  }
  setup('def f(x):'); assert.ok(press('Enter')); result('def f(x):\n    ');
  setup('    if x: # explanation'); press('Enter'); result('    if x: # explanation\n        ');
  setup('    x = 1'); press('Enter'); result('    x = 1\n    ');
  setup('    return "done"'); press('Enter'); result('    return "done"\n');
  setup('x = ":"'); press('Enter'); result('x = ":"\n');
  setup('# ignore this:'); press('Enter'); result('# ignore this:\n');
  setup('    call()', 9); press('Enter'); result('    call(\n        \n    )', 18);
  setup('xs = [   ]', 6); press('Enter'); result('xs = [\n    \n]', 11);
  setup('xs = [\n    1,'); press('Enter'); result('xs = [\n    1,\n    ');
  setup('"""text:'); press('Enter'); result('"""text:\n');
  for (const [open, close] of [['(',')'], ['[',']'], ['{','}'], ['"','"'], ["'", "'"]]) {
    setup(''); assert.ok(press(open)); result(open+close, 1);
    assert.ok(press(close)); result(open+close, 2);
    setup(open+close, 1); assert.ok(press('Backspace')); result('');
    setup('value', 0, 5); press(open); result(open+'value'+close, 1, 6);
  }
  setup(''); press('"'); press('"'); press('"'); result('""""""', 3);
  press('"'); press('"'); press('"'); result('""""""', 6);
  setup('# text'); assert.equal(press('('), false); result('# text');
  setup('"text'); assert.equal(press('['), false); result('"text');
  setup('"a\\"', 3); assert.equal(press('"'), false); result('"a\\"', 3);
  setup('name', 0); assert.equal(press('('), false); result('name', 0);
  setup('xy', 1); press('Tab'); result('x   y', 4);
  setup('    value', 4); press('Tab', {shiftKey:true}); result('value', 0);
  setup('      value', 6); press('Backspace'); result('    value', 4);
  press('Backspace'); result('value', 0);
  setup('one\ntwo\nthree', 0, 8); press('Tab'); result('    one\n    two\nthree', 4, 16);
  press('Tab', {shiftKey:true}); result('one\ntwo\nthree', 0, 8);
  setup('  one\n    two', 0, 13); press('Tab', {shiftKey:true}); result('one\ntwo', 0, 7);
  setup('\nline', 0); press('Tab'); result('    \nline', 4);
  setup(''); assert.equal(press('Backspace'), false);
  assert.equal(press('(', {ctrlKey:true}), false);
  assert.equal(press('[', {altKey:true}), false);
  assert.equal(press('(', {isComposing:true}), false); result('');
  assert.equal(press('z', {metaKey:true}), false, 'native undo must remain available');
  // Hosts supporting native insertion should get one input event per edit,
  // without replacing textarea.value (which would erase browser undo history).
  const command = w.document.execCommand;
  let commands = 0, inputs = 0;
  const input = () => inputs++;
  code.addEventListener('input', input);
  w.document.execCommand = (name, showUI, text) => {
    assert.equal(name, 'insertText'); commands++;
    code.setRangeText(text, code.selectionStart, code.selectionEnd, 'end');
    code.dispatchEvent(new w.Event('input', {bubbles:true})); return true;
  };
  press('('); result('()', 1);
  assert.equal(commands, 1); assert.equal(inputs, 1);
  w.document.execCommand = command; code.removeEventListener('input', input);
};

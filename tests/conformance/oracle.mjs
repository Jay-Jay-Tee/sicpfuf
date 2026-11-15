/** Pinned Source Academy oracle. Run with node after building build_oracle.mjs.
 * Reads one JSON request on stdin; emits cases with real CSE results, never sicpfuf expectations.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';

const upstream = process.env.PYSLANG ?? join(process.env.HOME ?? '', '.cache/sicpfuf/py-slang');
async function main() {
  const request = JSON.parse(readFileSync(0, 'utf8'));
  const require = createRequire(import.meta.url);
  const { runCode, spec, VARIANT_GROUPS, parse, runEStepper, getPythonSteps } = require(process.env.SICPFUF_UPSTREAM_BUNDLE ?? join(tmpdir(), 'sicpfuf-upstream-oracle.cjs'));
  let cases = request.cases ?? [];
  if (request.generate === 'operators') {
    for (const chapter of [1, 2, 3, 4]) {
      const types = spec.universeForChapter(chapter);
      const ops = chapter <= 2 ? spec.BINARY_OPS_12 : spec.BINARY_OPS_34;
      for (const op of ops) for (const left of types) for (const right of types) {
        const expression = `(${spec.literalFor(left, chapter)}) ${op} (${spec.literalFor(right, chapter)})`;
        cases.push({ id: `operators/${chapter}/${left}/${op}/${right}`, chapter,
          source: `print(${expression})\n`, specType: spec.specResult(op, left, right, chapter) });
      }
      for (const op of ['-', '+', 'not']) for (const type of types) {
        cases.push({ id: `operators/${chapter}/${op}/${type}`, chapter,
          source: `print(${op} (${spec.literalFor(type, chapter)}))\n` });
      }
      for (const op of ['and', 'or']) for (const left of types) for (const right of types) {
        cases.push({ id: `operators/${chapter}/${left}/${op}/${right}`, chapter,
          source: `print((${spec.literalFor(left, chapter)}) ${op} (${spec.literalFor(right, chapter)}))\n` });
      }
    }
  }
  if (request.generate === 'builtins') {
    const skip = new Set(['input', 'set_timeout', 'clear_all_timeout', 'draw_data']);
    const literals = ['2', '2.5', '(1+2j)', 'True', "'ab'", 'None', '(lambda x: x)'];
    for (const chapter of [1, 2, 3, 4]) {
      const available = [...literals, ...(chapter === 2 ? ['pair(1, 2)'] : chapter > 2 ? ['[1, 2]', 'llist(1, 2)'] : [])];
      const tuples = [[], ...available.map(value => [value]), ['2', '2'], ['2', '2.5'], ['2.5', '2'], ['2.5', '2.5'], ['2', '2', '2']];
      const names = new Map();
      for (const group of VARIANT_GROUPS[chapter]) for (const [name, value] of group.builtins) names.set(name, value);
      for (const name of names.keys()) {
        if (skip.has(name)) continue;
        if (name === 'random_random' || name === 'time_time') {
          cases.push({ id: `builtins/${chapter}/${name}/type`, chapter, source: `print(is_float(${name}()))\n` });
          continue;
        }
        for (const args of tuples) cases.push({ id: `builtins/${chapter}/${name}/${args.join(',')}`, chapter,
          source: `print(${name}(${args.join(', ')}))\n` });
      }
    }
  }
  const revision = execFileSync('git', ['-C', upstream, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
  const results = [];
  for (const entry of cases) {
    let expected;
    try {
      expected = { output: await runCode(entry.source, entry.chapter, { stepLimit: 200000 }), error: null };
    } catch (error) {
      expected = { output: error.output ?? '', error: error.message,
        category: error.kind ?? error.name };
    }
    if (entry.stepper && !expected.error) {
      const ast = parse(entry.source);
      const steps = entry.stepper === 'environment'
        ? (await runEStepper(ast, entry.source, entry.chapter, 1000)).steps
        : await getPythonSteps(ast, 1000);
      expected.steps = steps.map(step => ({
        explanation: step.markers?.[0]?.explanation,
        phase: step.markers?.[0]?.redexType ?? 'boundary',
        ast: step.ast,
        frames: step.frames,
        heap: step.heap,
        activeFrameId: step.activeFrameId,
        lookups: step.lookups ?? [],
        output: step.output ?? '',
      }));
    }
    results.push({ ...entry, expected });
    if (results.length % 200 === 0) process.stderr.write(`Oracle: ${results.length}/${cases.length}\n`);
  }
  process.stdout.write(JSON.stringify({ upstream: { repository: 'https://github.com/source-academy/py-slang', revision }, cases: results },
    (_key, value) => typeof value === 'bigint' ? value.toString() : value));
}
main().then(() => process.exit(0), error => { console.error(error); process.exit(1); });

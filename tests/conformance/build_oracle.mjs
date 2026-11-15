/** Bundle the pinned upstream TypeScript without changing its checkout. */
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
const upstream = process.env.PYSLANG ?? join(process.env.HOME, '.cache/sicpfuf/py-slang');
const require = createRequire(join(upstream, 'package.json'));
const { build } = require('esbuild');
const outfile = resolve(process.argv[2] ?? join(tmpdir(), 'sicpfuf-upstream-oracle.cjs'));
await build({
  stdin: { contents: `
export { runCode, VARIANT_GROUPS } from './src/runner.ts';
export * as spec from './src/tests/operator-spec.ts';
export { parse } from './src/parser/index.ts';
export { runEStepper } from './src/conductor/estepper/getSteps.ts';
export { getPythonSteps, evaluatePython } from './src/conductor/stepper/getSteps.ts';
`, resolveDir: upstream, loader: 'ts' },
  bundle: true, platform: 'node', format: 'cjs', outfile, logLevel: 'warning',
});
console.log(outfile);

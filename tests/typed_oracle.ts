/**
 * The ORACLE for Python §4 Typed: py-slang's own type checker (basedpyright, with Source Academy's
 * prelude and rules), run on programs given as files. Used by tests/run_tests.py --update / --oracle.
 *
 *     ~/.cache/sicpfuf/py-slang/node_modules/.bin/tsx tests/typed_oracle.ts a.py b.py ...
 *
 * For each file it prints one line of JSON:
 *   {"file": ..., "rule": "<message>"}                  a rule of the annotations is broken
 *                                                       (py-slang reports only the first)
 *   {"file": ..., "errors": ["L:C message", ...]}       the checker's errors (all of them)
 *   {"file": ..., "erased": "<program text>"}           accepted: the program with its types cut
 *                                                       out (same lines and columns), for run_tests.py
 *                                                       to run on py-slang's ordinary Python §4
 *   {"file": ..., "syntax": "<message>"}                py-slang could not parse it
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

const PYSLANG = process.env.PYSLANG ?? join(process.env.HOME ?? "", ".cache/sicpfuf/py-slang");

async function main() {
  const { parse } = await import(join(PYSLANG, "src/parser/parser-adapter.ts"));
  const { StmtNS } = await import(join(PYSLANG, "src/ast-types.ts"));
  const { traverseAST } = await import(join(PYSLANG, "src/validator/index.ts"));
  const typecheck = await import(join(PYSLANG, "src/typecheck/index.ts"));
  const harness = await import(join(PYSLANG, "src/tests/typecheck-harness.ts"));
  const checker = await harness.startTypedChecker();
  try {
    for (const file of process.argv.slice(2)) {
      const source = readFileSync(file, "utf8");
      const text = source.endsWith("\n") ? source : source + "\n";
      const out: Record<string, unknown> = { file };
      let ast;
      try {
        ast = parse(text);
      } catch (e) {
        out.syntax = (e as Error).message.split("\n")[0];
        console.log(JSON.stringify(out));
        continue;
      }
      try {
        typecheck.validateTypedProgram(ast);
      } catch (e) {
        out.rule = (e as Error).message;
        console.log(JSON.stringify(out));
        continue;
      }
      const diagnostics = (await checker.check(text)).filter(
        (d: { severity: string }) => d.severity === "error",
      );
      if (diagnostics.length > 0) {
        out.errors = diagnostics.map(
          (d: { line: number; column: number; message: string }) =>
            `${d.line}:${d.column} ${d.message}`,
        );
        console.log(JSON.stringify(out));
        continue;
      }
      // Cut the types out of the text: blanks keep every other token where it was.
      const chars = text.split("");
      const blank = (from: number, to: number) => {
        for (let i = from; i < to; i++) if (chars[i] !== "\n") chars[i] = " ";
      };
      const end = (e: { endToken: { indexInSource: number; lexeme: string } }) =>
        e.endToken.indexInSource + e.endToken.lexeme.length;
      traverseAST(ast, (node: any) => {
        if (node instanceof StmtNS.FunctionDef) {
          for (const p of node.parameters)
            if (p.annotation) blank(p.indexInSource + p.lexeme.length, end(p.annotation));
          if (node.returns) {
            const arrow = text.lastIndexOf("->", node.returns.startToken.indexInSource);
            blank(arrow, end(node.returns));
          }
          if (node.typeParams.length > 0) {
            const open = text.lastIndexOf("[", node.typeParams[0].indexInSource);
            const last = node.typeParams[node.typeParams.length - 1];
            blank(open, text.indexOf("]", last.indexInSource) + 1);
          }
        } else if (node instanceof StmtNS.AnnAssign) {
          blank(end(node.target), end(node.ann));
        } else if (node instanceof StmtNS.TypeAlias) {
          const from = node.startToken.indexInSource;
          blank(from, end(node));
          chars.splice(from, 4, "p", "a", "s", "s");
        }
      });
      out.erased = chars.join("");
      console.log(JSON.stringify(out));
    }
  } finally {
    checker.dispose();
  }
}

main().then(
  () => process.exit(0),
  e => {
    console.error(e);
    process.exit(1);
  },
);

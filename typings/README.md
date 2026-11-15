# Editor hints

Pylance/Pyright reads `__builtins__.pyi` to recognise names supplied by sicpfuf, such as
`show_env`, `pair`, `llist` and `math_sqrt`. The four module directories describe the imports
provided by the interpreter. These are editor declarations, not importable Python modules.

They deliberately use permissive types: Pylance's native-Python rules are not the Python §
rules. Use `python3 -m sicpfuf program.py --typed` for the actual Python §4 type check.
No warnings are disabled. Ordinary Python built-ins keep their standard editor definitions.

Open the repository folder as your VS Code workspace so its settings and stubs are found.
If an already-open file still shows old diagnostics, run **Developer: Reload Window**.

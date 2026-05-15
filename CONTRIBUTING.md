# Contributing to Kryptic

Thank you for your interest in contributing!

---

## Getting started

1. **Fork** the repository and clone your fork:

   ```bash
   git clone https://github.com/<your-username>/kryptic
   cd kryptic
   ```

2. **Install dependencies:**

   ```bash
   pip install -e ".[dev]"
   python -m playwright install chromium
   ```

3. **Create a branch** for your change:

   ```bash
   git checkout -b feat/my-feature
   ```

---

## Project layout

```
kryptic/          Python library source
bindings/         Client libraries for other languages
examples/         Runnable usage examples
tests/            Test suite (pytest)
```

---

## Coding guidelines

- Python 3.10+ syntax and type hints throughout
- All public methods must have docstrings
- Never use `print()` in library code — raise exceptions or return structured data
- All async functions must be fully awaited; no fire-and-forget side effects
- New features should come with at least one example in `examples/`
- Keep bindings in sync — if you add a server endpoint, add the corresponding method to all six language bindings

---

## Running the tests

```bash
pytest tests/
```

---

## Submitting a pull request

1. Make sure existing tests pass
2. Add tests for new behaviour
3. Update `CHANGELOG.md` under `[Unreleased]`
4. Open a PR with a clear description of what you changed and why

---

## Reporting bugs

Open an issue and include:

- Python version and OS
- Kryptic version
- Minimal code that reproduces the problem
- Full error traceback

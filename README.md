# Bola Utils

Bola Utils is a personal, growing collection of small, reusable utilities for
getting practical work done quickly. Utilities may be written in Python, Bash,
SQL, or another language when that is the clearest tool for the job.

The repository is intentionally organized by utility. Each utility has its own
folder, README, implementation, and tests or runnable examples where they add
value.

## Available utilities

| Utility | What it does | Status |
| --- | --- | --- |
| [Timestamp Normalizer](<Timestamp Normalizer/>) | Rescales timestamp columns onto a configurable target date period while preserving relative position. | Available |

## Repository layout

```text
bola-utils/
├── README.md
└── Timestamp Normalizer/
    ├── README.md
    ├── pyproject.toml
    ├── timestamp_normalizer.py
    └── test_timestamp_normalizer.py
```

Each utility should be understandable and usable without requiring knowledge of
the rest of the repository.

## Quick start

Choose a utility and follow its README. For Timestamp Normalizer:

```bash
cd "Timestamp Normalizer"
python3 -m pip install -e ".[test,pandas]"
python3 -m pytest -q
```

The pandas extra is only needed for DataFrame and Series support. The core
timestamp transformation uses the Python standard library.

## Design principles

- Keep utilities small and focused.
- Prefer safe, explicit defaults.
- Preserve input data unless a caller explicitly requests in-place behavior.
- Include a practical use case, not only an abstract API description.
- Document important edge cases and assumptions.
- Add tests for behavior that should remain stable.
- Avoid coupling one utility to another unless the dependency is deliberate.

## Adding a utility

1. Create a clearly named subfolder for the utility.
2. Add a README explaining what it solves, when to use it, and how to run it.
3. Keep implementation files and tests inside that subfolder.
4. Document dependencies and provide a quick-start example.
5. Add the utility to the catalog above.

The goal is a useful personal toolbox that can also be shared with collaborators
without a long explanation.

## Branching strategy

The repository uses three persistent branches:

- `main` is the stable branch.
- `staging` is the integration and release-candidate branch.
- `dev-bola` is Bolaji's development branch and follows the `dev-*` convention.

Other development branches should also use the `dev-*` prefix, for example
`dev-new-utility` or `dev-sql-helper`. The normal promotion path is:

```text
dev-*  →  staging  →  main
```

Continuous integration runs on pushes to `main`, `staging`, and `dev-*`, and on
pull requests targeting `main` or `staging`. It discovers the utility folders
changed by the event and runs that utility's quality, format, and integration
checks.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow and the
subproject CI contract.

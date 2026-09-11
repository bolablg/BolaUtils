# Contributing to Bola Utils

## Branch workflow

Use the following branch roles:

| Branch | Purpose |
| --- | --- |
| `main` | Stable, shareable code |
| `staging` | Integration and release-candidate validation |
| `dev-bola` | Bolaji's active development branch |
| `dev-*` | Other development branches |

Promote changes through `dev-*` to `staging`, then from `staging` to `main`.
Keep development branches focused on one utility or related change.

## Subproject contract

Each utility lives in its own top-level folder and should contain:

```text
<Utility Name>/
├── README.md
├── ci/
│   ├── format.sh
│   ├── integration.sh
│   └── quality.sh
└── implementation and tests
```

The three scripts are the utility's CI interface:

- `quality.sh` checks correctness, static quality, and basic validity.
- `format.sh` verifies that source files are formatted.
- `integration.sh` runs the utility's integration-level checks.

The scripts may use language-specific tools. A Python utility can use a local
`pyproject.toml`; a Bash or SQL utility can define its own tooling inside the
same scripts. The root workflow does not need to know the implementation
language.

## Local validation

Run the checks from the utility folder before opening a pull request:

```bash
bash ci/quality.sh
bash ci/format.sh
bash ci/integration.sh
```

For Timestamp Normalizer, install its development extras first:

```bash
python3 -m pip install -e ".[ci]"
```

## Pull requests

Pull requests should explain the use case, identify the affected utility, and
include tests or runnable examples for behavior that changed. The GitHub
workflow automatically runs checks for each changed or newly created utility;
an unrelated utility is not run unless the change touches it.

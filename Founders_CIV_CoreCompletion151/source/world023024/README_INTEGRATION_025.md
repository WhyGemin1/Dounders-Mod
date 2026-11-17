# Founders-CIV INTEGRATION-025: compatibility layer and project history

**Base:** latest supplied `WORLD-024` experimental branch. No source edits to original core or existing Social/World mechanics; all new integration code is opt-in.

## Contents

- `founders_civ/integration/`: versioned contracts, live WORLD-024 adapter, read-only branch inspector, extension loader and hash checks.
- `run_integration_025.py`: reproduce one selected policy/scenario.
- `run_compat_matrix_025.py`: eight governance/social/extraction variations with paired seeds.
- `examples/scenarios/`: three valid JSON examples.
- `examples/extensions/`: reviewed-local-plugin example.
- `tests/test_integration_025.py`: 15 integration tests.
- `docs/INTEGRATION_025/DEVLOG_SOCIAL_WORLD.docx`: complete Social and World development log; editable Word.
- `docs/INTEGRATION_025/DEVLOG_SOCIAL_WORLD.md`: source-readable change history.
- `docs/INTEGRATION_025/README.md`: detailed setup and extension API.
- `docs/INTEGRATION_025/COMPATIBILITY_MATRIX.md`: actual compatibility boundaries.
- `results/integration_025/matrix.csv`: short 16-scenario compatibility check data.

## Start here

1. Extract archive.
2. Enter `Founders_CIV_v020_Soul_Ecology_Pilot`.
3. Run `RUN_COMPAT_025_TESTS.bat` on Windows, or the Python commands below.

```bash
python -m unittest discover -s tests -q
python -m unittest discover -s . -p 'test*.py' -q
python run_integration_025.py examples/scenarios/commons.json --check-hashes --out results/integration_025/commons.json
python run_compat_matrix_025.py --seeds 820 821 --cycles 4
```

**Caution:** This is an extension-and-compatibility release, not a new claim of ecological sustainability or emergent consciousness. Worlds can fail naturally. Custom third-party Python extensions are trusted local code, not sandboxed. Full-state saving and mutating third-party plugin actions are not yet supported.

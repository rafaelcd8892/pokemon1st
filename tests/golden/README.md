# Golden logs

These JSON files are **snapshots** of battle output used for regression detection.
If a PR changes these files, that is a breaking change unless explicitly approved.

## Rules
- Always run golden verification before merging (`python scripts/run_golden.py`).
- Baselines are generated with a fixed seed and stored **normalized** (no timestamps or battle IDs).
- After an intentional engine change, update baselines with `python scripts/run_golden.py --update` and commit them.

## Naming convention
`<scenario_name>__seed_<N>.json`

Example: `charizard_vs_blastoise__seed_42.json`

## Workflow
```bash
python scripts/run_golden.py --generate   # create baselines for new scenarios
python scripts/run_golden.py              # verify — should show all PASS
python scripts/run_golden.py --update     # approve new engine output
pytest tests/test_golden.py -v            # same checks via pytest
```

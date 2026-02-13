# Tests

## Test types
- **Unit tests** — mechanics functions (damage, crit, accuracy, status)
- **Integration tests** — short simulated battles
- **Golden tests** — exact battle-log snapshots for regression detection

## Commands
```bash
pytest -q                              # run all tests
pytest tests/test_golden.py -v         # run golden tests only
python scripts/run_golden.py           # verify golden baselines (standalone)
python scripts/run_golden.py --generate  # create missing baselines
python scripts/run_golden.py --update    # regenerate all baselines
```

## Golden test workflow

1. **Create a scenario** — add a JSON file to `tests/scenarios/` defining teams, seed, and format.
2. **Generate the baseline** — `python scripts/run_golden.py --generate` runs the scenario and saves the normalized log to `tests/golden/<name>__seed_<N>.json`.
3. **Verify** — `python scripts/run_golden.py` (or `pytest tests/test_golden.py`) replays every scenario and diffs the output against the stored baseline.
4. **Update after intentional changes** — when the engine changes behaviour on purpose, run `python scripts/run_golden.py --update` and commit the new baselines.

### Scenario format
```json
{
  "name": "charizard_vs_blastoise",
  "description": "Fire vs Water type matchup",
  "seed": 42,
  "format": "1v1",
  "team1": {
    "name": "Red",
    "pokemon": [
      {"species": "charizard", "level": 50, "moves": ["flamethrower", "slash", "earthquake", "dragon-rage"]}
    ]
  },
  "team2": { "..." : "..." }
}
```

### Naming convention
Golden baselines: `<scenario_name>__seed_<N>.json`
Example: `charizard_vs_blastoise__seed_42.json`

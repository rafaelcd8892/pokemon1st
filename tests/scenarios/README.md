# Scenarios

Scenario definitions used by integration/golden tests.

Each scenario should specify:
- Pokémon on each side (species, level, stats if overridden)
- Movesets (PP optional)
- Starting conditions (status, stat boosts, screens)
- Seed
- Optional scripted move choices (if AI isn't deterministic)

Goal: scenarios should be small, deterministic, and cover tricky mechanics.
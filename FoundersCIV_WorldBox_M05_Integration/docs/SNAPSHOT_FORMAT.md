# Normalized snapshots — exact supported M05 input

WorldBox M02's raw snapshot files were **not** available in the provided materials. The following format is an **intermediate exchange contract**, not an assertion about M02 source structure. Do not invent unknown identity markers, parents or species: omit them or set `null` in source conversion.

```json
{
  "schema": "founders-native-snapshot-1",
  "world_key": "house-save-2026-11-13-test1",
  "capture_id": "before",
  "session_id": "session1",
  "native_tick": 71236,
  "actors": [
    {
      "id": "12345",
      "species": "wolf",
      "generation": 3,
      "creation_marker": "native",
      "parent_1": "10001",
      "parent_2": "10002"
    }
  ]
}
```

- `world_key` must match the M05 state and the save being studied.
- `capture_id` must be unique for the save. Reusing the capture ID with conflicting data is rejected.
- IDs can be integers or strings; they are normalized to strings and are unique per capture.
- Species, generation, creation marker and parent fields are used to **check continuity only**. They do not establish which observed actors died or were newly born.
- `native_tick` is observational metadata: a lower value after reload is possible. It cannot define a global age or chronology.
- Actor list has a safety maximum of 500,000 entries and no fixed 5,000 limit.
- A real M02 converter should be written against an actual raw snapshot and unit-tested for all naming/identity conversions before importing production data.

The M05 regression test reconstructs **synthetic** snapshots of 2,293 and 4,900 actors sharing 559 unchanged IDs, with 1,734 earlier-only and 4,341 later-only. This checks comparison arithmetic; it is not a fresh inspection of your actual two WorldBox captures.

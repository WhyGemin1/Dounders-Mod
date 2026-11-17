# v0.19 experimental validation

K-01: 8 matched seeds × 5 channels × 100 v0.18 Founder actors × 80 ticks. Actor-specific exposure, recall, understanding, confidence, practice and application recorded. One seed of event-level traces retained. Results in `k01_results/summary.json` and CSV files.

TR-01: 12 seeds × 4 conditions × 100 actor cognition states × 20 reports. Source truthfulness and verification are controlled; trust updates use evidence counters. Results in `tr01_results/summary.json` and CSV files.

The original v0.18 tests (46) plus six new architecture invariants (52 total) pass. These are model consistency tests, **not human validation**. K-01 saturates recall and understanding in four of five channels, making those outcomes insufficiently discriminative. Source reliability and message fidelity are programmed, not emergent. Trust calibration outcomes are consequences of assumed verification frequency and error rate. Future work: shorten exposure, test forgetting and noise, compare alternative learning equations, and integrate artifacts/communication with physical constraints.

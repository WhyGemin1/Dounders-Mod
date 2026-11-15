# Core151 Book consolidation contract — not yet satisfied

M05's SQLite ledger is an **isolated virtual Book for M05 experiments**, NOT an implementation inside the existing Core151 Book. The original Core151 source, account/transaction schema, evolution of WORLD-023/024, actual event scheduler and M01/M02 bridge files were not in the files available for this build. Do not deploy two writers for the same resource asset or pretend the M05 export is a completed integration.

## Required before promotion

1. **Obtain and inspect the actual Core151 authoritative Book source and existing resource account identities.** Avoid new shadow balances for any existing BIO-like resource.
2. **Map types safely.** `bio_equiv` is an illustrative producer/consumer accounting unit, not joules or WorldBox nutrition. `creation_charge` is fictional river potential. No conversion factor is assumed; the assets must have explicitly approved semantics.
3. **Write a single Book adapter** supporting atomic `transfer_many(tx_id, [(asset,from,to,amount),...])`, balance readback, canonical serialized journal, and consistent transaction IDs across restarts. Tests must prove conflicting replay is rejected and partial multi-asset transfers roll back.
4. **Migrate authority, don't clone it.** On a specific migration checkpoint: pause virtual writes; capture journal SHA, balances, complete unspent fruit inventory and Creation states; translate the transactions into Core151 using a one-time migration ID; verify balances; mark M05 ledger **read-only after promotion**. Never keep two active writable versions of a resource account.
5. **Bind World Trees to WORLD-023/024** and their four actual habitat IDs rather than creating synthetic replacements. Keep existing Founder identities, Creation Seed ownership and river/pool rules.
6. **Preserve WorldBox native authority** until verified real source matter/quantity, native callback semantics, durable ACK/replay, and a decision about which engine writes each native effect. Nested `resource_consume_call` and `nutrition_call` must not become independent duplicate food transfers.
7. **Test game behavior** on a copied save: patched vs. unpatched matched scenarios, hook cost at 4,900+ actors, identity continuity after reload, predation and reproduction classification, juvenile feeding and Tree health. Run 30/180/360/720/1080 horizon comparisons where feasible. Fail closed on drift and failed conservation audits.

## Review artifact

`py m05.py --db data\house.sqlite export-core151-review --output results\core151_review.json` produces a complete chronological **review-only** transaction list and a source fingerprint. It must not be automatically ingested into Core151 without a carefully implemented migration step. It does not provide authorization to change WorldBox actors.

## Why the boundary matters

A game animal eating is a WorldBox native event. An M05 virtual Founder feeding from its *own* virtual Tree's modeled resource pool is a different event. Until there is an experimentally validated material identity connecting those two events, debiting both would double-count food, while crediting both would create energy. Similarly, a funded M05 world seed is a planned object, not a WorldBox map alteration.

#!/usr/bin/env python3
"""List virtual fruit in the M05 SQLite Book. No state changes."""
import argparse,sqlite3,json
p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--all',action='store_true')
a=p.parse_args();db=sqlite3.connect(a.db);db.row_factory=sqlite3.Row
q='SELECT fruit_id,tree_id,born_period,bio,ce,status,founder_id FROM fruits'
if not a.all:q+=" WHERE status='on_tree'"
q+=' ORDER BY born_period,fruit_id'
print(json.dumps([dict(x) for x in db.execute(q)],indent=2))
db.close()

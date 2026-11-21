import json,sys
from pathlib import Path
from factorial_021126 import configuration
from factorial_021128 import run_verified
folder=Path(sys.argv[1]);cfg=configuration(9711,density=8,capacity=.5,family=True,memory=True,funded=False)
records=run_verified(cfg,[30,60],folder)
print(json.dumps(records,default=str))

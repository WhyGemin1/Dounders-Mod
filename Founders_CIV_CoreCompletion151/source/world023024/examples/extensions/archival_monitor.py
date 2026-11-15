"""Example custom plug-in. Import this locally after reviewing the code.
The extension observes events only; it does not change simulation physics.
"""
from founders_civ.integration import Extension,API_VERSION
class ArchiveMonitor(Extension):
    id='archive_monitor'
    api_version=API_VERSION
    def __init__(self):self.records=[]
    def on_event(self,e):
        if e.action in ('seed_drafted','seed_researched','seed_validated','seed_planted','creation_collapsed'):
            self.records.append({'cycle':e.cycle,'event_key':e.event_key,'action':e.action})
    def report(self):return {'seed_lifecycle_events':self.records}

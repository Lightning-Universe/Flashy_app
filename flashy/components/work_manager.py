import uuid
from typing import Dict

from lightning import LightningFlow


class WorkManager(LightningFlow):
    def __init__(self, groups):
        super().__init__()

        self.groups = groups

        # Maps collection name -> work name -> work attribute
        self.managed_works: Dict[str, Dict[str, str]] = {}

        self.reset()

    def reset(self):
        """Stop all works owned by this ``WorkManager`` and clear the layout."""
        for work_name, work in self.named_works():
            # TODO: Add a method in the base ``LightningFlow`` to stop **and** remove a work
            work.stop()

            # TODO: Figure out why the work can't be removed this way
            # delattr(self, work_name)
            # self._works.remove(work_name)

        self.managed_works = {group: {} for group in self.groups}

    def register_work(self, group, work_name, work):
        # TODO: Use a full UUID when restrictions on work names are lifted
        work_attribute = uuid.uuid4().hex[:8]
        if group not in self.managed_works:
            self.managed_works[group] = {}
        self.managed_works[group][str(work_name)] = work_attribute
        setattr(self, work_attribute, work)

    def get_work(self, group, work_name):
        work_name = str(work_name)
        if group in self.managed_works and work_name in self.managed_works[group]:
            return getattr(self, self.managed_works[group][work_name], None)
        return None

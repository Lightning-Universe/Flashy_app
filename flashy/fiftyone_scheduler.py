import logging
from typing import Any, Dict

from lightning import LightningFlow
from lightning.storage.path import Path

from flashy.components.flash_fiftyone import FlashFiftyOne


class FiftyOneScheduler(LightningFlow):
    def __init__(self):
        super().__init__()

        self.work = FlashFiftyOne()

        self.run_id = None
        self.ready = False

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self.ready = False

        if run["id"] != self.run_id:
            logging.info(
                f"Launching FiftyOne with path: {checkpoint}, of type: {type(checkpoint)}"
            )
            self.run_id = run["id"]
            self.work.run(run["task"], run["url"], run["data_config"], checkpoint)

        if self.work.has_succeeded:
            self.ready = True

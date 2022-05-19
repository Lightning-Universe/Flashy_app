import logging
from typing import Any, Dict

from lightning import LightningFlow
from lightning.storage.path import Path
from flashy.components.flash_gradio import FlashGradio


class GradioScheduler(LightningFlow):
    def __init__(self):
        super().__init__()

        self.work = FlashGradio()

        self.run_id = None
        self.ready = False

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self.ready = False

        if run["id"] != self.run_id:
            logging.info(
                "Launching gradio with path: {checkpoint}, of type: {type(checkpoint)}"
            )
            self.run_id = run["id"]
            self.work.run(run["task"], run["url"], run["data_config"], checkpoint)

        if self.work.launched:
            self.ready = True

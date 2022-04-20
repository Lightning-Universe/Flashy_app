import logging
import os
from typing import Any, Dict

import torch
from flash.core.integrations.fiftyone import visualize
from lightning import LightningFlow
from lightning.components.python import TracerPythonScript
from lightning.storage.path import Path

from flashy.run_scheduler import _generate_script


class FiftyOneTemplateTracer(TracerPythonScript):
    def __init__(self):
        super().__init__(__file__, blocking=True, run_once=False, exposed_ports={"fiftyone": 5151})

        self._session = None

    def run(self, run: Dict[str, Any], checkpoint: str):
        self.script_path = _generate_script(
            ".", run, f"{run['task']}_fiftyone.jinja", checkpoint=checkpoint
        )
        super().run()

    def on_after_run(self, res):
        logging.info("Launching FiftyOne")

        if self._session is not None:
            self._session.close()

        predictions = res["predictions"]

        self._session = visualize(predictions, wait=False, remote=True)

        logging.info("Launched")


class FiftyOneScheduler(LightningFlow):
    def __init__(self):
        super().__init__()

        self.work = FiftyOneTemplateTracer()

        self.run_id = None
        self.ready = False

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self.ready = False

        if run["id"] != self.run_id:
            self.run_id = run["id"]
            self.work.run(run, checkpoint)

        if self.work.has_succeeded:
            self.ready = True

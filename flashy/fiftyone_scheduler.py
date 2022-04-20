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
        super().__init__(__file__, blocking=False, exposed_ports={"fiftyone": 5151})

        self._session = None

    def run(self, run: Dict[str, Any], checkpoint: str):
        self.script_path = _generate_script(
            ".", run, f"{run['task']}_fiftyone.jinja", checkpoint=checkpoint
        )
        super().run()

    def on_after_run(self, res):
        predictions_path = os.path.join(".", f"{self.run_dict['id']}_predictions.pt")

        if self._session is not None:
            self._session.close()
        predictions = torch.load(predictions_path)

        self._session = visualize(predictions, wait=False, remote=True)


class FiftyOneScheduler(LightningFlow):
    def __init__(self):
        super().__init__()

        self.work = FiftyOneTemplateTracer()

        self.run_id = None

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self.run_id = run["id"]
        self.work.run(run, checkpoint)

import torch
from typing import Any, Dict
import os

from flash.core.integrations.fiftyone import visualize

import os
import sys

sys.path.append(os.path.dirname(__file__))

from run_scheduler import _generate_script
from lightning import LightningFlow, LightningWork
from lightning.components.python import TracerPythonScript


class FiftyOneLauncher(LightningWork):

    def __init__(self):
        super().__init__(blocking=True, exposed_ports={"fiftyone": 5151})
        self._session = None

    def run(self, predictions_path: str, root: str):
        if self._session is not None:
            self._session.close()
        predictions = torch.load(predictions_path)

        os.chdir(root)
        self._session = visualize(predictions, wait=False, remote=True)


class FiftyOneTemplateTracer(TracerPythonScript):

    def __init__(self):
        super().__init__(__file__, blocking=True)

    def run(self, run: Dict[str, Any], checkpoint: str, script_dir: str):
        self.script_path = _generate_script(script_dir, run, f"{run['task']}_fiftyone.jinja", checkpoint=checkpoint)
        super().run()


class FiftyOneScheduler(LightningFlow):

    def __init__(self):
        super().__init__()

        self.run_work = FiftyOneTemplateTracer()
        self.fiftyone_work = FiftyOneLauncher()

        self.script_dir = None
        self.run_id = None
        self.done = False

    def run(self, run: Dict[str, Any], checkpoint: str):
        self.done = False
        # os.system(f"kill -9 $(ps -A | grep {self.run_work.script_path} " + "| awk '{print $1}')")
        self.run_id = run["id"]
        self.run_work.run(run, checkpoint, self.script_dir)

        predictions_path = os.path.join(self.script_dir, f"{run['id']}_predictions.pt")
        if os.path.exists(predictions_path) and self.run_work.has_succeeded:
            self.fiftyone_work.run(predictions_path, self.script_dir)
        self.done = True

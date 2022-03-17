import tempfile
import torch
from typing import Any, Dict
import os

from flash.core.integrations.fiftyone import visualize

from flashy.run_scheduler import _generate_script
from lightning import LightningFlow, LightningWork
from lightning.components.python import TracerPythonScript


# TODO: This should be a private member of the FiftyOneScheduler once support is added
session = None


class FiftyOneLauncher(LightningWork):

    def __init__(self):
        super().__init__(blocking=True)

    def run(self, predictions_path: str, root: str):
        global session
        if session is not None:
            session.close()
        predictions = torch.load(predictions_path)

        os.chdir(root)
        session = visualize(predictions, wait=False, remote=True)


class FiftyOneTemplateTracer(TracerPythonScript):

    def __init__(self):
        super().__init__(__file__, blocking=True)

    def run(self, run: Dict[str, Any], checkpoint: str, script_dir: str):
        _generate_script(script_dir, run, f"{run['task']}_fiftyone.jinja", checkpoint=checkpoint)
        self.script_path = str(os.path.join(script_dir, f"{run['id']}_{run['task']}_fiftyone.py"))
        super().run()


class FiftyOneScheduler(LightningFlow):

    def __init__(self):
        super().__init__()

        self.run_work = FiftyOneTemplateTracer()
        self.launcher_work = FiftyOneLauncher()

        self.script_dir = tempfile.mkdtemp()

        self.run_id = None

        self.done = False

    def run(self, run: Dict[str, Any], checkpoint: str):
        self.done = False
        # os.system(f"kill -9 $(ps -A | grep {self.run_work.script_path} " + "| awk '{print $1}')")
        self.run_id = run["id"]
        self.run_work.run(run, checkpoint, self.script_dir)

        predictions_path = os.path.join(self.script_dir, f"{run['id']}_predictions.pt")
        if os.path.exists(predictions_path) and self.run_work.has_completed:
            self.launcher_work.run(predictions_path, self.script_dir)
        self.done = True

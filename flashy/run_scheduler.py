from typing import Any, Dict, List, Optional
import os.path

from flash.core.data.utils import download_data
from jinja2 import Environment, FileSystemLoader

from lightning import LightningFlow, LightningWork
from lightning.storage.path import Path
from lightning.components.python import TracerPythonScript

import os
import sys

sys.path.append(os.path.dirname(__file__))

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))


def _generate_script(script_dir, run: Dict[str, Any], template_file, **kwargs) -> str:
    template = env.get_template(os.path.join(template_file))

    variables = {
        "root": script_dir,
        "run_id": run["id"],
        "url": run["url"],
        "method": run['method'],
        "data_config": run['data_config'],
        "model_config": run['model_config'],
        **kwargs
    }

    generated_script = os.path.join(script_dir, f"{run['id']}_{template_file.replace('jinja', 'py')}")
    with open(generated_script, "w") as f:
        f.write(template.render(**variables))

    return generated_script


class RunGeneratedScript(TracerPythonScript):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, raise_exception=True, **kwargs)
        self.script_dir = None
        self.run_dict = None
        self.best_model_path: Optional[Path] = None
        self.monitor = None

    def run(self, script_dir: str, run_dict: Dict[str, str]):
        self.script_dir = script_dir
        self.run_dict = run_dict
        self.script_path = _generate_script(script_dir, run_dict, f"{run_dict['task']}.jinja", rendering=False)
        super().run()

    def on_after_run(self, res):
        self.monitor = float(res['trainer'].callback_metrics["val_accuracy"].item())
        self.best_model_path = Path(os.path.join(self.script_dir, f"{self.run_dict['id']}.pt"))

class RunScheduler(LightningFlow):

    def __init__(self):
        super().__init__()

        for idx in range(10):
            run_work = RunGeneratedScript(__file__)
            setattr(self, f"run_work_{idx}", run_work)

        self.script_dir = None
        self.queued_runs: Optional[List[Dict[str, Any]]] = None
        self.running_runs = None

    def run(self):
        if self.queued_runs:
            for run in self.queued_runs:
                run_work = getattr(self, f"run_work_{run['id']}")
                run_work.run(self.script_dir, run)
            self.running_runs = self.queued_runs
            self.queued_runs = None

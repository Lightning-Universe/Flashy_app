import functools
import os
import os.path
from typing import Any, Dict, List, Optional
import logging

from jinja2 import Environment, FileSystemLoader
from lightning import LightningFlow
from lightning.components.python import TracerPythonScript
from lightning.storage.path import Path


@functools.lru_cache
def _get_env():
    return Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates"))
    )


def _generate_script(script_dir, run: Dict[str, Any], template_file, **kwargs) -> str:
    template = _get_env().get_template(os.path.join(template_file))

    variables = {
        "root": script_dir,
        "run_id": run["id"],
        "url": run["url"],
        "method": run["method"],
        "data_config": run["data_config"],
        "model_config": run["model_config"],
        **kwargs,
    }

    generated_script = os.path.join(
        script_dir, f"{run['id']}_{template_file.replace('jinja', 'py')}"
    )
    with open(generated_script, "w") as f:
        logging.info(f"Rendering {template_file} with variables: {variables}")
        f.write(template.render(**variables))

    return generated_script


class RunGeneratedScript(TracerPythonScript):
    def __init__(self, **kwargs):
        super().__init__(__file__, blocking=False, raise_exception=True, **kwargs)
        self.script_dir = None
        self.run_dict = None
        self.best_model_path: Optional[Path] = None
        self.monitor = None

    def run(self, script_dir: str, run_dict: Dict[str, str]):
        self.script_dir = script_dir
        self.run_dict = run_dict
        print(f"Generating script in: {script_dir}")
        self.script_path = _generate_script(
            script_dir, run_dict, f"{run_dict['task']}.jinja", rendering=False
        )
        print(f"Running script: {self.script_path}")
        super().run()

    def on_after_run(self, res):
        self.monitor = float(res["trainer"].callback_metrics["val_accuracy"].item())
        self.best_model_path = Path(
            os.path.join(self.script_dir, f"{self.run_dict['id']}.pt")
        )
        logging.info(f"Stored best model path: {self.best_model_path}")


class RunScheduler(LightningFlow):
    def run(self, queued_runs: Optional[List[Dict[str, Any]]]):
        logging.info(f"Queued runs: {queued_runs}")
        for run in queued_runs:
            run_work = RunGeneratedScript()
            setattr(self, f"work_{run['id']}", run_work)
            logging.info(f"Launching run: {run['id']}. Run work `run` method: {run_work.run}.")
            run_work.run(".", run)

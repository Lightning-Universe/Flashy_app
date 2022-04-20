import functools
import os
import os.path
from typing import Any, Dict, List, Optional
import logging

from jinja2 import Environment, FileSystemLoader
from lightning import LightningFlow, LightningWork
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


# class RunGeneratedScript(TracerPythonScript):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, raise_exception=True, **kwargs)
#         self.script_dir = None
#         self.run_dict = None
#         self.best_model_path: Optional[Path] = None
#         self.monitor = None
#
#     def run(self, script_dir: str, run_dict: Dict[str, str]):
#         self.script_dir = script_dir
#         self.run_dict = run_dict
#         print(f"Generating script in: {script_dir}")
#         self.script_path = _generate_script(
#             script_dir, run_dict, f"{run_dict['task']}.jinja", rendering=False
#         )
#         print(f"Running script: {self.script_path}")
#         super().run()
#
#     def on_after_run(self, res):
#         self.monitor = float(res["trainer"].callback_metrics["val_accuracy"].item())
#         self.best_model_path = Path(
#             os.path.join(self.script_dir, f"{self.run_dict['id']}.pt")
#         )


class MyTestWork(LightningWork):

    def __init__(self):
        super().__init__(blocking=False)

        self.monitor = None

    def run(self, script_dir: str, run_dict: Dict[str, str]):
        self.monitor = script_dir


class RunScheduler(LightningFlow):
    def __init__(self):
        super().__init__()

        self.run_work_0 = MyTestWork()  # RunGeneratedScript(__file__)

        # for idx in range(10):
        #     run_work = RunGeneratedScript(__file__)
        #     setattr(self, f"run_work_{idx}", run_work)

        # self.script_dir = None
        # self.running_runs = None

    def run(self, queued_runs: Optional[List[Dict[str, Any]]]):
        logging.info(f"Queued runs: {queued_runs}")
        for run in queued_runs:
            run_work = getattr(self, f"run_work_{run['id']}")
            logging.info(f"Launching run: {run['id']}. Run work `run` method: {run_work.run}.")
            run_work.run(".", run)
        # self.running_runs = queued_runs

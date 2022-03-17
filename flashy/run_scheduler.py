import tempfile
from typing import Any, Dict, List
import os.path
from jinja2 import Environment, FileSystemLoader

from lightning import LightningFlow
from lightning.components.python import TracerPythonScript

import flashy

env = Environment(loader=FileSystemLoader(flashy.TEMPLATES_ROOT))


def _generate_script(script_dir, run: Dict[str, Any], template_file, **kwargs):
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

    with open(os.path.join(script_dir, f"{run['id']}_{template_file.replace('jinja', 'py')}"), "w") as f:
        f.write(template.render(**variables))


class RunScheduler(LightningFlow):

    def __init__(self):
        super().__init__()

        for idx in range(10):
            run_work = TracerPythonScript(__file__)
            setattr(self, f"run_work_{idx}", run_work)

        self.script_dir = tempfile.mkdtemp()

    def run(self, runs: List[Dict[str, Any]]):
        for run in runs:
            _generate_script(self.script_dir, run, f"{run['task']}.jinja", rendering=False)
            # _generate_script(self.script_dir, run, f"{run['task']}_rendered.py", rendering=True)
            run_work = getattr(self, f"run_work_{run['id']}")
            run_work.script_path = str(os.path.join(self.script_dir, f"{run['id']}_{run['task']}.py"))
            run_work.run()

import tempfile
from typing import Any, Dict, List, Optional
import os.path

from flash.core.data.utils import download_data
from jinja2 import Environment, FileSystemLoader

from lightning import LightningFlow, LightningWork
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


class DataDownloader(LightningWork):

    def __init__(self):
        super().__init__(blocking=False)

        self.done = False

    def run(self, root, url):
        self.done = False
        download_data(url, root)
        self.done = True


class RunScheduler(LightningFlow):

    def __init__(self):
        super().__init__()

        for idx in range(10):
            run_work = TracerPythonScript(__file__)
            setattr(self, f"run_work_{idx}", run_work)

        self.data_downloader = DataDownloader()

        self.script_dir = tempfile.mkdtemp()

        self.queued_runs: Optional[List[Dict[str, Any]]] = None
        self.running_runs = None

    def run(self):
        if self.queued_runs:
            self.data_downloader.run(self.script_dir, self.queued_runs[0]["url"])

        if self.queued_runs and self.data_downloader.done:
            for run in self.queued_runs:
                _generate_script(self.script_dir, run, f"{run['task']}.jinja", rendering=False)
                run_work = getattr(self, f"run_work_{run['id']}")
                run_work.script_path = str(os.path.join(self.script_dir, f"{run['id']}_{run['task']}.py"))
                run_work.run()
            self.running_runs = self.queued_runs
            self.queued_runs = None

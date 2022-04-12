import tempfile
import subprocess
import os

if bool(int(os.getenv("INSTALL", '1'))):
    # FIXME: Install flashy as setup.py doesn't work in the cloud.
    with subprocess.Popen(
        "pip install -e .".split(' '), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0, close_fds=True
    ) as proc:
        proc.wait()

from flashy.data_manager import DataManager
from flashy.hpo_manager import HPOManager
from flashy.task_selector import TaskSelector
from lightning import LightningApp, LightningFlow


class Flashy(LightningFlow):
    """The root flow for the `Flashy` app."""

    def __init__(self):
        super().__init__()

        self.script_dir = tempfile.mkdtemp()
        self.task_selector: LightningFlow = TaskSelector()
        self.data_manager: LightningFlow = DataManager()
        self.hpo_manager: LightningFlow = HPOManager()

        self.hpo_manager.run_scheduler.script_dir = self.script_dir
        self.hpo_manager.fiftyone_scheduler.script_dir = self.script_dir

    def run(self):
        self.task_selector.run()

        if self.task_selector.selected_task is not None:
            selected_task = self.task_selector.selected_task
            self.data_manager.run(selected_task)

            if self.data_manager.config is not None:
                self.hpo_manager.run(
                    self.data_manager.selected_task,
                    self.data_manager.url,
                    self.data_manager.method,
                    self.data_manager.config,
                )

    def configure_layout(self):
        return [
            {"name": "Task", "content": self.task_selector},
            {"name": "Data", "content": self.data_manager},
            {"name": "Model", "content": self.hpo_manager},
            {"name": "Data Explorer", "content": self.hpo_manager.exposed_url("fiftyone")},
            # {"name": "Swagger UI", "content": "http://127.0.0.1:8000/docs"},
            # {"name": "Demo", "content": self.demo_ui},
        ]


app = LightningApp(Flashy())

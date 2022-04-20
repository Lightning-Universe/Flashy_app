import os
import sys

sys.path.append(os.path.dirname(__file__))

from lightning import LightningApp, LightningFlow

from flashy.data_manager import DataManager
from flashy.task_selector import TaskSelector
from flashy.hpo_manager import HPOManager


class Flashy(LightningFlow):
    """The root flow for the `Flashy` app."""

    def __init__(self):
        super().__init__()

        # self.script_dir = tempfile.mkdtemp()
        self.task_selector: LightningFlow = TaskSelector()
        self.data: LightningFlow = DataManager()
        self.hpo: LightningFlow = HPOManager()
        #
        # self.hpo_manager.run_scheduler.script_dir = self.script_dir
        # self.hpo_manager.fiftyone_scheduler.script_dir = self.script_dir

    def run(self):
        self.task_selector.run()

        if self.task_selector.selected_task is not None:
            selected_task = self.task_selector.selected_task
            self.data.run(selected_task)

            if self.data.config is not None:
                self.hpo.run(
                    self.data.selected_task,
                    self.data.url,
                    self.data.method,
                    self.data.config,
                )

    def configure_layout(self):
        return [
            {"name": "Task", "content": self.task_selector},
            {"name": "Data", "content": self.data},
            {"name": "Model", "content": self.hpo},
            # {
            #     "name": "Data Explorer",
            #     "content": self.hpo_manager.exposed_url("fiftyone"),
            # },
        ]


app = LightningApp(Flashy(), debug=True)

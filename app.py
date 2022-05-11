import os
import sys

sys.path.append(os.path.dirname(__file__))

from lightning import LightningApp, LightningFlow  # noqa: E402

from flashy.data_manager import DataManager  # noqa: E402
from flashy.hpo_manager import HPOManager  # noqa: E402
from flashy.task_selector import TaskSelector  # noqa: E402


class Flashy(LightningFlow):
    """The root flow for the `Flashy` app."""

    def __init__(self):
        super().__init__()

        self.task_selector: LightningFlow = TaskSelector()
        self.data: LightningFlow = DataManager()
        self.hpo: LightningFlow = HPOManager()

    def run(self):
        self.task_selector.run()

        if self.task_selector.selected_task is not None:
            selected_task = self.task_selector.selected_task
            self.data.run(selected_task, self.task_selector.defaults)

            if self.data.config:
                self.hpo.run(
                    selected_task,
                    self.data.config,
                )

    def configure_layout(self):
        data_explorer_url = self.hpo.exposed_url()
        if not self.hpo.fo.ready:
            data_explorer_url = "https://pl-flash-data.s3.amazonaws.com/assets_lightning/large_spinner.gif"

        return [
            {"name": "Task", "content": self.task_selector},
            {"name": "Data", "content": self.data},
            {"name": "Model", "content": self.hpo},
            {
                "name": "Data Explorer",
                "content": data_explorer_url,
            },
        ]


app = LightningApp(Flashy(), debug=True)

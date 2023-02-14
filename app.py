import os
import sys

sys.path.append(os.path.dirname(__file__))

import lightning as L
from lightning.app.frontend import StaticWebFrontend  # noqa: E402
from lightning.app.storage import Drive  # noqa: E402

from flashy.components.file_server import FileServer  # noqa: E402
from flashy.hpo_manager import HPOManager  # noqa: E402


class ReactUI(L.LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(os.path.join(os.path.dirname(__file__), "flashy", "ui", "build"))


class Flashy(L.LightningFlow):
    """The root flow for the `Flashy` app."""

    def __init__(self):
        super().__init__()

        self.datasets = Drive("lit://datasets")
        self.checkpoints = Drive("lit://checkpoints", allow_duplicates=True)

        self.ui = ReactUI()
        self.hpo = HPOManager(self.datasets, self.checkpoints)

        self.file_upload = FileServer(self.datasets, cache_calls=True, parallel=True)
        self.file_upload_url: str = ""

        self.checkpoints_server = FileServer(self.checkpoints, cache_calls=True, parallel=True)
        self.checkpoints_server_url: str = ""

    @property
    def ready(self):
        return self.file_upload.ready and self.checkpoints_server.ready

    def run(self):
        self.file_upload_url = self.file_upload.url
        self.file_upload.run()

        self.checkpoints_server_url = self.checkpoints_server.url
        self.checkpoints_server.run()

        self.hpo.run()

    def configure_layout(self):
        return [
            {"name": "Flashy", "content": self.ui},
        ]


app = L.LightningApp(Flashy())

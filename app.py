import os
import sys

from lightning.storage import Path

sys.path.append(os.path.dirname(__file__))

from lightning import LightningApp, LightningFlow  # noqa: E402
from lightning.frontend import StaticWebFrontend  # noqa: E402

from flashy.components.file_server import FileServer  # noqa: E402
from flashy.hpo_manager import HPOManager  # noqa: E402


class ReactUI(LightningFlow):
    def configure_layout(self):
        return StaticWebFrontend(
            os.path.join(os.path.dirname(__file__), "flashy", "ui", "build")
        )


class Flashy(LightningFlow):
    """The root flow for the `Flashy` app."""

    def __init__(self):
        super().__init__()

        self.ui = ReactUI()
        self.hpo = HPOManager()

        self.file_upload = FileServer("uploaded_data", run_once=True, parallel=True)
        self.file_upload_url: str = ""

    def run(self):
        self.file_upload_url = self.file_upload.url
        self.file_upload.run()

        root = Path(self.file_upload.root)
        root._attach_work(self.file_upload)
        self.hpo.run(root)

    def configure_layout(self):

        layout = [
            {"name": "Flashy", "content": self.ui},
            # {"name": "Results", "content": self.hpo},
        ]

        return layout + self.hpo.dm.layout


app = LightningApp(Flashy(), debug=False)

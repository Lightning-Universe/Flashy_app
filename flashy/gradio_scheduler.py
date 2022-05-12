import logging
import os
from typing import Any, Dict, List

from lightning.components.python import TracerPythonScript
from lightning.storage.path import Path

import gradio as gr

    
class GradioTemplateTracer(TracerPythonScript):
    def __init__(self):
        self.por = 5151
        super().__init__(
            __file__,
            blocking=True,
            run_once=False,
            port=self.port
        )

        self._instance = None
        self._input_text = None
        self._checkpoint = None

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self._checkpoint = checkpoint
        self._instance = self.gradio_interface(address="0.0.0.0", port=self.port)

    def gradio_interface(self, address: str, port: int):
        demo = gr.Interface(fn=self._apply, inputs="text", outputs="text")
        demo.launch(server_name=address, server_port=port)

    def _apply(self, text):
        self._input_text = text
        self.script_path = _generate_script(
            ".", run, f"{run['task']}_gradio.jinja", checkpoint=str(self._checkpoint), text_input=text
        )
        super().run()
        return res['predictions']

    # def on_after_run(self, res):
    #     logging.info("Launching Gradio")
    #
    #     # if self._instance is not None:
    #     # self._instance.close()

class GradioScheduler(LightningFlow):
    def __init__(self):
        super().__init__()

        self.work = GradioTemplateTracer()

        self.run_id = None
        self.ready = False

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self.ready = False

        if run["id"] != self.run_id:
            logging.info("Launching gradio with path: {checkpoint}, of type: {type(checkpoint)}")
            self.run_id = run["id"]
            self.work.run(run, checkpoint)

        if self.work.has_succeeded:
            self.ready = True

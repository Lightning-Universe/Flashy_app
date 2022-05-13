import logging
import os
from typing import Any, Dict

import gradio as gr
from lightning import LightningFlow
from lightning.components.python import TracerPythonScript
from lightning.storage.path import Path

from flashy.run_scheduler import _generate_script


class GradioTemplateTracer(TracerPythonScript):
    def __init__(self):
        super().__init__(__file__, blocking=True, run_once=False, port=5151)

        self._instance = None
        self._input_text = None
        self._checkpoint = None
        self._run = None
        self.demo = None

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self._checkpoint = checkpoint
        self._run = run

    def on_after_run(self, res):
        demo = gr.Interface(fn=self._apply, inputs="text", outputs="text")
        demo.launch(server_name="0.0.0.0", server_port=5151)

    def _apply(self, text):
        self._input_text = text
        self.script_path = _generate_script(
            ".",
            self._run,
            f"{self._run['task']}_gradio.jinja",
            checkpoint=str(self._checkpoint),
            text_input=text,
        )
        env_copy = os.environ.copy()
        if self.env:
            os.environ.update(self.env)
        res = super()._run_tracer()
        os.environ = env_copy
        return res["predictions"]


class GradioScheduler(LightningFlow):
    def __init__(self):
        super().__init__()

        self.work = GradioTemplateTracer()

        self.run_id = None
        self.ready = False

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self.ready = False

        if run["id"] != self.run_id:
            logging.info(
                "Launching gradio with path: {checkpoint}, of type: {type(checkpoint)}"
            )
            self.run_id = run["id"]
            self.work.run(run, checkpoint)

        if self.work.has_succeeded:
            self.ready = True

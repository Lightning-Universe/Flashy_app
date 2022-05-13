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
        super().__init__(__file__, blocking=True, run_once=True, port=5151)

        self._checkpoint = None
        self.share_url = None

    def run(self, run: Dict[str, Any], checkpoint: Path):
        self._checkpoint = checkpoint
        self.script_path = _generate_script(
            ".",
            run,
            f"{run['task']}_gradio.jinja",
            checkpoint=str(self._checkpoint),
        )
        super().run()

    def on_after_run(self, res):
        sample_input = (
            "Turgid dialogue, feeble characterization - Harvey Keitel a judge?. "
        )
        +"\n The worst movie in the history of cinema. \n"
        +"I come from Bulgaria where it 's almost impossible to have a tornado."
        demo = gr.Interface(
            fn=self._apply,
            inputs=[
                gr.inputs.Textbox(default=sample_input),
            ],
            outputs="text",
        )
        _, path_to_local_server, self.share_url = demo.launch(
            server_name="0.0.0.0", server_port=5151
        )

        logging.info(
            "Launched gradio server at {self.share_url}, local server: {path_to_local_server}"
        )

    def _apply(self, text):
        self._input_text = text
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

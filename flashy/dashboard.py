import dataclasses
import inspect
import os
import subprocess
import sys

import streamlit as st
from lightning import LightningWork
from lightning.frontend import streamlit_base

from flashy.components import tasks
from flash_fiftyone import FlashFiftyOne
from flashy.components.flash_gradio import FlashGradio
from flashy.components.work_manager import WorkManager
from flashy.utilities import add_flashy_styles


class Dashboard(LightningWork):
    def __init__(self, run_config):
        super().__init__(parallel=True, run_once=True, raise_exception=False)

        self.run_config = run_config
        self.checkpoint = None

        self.ready = False
        self.task_meta = dataclasses.asdict(getattr(tasks, run_config["task"]))
        self.urls = []

        self.launch_fiftyone = False
        self.launch_gradio = False

        self.fiftyone_ready = False
        self.gradio_ready = False

        self._process = None

    def run(self, checkpoint):
        self.checkpoint = str(checkpoint)

        # Launch streamlit
        if self._process is None:
            env = os.environ.copy()
            env["LIGHTNING_FLOW_NAME"] = self.name
            env["LIGHTNING_RENDER_FUNCTION"] = render_fn.__name__
            env["LIGHTNING_RENDER_MODULE_FILE"] = inspect.getmodule(render_fn).__file__
            self._process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    streamlit_base.__file__,
                    "--server.address",
                    str(self.host),
                    "--server.port",
                    str(self.port),
                    "--server.headless",
                    "true",  # do not open the browser window when running locally
                ],
                env=env,
            )
            self.ready = True

    def on_exit(self):
        if self._process is not None:
            self._process.kill()


@add_flashy_styles
def render_fn(state: Dashboard):

    st.title(f"Run {state.run_config['id']}")

    st.header("Hyper-parameters")

    st.json(state.run_config["model_config"])

    with st.sidebar:

        st.header("Options")

        if state.task_meta["supports_fiftyone"]:
            launch_fiftyone = st.button(
                "Explore Predictions!", disabled=state.launch_fiftyone
            )
            if launch_fiftyone:
                state.launch_fiftyone = True

        if state.task_meta["supports_gradio"]:
            launch_gradio = st.button("Launch Demo!", disabled=state.launch_gradio)
            if launch_gradio:
                state.launch_gradio = True

        with open(state.checkpoint, "rb") as checkpoint_file:
            st.download_button(
                data=checkpoint_file.read(),
                file_name=f"checkpoint_{state.run_config['id']}.ckpt",
                label="Download Checkpoint",
            )


class DashboardManager(WorkManager):
    def __init__(self):
        super().__init__(["dashboards", "fiftyones", "gradios"])

        self.layout = []

    def reset(self):
        self.layout = []
        super().reset()

    def run(self, dashboards):
        layout = []

        for run_config, checkpoint in dashboards:
            id = run_config["id"]

            dashboard = self.get_work("dashboards", id)
            if dashboard is None:
                dashboard = Dashboard(run_config)
                self.register_work("dashboards", id, dashboard)
                dashboard.run(checkpoint)

            if dashboard.ready:
                layout.append(
                    {
                        "name": f"{id}: Dashboard",
                        "content": dashboard.url,
                    }
                )

            if dashboard.launch_fiftyone:
                fo = self.get_work("fiftyones", id)
                if fo is None:
                    fo = FlashFiftyOne()
                    self.register_work("fiftyones", id, fo)
                    fo.run(
                        id,
                        run_config["task"],
                        run_config["url"],
                        run_config["data_config"],
                        checkpoint,
                    )

                if fo.ready:
                    dashboard.fiftyone_ready = True

                    layout.append(
                        {
                            "name": f"{id}: Explorer",
                            "content": fo.url,
                        }
                    )

            if dashboard.launch_gradio:
                gradio = self.get_work("gradios", id)
                if gradio is None:
                    gradio = FlashGradio()
                    self.register_work("gradios", id, gradio)
                    gradio.run(
                        run_config["task"],
                        run_config["url"],
                        run_config["data_config"],
                        checkpoint,
                    )

                if gradio.ready:
                    dashboard.gradio_ready = True

                    layout.append(
                        {
                            "name": f"{id}: Demo",
                            "content": gradio.url,
                        }
                    )

        self.layout = layout

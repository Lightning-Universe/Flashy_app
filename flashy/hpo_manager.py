import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from lightning import LightningFlow
from lightning.frontend import StreamlitFrontend
from lightning.storage import Path
from lightning.storage.path import filesystem
from lightning.utilities.state import AppState
from ray import tune
from streamlit.script_request_queue import RerunData
from streamlit.script_runner import RerunException

from flashy.fiftyone_scheduler import FiftyOneScheduler
from flashy.run_scheduler import RunScheduler
from flashy.utilities import add_flashy_styles

_search_spaces: Dict[str, Dict[str, Dict[str, tune.sample.Domain]]] = {
    "image_classification": {
        "demo": {
            "backbone": tune.choice(["resnet18", "efficientnet_b0"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
        },
        "regular": {
            "backbone": tune.choice(["resnet50", "efficientnet_b2"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
        },
        "state-of-the-art!": {
            "backbone": tune.choice(["resnet101", "efficientnet_b4"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
        },
    }
}


def _generate_runs(count: int, task: str, search_space: Dict) -> List[Dict[str, Any]]:
    runs = []
    for run_id in range(count):
        model_config = {}
        for key, domain in search_space.items():
            model_config[key] = domain.sample()
        runs.append({"id": run_id, "task": task, "model_config": model_config})
    return runs


class HPOManager(LightningFlow):
    """The HPOManager is used to suggest a list of configurations (hyper-parameters) to run with some configuration from
    the user for the given task."""

    def __init__(self):
        super().__init__()

        self.has_run = False
        self.started = False

        self.generated_runs: Optional[List[Dict[str, Any]]] = None
        self.running_runs: Optional[List[Dict[str, Any]]] = []
        self.runs_progress = {}

        self.selected_task: Optional[str] = None

        self.explore_id: Optional[str] = None

        self.runs: LightningFlow = RunScheduler()

        self.fo = FiftyOneScheduler()

        self.results: Dict[int, Tuple[Dict[str, Any], float, str]] = {}

        self.env = None

    def run(self, selected_task: str, data_config):
        self.selected_task = selected_task.lower().replace(" ", "_")

        if self.generated_runs is not None:
            self.has_run = True
            self.running_runs: List[Dict[str, Any]] = self.generated_runs
            for run in self.running_runs:
                run["url"] = data_config.pop("url")
                run["method"] = data_config.pop("target")
                run["data_config"] = data_config

                self.results[run["id"]] = (run, "launching", None)
                logging.info(f"Results: {self.results[run['id']]}")
            logging.info(f"Running: {self.running_runs}")

            self.runs.run(self.running_runs)
            self.generated_runs = None

        for run in self.running_runs:
            run_work = getattr(self.runs, f"work_{run['id']}")
            if run_work.has_succeeded:
                # HACK!!!
                self.env = run_work.env
                self.results[run["id"]] = (
                    run,
                    run_work.monitor,
                    run_work.last_model_path_source,
                )
            elif run_work.has_failed:
                self.results[run["id"]] = (run, "Failed", None)
            elif run_work.has_started:
                self.results[run["id"]] = (run, "started", None)

        if self.explore_id is not None:
            result = self.results[self.explore_id]
            run_work = getattr(self.runs, f"work_{result[0]['id']}")
            path = Path(run_work.last_model_path)
            path._attach_work(run_work)
            self.fo.run(result[0], path)

    def configure_layout(self):
        return StreamlitFrontend(render_fn=render_fn)

    def exposed_url(self) -> str:
        return self.fo.work.url


@add_flashy_styles
def render_fn(state: AppState) -> None:
    st.title("Build your model!")

    quality = st.select_slider(
        "Model type",
        _search_spaces.get(state.selected_task, {}).keys(),
        disabled=state.selected_task not in _search_spaces,
    )

    performance = st.select_slider(
        "Target performance",
        ("low", "medium", "high"),
        disabled=state.selected_task not in _search_spaces,
    )

    start_training_placeholder = st.empty()
    start_runs = start_training_placeholder.button(
        "Start training!",
        disabled=state.has_run
        or state.generated_runs is not None
        or state.selected_task not in _search_spaces,
    )

    if start_runs:
        start_training_placeholder.button("Start training!", disabled=True)
        performance_runs = {
            "low": 1,
            "medium": 5,
            "high": 10,
        }
        state.generated_runs = _generate_runs(
            performance_runs[performance],
            state.selected_task,
            _search_spaces[state.selected_task][quality],
        )

    st.write("## Results")

    if state.results or state.generated_runs:
        spinners = []
        refresh = False

        results = state.results

        if not results:
            results = {
                run["id"]: (run, "launching", "") for run in state.generated_runs
            }

        keys = results[next(iter(results.keys()))][0]["model_config"].keys()
        columns = st.columns(len(keys) + 3)

        for idx, key in enumerate(keys):
            with columns[idx]:
                st.write(f"### {key}")

                for result in results.values():
                    st.write(result[0]["model_config"][key])

        with columns[-3]:
            st.write("### Performance")

            for result in results.values():
                if result[1] == "launching":
                    spinner_context = st.spinner("Launching...")
                    spinner_context.__enter__()
                    spinners.append(spinner_context)
                elif result[1] == "started":
                    progress = getattr(
                        getattr(state.runs, f"work_{result[0]['id']}", None),
                        "progress",
                        None,
                    )
                    state.runs_progress[result[0]["id"]] = progress or 0.0
                    st.progress(state.runs_progress[result[0]["id"]])
                    refresh = True
                else:
                    st.write(result[1])

        with columns[-2]:
            st.write("### FiftyOne")

            fiftyone_buttons = []

            for result in results.values():
                if result[1] == "Failed":
                    st.write("Failed")
                elif result[1] in ["launching", "started"]:
                    st.write("Waiting")
                else:
                    fiftyone_buttons.append(
                        (
                            result,
                            st.button(
                                "Explore!",
                                key=result[0]["id"],
                                disabled=state.explore_id == result[0]["id"],
                            ),
                        )
                    )

            for (result, button) in fiftyone_buttons:
                if button:
                    state.explore_id = result[0]["id"]

                if (
                    state.explore_id == result[0]["id"]
                    and state.fo.ready
                    and state.fo.run_id == result[0]["id"]
                ):
                    st.write(
                        """
                        <a href="http://127.0.0.1:7501/view/Data%20Explorer" target="_parent">Open</a>
                    """,
                        unsafe_allow_html=True,
                    )
                elif state.explore_id == result[0]["id"] or button:
                    spinner_context = st.spinner("Loading...")
                    spinner_context.__enter__()
                    spinners.append(spinner_context)

        with columns[-1]:
            st.write("### Checkpoint")

            fs = None
            if state.env is not None:
                for key, value in state.env.items():
                    if value:
                        os.environ[key] = value
                fs = filesystem()

            for result in results.values():
                if result[1] == "Failed":
                    st.write("Failed")
                elif result[1] in ["launching", "started"]:
                    st.write("Waiting...")
                else:
                    # if not os.path.exists(result[2]):
                    #     logging.error(f"Checkpoint file at: {result[2]} not found.")
                    if fs is not None:
                        with fs.open(result[2], "rb") as ckpt_file:
                            st.download_button(
                                data=ckpt_file.read(),
                                file_name="checkpoint_"
                                + str(result[0]["id"])
                                + ".ckpt",
                                label="Download",
                                key=str(result[0]["id"]),
                            )

        if refresh or spinners or state.explore_id != state.fo.run_id:
            time.sleep(0.5)
            _ = [
                spinner_context.__exit__(None, None, None)
                for spinner_context in spinners
            ]
            raise RerunException(RerunData())

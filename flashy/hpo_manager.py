import time
from copy import copy
from typing import Any, Dict, List, Optional, Tuple
import logging

import streamlit as st
from lightning import LightningFlow
from lightning.frontend import StreamlitFrontend
from lightning.storage import Path
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

        self.generated_runs: Optional[List[Dict[str, Any]]] = None
        self.running_runs: Optional[List[Dict[str, Any]]] = []

        self.selected_task: Optional[str] = None

        self.explore_id: Optional[str] = None

        self.runs: LightningFlow = RunScheduler()

        self.fo = FiftyOneScheduler()

        self.results: Dict[int, Tuple[Dict[str, Any], float]] = {}

    def run(self, selected_task: str, url, method, data_config):
        self.selected_task = selected_task.lower().replace(" ", "_")

        if self.generated_runs is not None:
            self.has_run = True
            self.running_runs: List[Dict[str, Any]] = self.generated_runs
            for run in self.running_runs:
                run["url"] = url
                run["method"] = method
                run["data_config"] = data_config

                self.results[run['id']] = (run, "launching")
            logging.info(f"Running: {self.running_runs}")

            self.runs.run(self.running_runs)
            self.generated_runs = None

        for run in self.running_runs:
            run_work = getattr(self.runs, f"work_{run['id']}")
            if run_work.has_succeeded:
                self.results[run['id']] = (run, run_work.monitor)
            elif run_work.has_failed:
                self.results[run['id']] = (run, "Failed")
            elif run_work.has_started:
                self.results[run['id']] = (run, "started")

            if self.explore_id is not None and run["id"] == self.explore_id:
                path = Path(run_work.best_model_path)
                path._attach_work(run_work)
                self.fo.run(run, path)

    def configure_layout(self):
        return StreamlitFrontend(render_fn=render_fn)

    def exposed_url(self, key: str) -> str:
        return self.fo.work.exposed_url(key)


@add_flashy_styles
def render_fn(state: AppState) -> None:
    st.title("Build your model!")

    quality = st.select_slider("Model type", _search_spaces[state.selected_task].keys())

    performance = st.select_slider("Target performance", ("low", "medium", "high"))

    start_runs = st.button("Start training!", disabled=state.has_run)

    if start_runs:
        if performance:
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
            raise RerunException(RerunData())

    st.write("## Results")


    if state.results:
        spinners = []
        keys = state.results[next(iter(state.results.keys()))][0]["model_config"].keys()
        columns = st.columns(len(keys) + 2)

        for idx, key in enumerate(keys):
            with columns[idx]:
                st.write(f"### {key}")

                for result in state.results.values():
                    st.write(result[0]["model_config"][key])

        with columns[-2]:
            st.write("### Performance")

            for result in state.results.values():
                if result[1] == "launching":
                    spinner_context = st.spinner("Launching...")
                    spinner_context.__enter__()
                    spinners.append(spinner_context)
                elif result[1] == "started":
                    spinner_context = st.spinner("Running...")
                    spinner_context.__enter__()
                    spinners.append(spinner_context)
                else:
                    st.write(result[1])

        with columns[-1]:
            st.write("### FiftyOne")

            def set_explore_id(id):
                def callback():
                    state.explore_id = id

                return callback

            for result in state.results.values():
                if state.fo.run_id == result[0]["id"]:
                    if state.fo.ready:
                        st.write(
                            """
                            <a href="http://127.0.0.1:7501/view/Data%20Explorer" target="_parent">Open</a>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        spinner_context = st.spinner("Loading...")
                        spinner_context.__enter__()
                        spinners.append(spinner_context)
                else:
                    if result[1] == "Failed":
                        st.write("Failed")
                    elif result[1] in ["launching", "started"]:
                        st.write("Waiting")
                    else:
                        explore = st.button(
                            "Explore!",
                            key=result[0]["id"],
                            on_click=set_explore_id(result[0]["id"]),
                        )
                        if explore:
                            raise RerunException(RerunData())

        if spinners:
            time.sleep(2)
            _ = [spinner_context.__exit__(None, None, None) for spinner_context in spinners]
            raise RerunException(RerunData())

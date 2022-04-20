import time
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from lightning import LightningFlow
from lightning.frontend import StreamlitFrontend
from lightning.utilities.state import AppState
from ray import tune
from streamlit.script_request_queue import RerunData
from streamlit.script_runner import RerunException

from fiftyone_scheduler import FiftyOneScheduler
from run_scheduler import RunScheduler
from utilities import add_flashy_styles

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

        self.selected_task: Optional[str] = None

        self.explore_id: Optional[str] = None

        self.run_scheduler: LightningFlow = RunScheduler()

        self.fiftyone_scheduler = FiftyOneScheduler()

        self.results: List[Tuple[Dict[str, Any], float]] = []

    def run(self, selected_task: str, url, method, data_config):
        self.selected_task = selected_task.lower().replace(" ", "_")

        if self.generated_runs is not None:
            self.has_run = True
            runs: List[Dict[str, Any]] = self.generated_runs
            for run in runs:
                run["url"] = url
                run["method"] = method
                run["data_config"] = data_config
            self.run_scheduler.queued_runs = runs
            self.generated_runs = None

        self.run_scheduler.run()

        if self.run_scheduler.running_runs is not None:
            running_runs = []
            for run in self.run_scheduler.running_runs:
                run_work = getattr(self.run_scheduler, f"run_work_{run['id']}")
                if run_work.has_succeeded:
                    self.results.append((run, run_work.monitor))
                elif run_work.has_failed:
                    self.results.append((run, "Failed"))
                else:
                    running_runs.append(run)
                self.run_scheduler.running_runs = running_runs

        if self.explore_id is not None:
            run = None
            for result in self.results:
                if result[0]["id"] == self.explore_id:
                    run = result[0]
                    break

            self.fiftyone_scheduler.run(
                run,
                getattr(self.run_scheduler, f"run_work_{run['id']}").best_model_path,
            )

    def configure_layout(self):
        return StreamlitFrontend(render_fn=render_fn)

    def exposed_url(self, key: str) -> str:
        return self.fiftyone_scheduler.fiftyone_work.exposed_url(key)


@add_flashy_styles
def render_fn(state: AppState) -> None:
    st.title("Build your model!")

    quality = st.select_slider("Model type", _search_spaces[state.selected_task].keys())

    performance = st.select_slider("Target performance", ("low", "medium", "high"))

    start_runs = st.button("Start training!", disabled=state.has_run)

    if start_runs:
        if performance:
            # TODO: Currently medium == high but should be changed when dynamic works are supported
            performance_runs = {
                "low": 1,
                "medium": 10,
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
        columns = st.columns(len(state.results[0][0]["model_config"].keys()) + 2)

        for idx, key in enumerate(state.results[0][0]["model_config"].keys()):
            with columns[idx]:
                st.write(f"### {key}")

                for result in state.results:
                    st.write(result[0]["model_config"][key])

        with columns[-2]:
            st.write("### performance")

            for result in state.results:
                st.write(result[1])

        with columns[-1]:
            st.write("### ---")

            def set_explore_id(id):
                def callback():
                    state.explore_id = id

                return callback

            for result in state.results:
                if state.fiftyone_scheduler.run_id == result[0]["id"]:
                    if state.fiftyone_scheduler.done:
                        st.write(
                            """
                            <a href="http://127.0.0.1:7501/view/Data%20Explorer" target="_parent">Open</a>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        with st.spinner("Loading..."):
                            time.sleep(1)
                            raise RerunException(RerunData())
                else:
                    if result[1] != "Failed":
                        explore = st.button(
                            "Explore!",
                            key=result[0]["id"],
                            on_click=set_explore_id(result[0]["id"]),
                        )
                        if explore:
                            raise RerunException(RerunData())
                    else:
                        st.write("Failed")

    if state.run_scheduler.running_runs or state.run_scheduler.queued_runs:
        with st.spinner("Training..."):
            time.sleep(2)
            raise RerunException(RerunData())

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from lightning import LightningFlow
from lightning.frontend import StreamlitFrontend
from lightning.storage import Path
from lightning.utilities.state import AppState
from ray import tune
from streamlit.scriptrunner import RerunData, RerunException

from flashy.dashboard import DashboardManager
from flashy.run_scheduler import RunScheduler
from flashy.utilities import add_flashy_styles

_search_spaces: Dict[str, Dict[str, Dict[str, tune.sample.Domain]]] = {
    "image_classification": {
        "demo": {
            "backbone": tune.choice(["resnet18", "efficientnet_b0"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
            "use_gpu": False,
        },
        "regular": {
            "backbone": tune.choice(["resnet50", "efficientnet_b2"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
            "use_gpu": True,
        },
        "state-of-the-art!": {
            "backbone": tune.choice(["resnet101", "efficientnet_b4"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
            "use_gpu": True,
        },
    },
    "text_classification": {
        "demo": {
            "backbone": tune.choice(["prajjwal1/bert-tiny"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
        },
        "regular": {
            "backbone": tune.choice(["prajjwal1/bert-small"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
        },
        "state-of-the-art!": {
            "backbone": tune.choice(["prajjwal1/bert-medium"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
        },
    },
}


def _generate_runs(count: int, task: str, search_space: Dict) -> List[Dict[str, Any]]:
    runs = []
    for run_id in range(count):
        model_config = {}
        for key, domain in search_space.items():
            if hasattr(domain, "sample"):
                model_config[key] = domain.sample()
            else:
                model_config[key] = domain
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
        self.runs_progress = {}

        self.selected_task: Optional[str] = None

        self.runs: LightningFlow = RunScheduler()

        self.dm = DashboardManager()

        self.results: Dict[int, Tuple[Dict[str, Any], float]] = {}

        self.dashboards = []

    def run(self, selected_task: str, data_config, url: str):
        self.selected_task = selected_task.lower().replace(" ", "_")

        if self.generated_runs is not None:
            self.has_run = True
            self.running_runs: List[Dict[str, Any]] = self.generated_runs
            for run in self.running_runs:
                run["url"] = url

                run["data_config"] = data_config

                self.results[run["id"]] = (run, "launching")
                logging.info(f"Results: {self.results[run['id']]}")
            logging.info(f"Running: {self.running_runs}")

            self.generated_runs = None
            self.runs.run(self.running_runs)

        for run in self.running_runs:
            run_work = getattr(self.runs, f"work_{run['id']}", None)
            if run_work is not None:
                if run_work.has_succeeded:
                    self.results[run["id"]] = (
                        run,
                        run_work.monitor,
                    )
                elif run_work.has_failed:
                    self.results[run["id"]] = (run, "Failed")
                elif run_work.has_started:
                    self.results[run["id"]] = (run, "started")

        dashboards = []
        for run_id in self.dashboards:
            run_work = getattr(self.runs, f"work_{run_id}")
            path = Path(run_work.last_model_path)
            path._attach_work(run_work)
            dashboards.append((self.results[run_id][0], path))
        self.dm.run(dashboards)

    def configure_layout(self):
        return StreamlitFrontend(render_fn=render_fn)


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

    start_runs = st.button(
        "Start training!",
        disabled=state.has_run
        or state.generated_runs is not None
        or state.selected_task not in _search_spaces,
    )

    if start_runs:
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

        results = state.results

        if not results:
            results = {
                run["id"]: (run, "launching", "") for run in state.generated_runs
            }

        keys = results[next(iter(results.keys()))][0]["model_config"].keys()
        columns = st.columns(len(keys) + 2)

        for idx, key in enumerate(keys):
            with columns[idx]:
                st.write(f"### {key}")

                for result in results.values():
                    st.write(result[0]["model_config"][key])

        with columns[-2]:
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
                else:
                    st.write(result[1])

        with columns[-1]:
            st.write("### Open Dashboard")

            buttons = []

            for result in results.values():
                if result[1] == "Failed":
                    st.write("Failed")
                elif result[1] in ["launching", "started"]:
                    st.write("Waiting...")
                else:
                    buttons.append(
                        (
                            result,
                            st.button(
                                "Open!",
                                key=result[0]["id"],
                                disabled=result[0]["id"] in state.dashboards,
                            ),
                        )
                    )

            for (result, button) in buttons:
                if button and result[0]["id"] not in state.dashboards:
                    state.dashboards = state.dashboards + [result[0]["id"]]

                if (
                    result[0]["id"] in state.dashboards
                    and not getattr(
                        getattr(state.dm, f"dash_{result[0]['id']}", None),
                        "ready",
                        False,
                    )
                ) or button:
                    spinner_context = st.spinner("Loading...")
                    spinner_context.__enter__()
                    spinners.append(spinner_context)

        if spinners:
            time.sleep(0.5)
            _ = [
                spinner_context.__exit__(None, None, None)
                for spinner_context in spinners
            ]
            raise RerunException(RerunData())

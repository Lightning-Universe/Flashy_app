import logging
from typing import Any, Dict, List, Optional, Tuple

from lightning import LightningFlow
from lightning.storage import Path
from ray import tune

from flashy.dashboard import DashboardManager
from flashy.run_scheduler import RunScheduler

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

        self.start = False
        self.selected_task: Optional[str] = None
        self.data_config = {}
        self.model = "demo"
        self.performance = "low"

        self.ready = False
        self.has_run = False

        self.generated_runs: Optional[List[Dict[str, Any]]] = None
        self.running_runs: Optional[List[Dict[str, Any]]] = []

        self.runs = RunScheduler()

        self.dm = DashboardManager()

        self.results: Dict[int, Tuple[Dict[str, Any], float]] = {}

        self.dashboards = []

    def run(self, root: Path):
        if self.start:
            # Generate runs
            performance_runs = {
                "low": 1,
                "medium": 5,
                "high": 10,
            }
            self.generated_runs = _generate_runs(
                performance_runs[self.performance],
                self.selected_task,
                _search_spaces[self.selected_task][self.model],
            )
            self.start = False
            self.ready = False
            self.has_run = True

        if self.generated_runs is not None:
            # Teardown any existing works / results
            self.dm.reset()
            self.runs.reset()
            self.results = {}
            self.dashboards = []

            # Launch new runs
            self.running_runs: List[Dict[str, Any]] = self.generated_runs
            for run in self.running_runs:
                run["data_config"] = self.data_config
            logging.info(f"Running: {self.running_runs}")

            self.generated_runs = None
            self.runs.run(root, self.running_runs)

        for run in self.running_runs:
            run_work = self.runs.get_work("runs", str(run["id"]))
            if run_work is not None:
                if run_work.has_succeeded:
                    self.results[run["id"]] = {
                        "run": run,
                        "progress": "completed",
                        "monitor": run_work.monitor,
                    }
                elif run_work.has_failed:
                    self.ready = True
                    self.results[run["id"]] = {"run": run, "progress": "failed"}
                elif run_work.ready:
                    self.ready = True
                    self.results[run["id"]] = {
                        "run": run,
                        "progress": run_work.progress,
                    }

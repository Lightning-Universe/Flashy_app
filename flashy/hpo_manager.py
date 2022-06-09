import logging
import uuid
from typing import Any, Dict, List, Optional

from lightning import LightningFlow
from lightning.storage import Drive
from ray import tune

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
            "use_gpu": False,
        },
        "regular": {
            "backbone": tune.choice(["prajjwal1/bert-small"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
            "use_gpu": True,
        },
        "state-of-the-art!": {
            "backbone": tune.choice(["prajjwal1/bert-medium"]),
            "learning_rate": tune.uniform(0.00001, 0.01),
            "use_gpu": True,
        },
    },
}


def _generate_runs(count: int, task: str, search_space: Dict) -> List[Dict[str, Any]]:
    runs = []
    for _ in range(count):
        model_config = {}
        for key, domain in search_space.items():
            if hasattr(domain, "sample"):
                model_config[key] = domain.sample()
            else:
                model_config[key] = domain
        runs.append({"task": task, "model_config": model_config})
    return runs


class HPOManager(LightningFlow):
    """The HPOManager is used to suggest a list of configurations (hyper-parameters) to run with some configuration from
    the user for the given task."""

    def __init__(self, datasets: Drive, checkpoints: Drive):
        super().__init__()

        self.runs = RunScheduler(datasets, checkpoints)

        self.start = False
        self.dataset: Optional[str] = None
        self.selected_task: Optional[str] = None
        self.data_config = {}
        self.model = "demo"
        self.performance = "low"

        self.running_runs: Dict[int, List[Dict[str, Any]]] = {}
        self.results: Dict[int, Dict[str, Dict[str, Any]]] = {}

        self.stopped_run = None

    def run(self):
        if self.start:
            self.start = False
            # Generate runs
            performance_runs = {
                "low": 1,
                "medium": 5,
                "high": 10,
            }
            generated_runs = _generate_runs(
                performance_runs[self.performance],
                self.selected_task,
                _search_spaces[self.selected_task][self.model],
            )

            # Launch new runs
            for run in generated_runs:
                run["id"] = uuid.uuid4().hex[:8]  # TODO: Prettier random IDs
                run["data_config"] = self.data_config
            logging.info(f"Running: {generated_runs}")

            sweep_id = (
                max(int(id) for id in self.running_runs.keys()) + 1
                if self.running_runs
                else 1
            )
            self.running_runs[sweep_id] = generated_runs

            self.runs.run(self.dataset, generated_runs)

        for sweep_id, runs in self.running_runs.items():

            if sweep_id not in self.results:
                self.results[sweep_id] = {}

            for run in runs:
                run_work = self.runs.get_work("runs", str(run["id"]))
                if run_work is not None:
                    if run_work.has_succeeded:
                        self.results[sweep_id][run["id"]] = {
                            "run": run,
                            "progress": "succeeded",
                            "monitor": run_work.monitor,
                        }
                    elif run_work.has_failed:
                        self.results[sweep_id][run["id"]] = {
                            "run": run,
                            "progress": "failed",
                        }
                    elif run_work.has_stopped:
                        self.results[sweep_id][run["id"]] = {
                            "run": run,
                            "progress": "stopped",
                        }
                    elif run_work.ready:
                        self.results[sweep_id][run["id"]] = {
                            "run": run,
                            "progress": run_work.progress,
                        }
                    else:
                        self.results[sweep_id][run["id"]] = {
                            "run": run,
                            "progress": "launching",
                        }

        if self.stopped_run is not None:
            # TODO: There could be race conditions if two stop requests are made seperately
            run_work = self.runs.get_work("runs", str(self.stopped_run))
            self.stopped_run = None
            run_work.stop()

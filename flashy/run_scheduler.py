import logging
from typing import Any, Dict, List, Optional

import lightning as L
from lightning.app.storage import Drive

from flashy.components.flash_trainer import FlashTrainer
from flashy.components.work_manager import WorkManager


class RunScheduler(WorkManager):
    def __init__(self, datasets: Drive, checkpoints: Drive):
        super().__init__(["runs"])

        self.datasets = datasets
        self.checkpoints = checkpoints

    def run(self, dataset: str, queued_runs: Optional[List[Dict[str, Any]]]):
        logging.info(f"Queued runs: {queued_runs}")
        for run in queued_runs:
            run_work = FlashTrainer(
                run["task"],
                self.datasets,
                self.checkpoints,
                cloud_compute=L.CloudCompute("gpu" if run["model_config"].pop("use_gpu", False) else "cpu-small"),
            )
            self.register_work("runs", run["id"], run_work)
            logging.info(f"Launching run: {run['id']}. Run work `run` method: {run_work.run}.")
            run_work.run(run["id"], dataset, run["data_config"], run["model_config"])

import logging
from typing import Any, Dict, List, Optional

from lightning import CloudCompute
from lightning.storage import Path

from flashy.components.flash_trainer import FlashTrainer
from flashy.components.work_manager import WorkManager


class RunScheduler(WorkManager):
    def __init__(self):
        super().__init__(["runs"])

    def run(self, root: Path, queued_runs: Optional[List[Dict[str, Any]]]):
        logging.info(f"Queued runs: {queued_runs}")
        for run in queued_runs:
            run_work = FlashTrainer(
                cloud_compute=CloudCompute(
                    "gpu" if run["model_config"].pop("use_gpu", False) else "cpu-small"
                ),
            )
            self.register_work("runs", run["id"], run_work)
            logging.info(
                f"Launching run: {run['id']}. Run work `run` method: {run_work.run}."
            )
            run_work.run(root, run["task"], run["data_config"], run["model_config"])

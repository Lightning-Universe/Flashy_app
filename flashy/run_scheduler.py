import logging
from typing import Any, Dict, List, Optional

from lightning import LightningFlow

from flashy.components.flash_trainer import FlashTrainer


class RunScheduler(LightningFlow):
    def run(self, queued_runs: Optional[List[Dict[str, Any]]]):
        logging.info(f"Queued runs: {queued_runs}")
        for run in queued_runs:
            run_work = FlashTrainer()
            setattr(self, f"work_{run['id']}", run_work)
            logging.info(
                f"Launching run: {run['id']}. Run work `run` method: {run_work.run}."
            )
            run_work.run(
                run["task"], run["url"], run["data_config"], run["model_config"]
            )

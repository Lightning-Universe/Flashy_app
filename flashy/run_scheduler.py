import functools
import logging
import os
import os.path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from lightning import LightningFlow

import flashy
from flashy.components.flash_trainer import FlashTrainer


@functools.lru_cache
def _get_env():
    return Environment(loader=FileSystemLoader(flashy.TEMPLATES_ROOT))


def _generate_script(script_dir, run: Dict[str, Any], template_file, **kwargs) -> str:
    template = _get_env().get_template(template_file)

    variables = {
        "root": script_dir,
        "run_id": run["id"],
        "url": run["url"],
        "data_config": run["data_config"],
        "model_config": run["model_config"],
        **kwargs,
    }

    generated_script = os.path.join(
        script_dir, f"{run['id']}_{template_file.replace('jinja', 'py')}"
    )
    with open(generated_script, "w") as f:
        logging.info(f"Rendering {template_file} with variables: {variables}")
        f.write(template.render(**variables))

    return generated_script


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

import logging
import os
import os.path
import shutil
import sys
import tempfile
from typing import Dict, Optional

from lightning.components.python import TracerPythonScript
from lightning.storage.path import Path

from flashy.components import tasks
from flashy.components.tasks import TaskMeta
from flashy.components.utilities import generate_script


class FlashTrainer(TracerPythonScript):
    def __init__(self, **kwargs):
        super().__init__(__file__, raise_exception=True, parallel=True, **kwargs)

        self.script_dir = tempfile.mkdtemp()
        self.last_model_path: Optional[Path] = None
        self.monitor = None
        self.progress = None
        self._task_meta: Optional[TaskMeta] = None

    def convert_path_to_str(self, data_config: dict):
        for key, val in data_config.items():
            if isinstance(val, Path):
                data_config[key] = str(val)

    def run(
        self,
        task: str,
        url: str,
        data_config: Dict,
        task_config: Dict,
    ):
        logging.info(f"Generating script in: {self.script_dir}")

        self.script_path = os.path.join(self.script_dir, "flash_training.py")

        self._task_meta = getattr(tasks, task)

        logging.info("Data config: {data_config}")
        logging.info("Task config: {task_config}")

        self.convert_path_to_str(data_config)

        generate_script(
            self.script_path,
            "flash_training.jinja",
            task=task,
            data_module_import_path=self._task_meta.data_module_import_path,
            data_module_class=self._task_meta.data_module_class,
            task_import_path=self._task_meta.task_import_path,
            task_class=self._task_meta.task_class,
            linked_attributes=self._task_meta.linked_attributes,
            url=url,
            data_config=data_config,
            task_config=task_config,
        )
        logging.info(f"Running script: {self.script_path}")
        super().run()

    def _run_tracer(self, init_globals):
        sys.argv = [self.script_path]
        tracer = self.configure_tracer()
        return tracer.trace(self.script_path, self, *self.script_args, init_globals=init_globals)

    def on_after_run(self, res):
        checkpoint_path = os.path.join(self.script_dir, "last_checkpoint.pt")
        res["trainer"].save_checkpoint(checkpoint_path)

        self.monitor = float(
            res["trainer"].callback_metrics[self._task_meta.monitor].item()
        )
        self.last_model_path = Path(checkpoint_path)
        logging.info(f"Stored last model path: {self.last_model_path}")

    def on_exit(self):
        shutil.rmtree(self.script_dir)

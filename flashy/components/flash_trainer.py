import logging
import os
import os.path
import shutil
import sys
import tempfile
import time
from typing import Dict, Optional

from lightning.components.python import TracerPythonScript
from lightning.storage.path import (
    Path,
    PathGetRequest,
    filesystem,
    path_to_artifacts_path_work_name,
)

from flashy.components import tasks
from flashy.components.tasks import TaskMeta
from flashy.components.utilities import generate_script


class FlashTrainer(TracerPythonScript):
    def __init__(self, **kwargs):
        super().__init__(__file__, blocking=False, raise_exception=True, **kwargs)

        self.script_dir = tempfile.mkdtemp()
        self.last_model_path: Optional[Path] = None
        self.last_model_path_source = None
        self.env = None
        self.monitor = None
        self.progress = None
        self._task_meta: Optional[TaskMeta] = None

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

    def _run_tracer(self):
        sys.argv = [self.script_path]
        tracer = self.configure_tracer()
        return tracer.trace(self.script_path, self, *self.script_args)

    def on_after_run(self, res):
        checkpoint_path = os.path.join(self.script_dir, "last_checkpoint.pt")
        res["trainer"].save_checkpoint(checkpoint_path)

        self.monitor = float(
            res["trainer"].callback_metrics[self._task_meta.monitor].item()
        )
        self.last_model_path = Path(checkpoint_path)
        logging.info(f"Stored last model path: {self.last_model_path}")

        # Transfer Path to Storage
        path = Path(self.last_model_path)
        path._attach_work(self)
        path._attach_queues(self._request_queue, self._response_queue)

        request = PathGetRequest(
            source=path.origin_name, path=str(path), hash=path.hash
        )
        path._request_queue.put(request)

        response = path._response_queue.get()  # blocking

        fs = filesystem()
        source_path = path_to_artifacts_path_work_name(path, response.source)

        while not fs.exists(source_path):
            # TODO: Existence check on folder is not enough, files may not be completely transferred yet
            time.sleep(0.5)

        self.last_model_path_source = str(source_path)

        self.env = {
            "LIGHTNING_BUCKET_ENDPOINT_URL": os.getenv(
                "LIGHTNING_BUCKET_ENDPOINT_URL", ""
            ),
            "LIGHTNING_BUCKET_NAME": os.getenv("LIGHTNING_BUCKET_NAME", ""),
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
            "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "LIGHTNING_CLOUD_APP_ID": os.getenv("LIGHTNING_CLOUD_APP_ID", ""),
        }

    def on_exit(self):
        shutil.rmtree(self.script_dir)

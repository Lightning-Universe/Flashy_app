import json
import logging
import os
import os.path
import shutil
import sys
import tarfile
import tempfile
import zipfile
from typing import Dict

from lightning import BuildConfig
from lightning.components.python import TracerPythonScript
from lightning.storage import Drive

from flashy.components import tasks
from flashy.components.tasks import TaskMeta
from flashy.components.utilities import generate_script


class FlashTrainer(TracerPythonScript):
    def __init__(self, task: str, datasets: Drive, checkpoints: Drive, **kwargs):
        super().__init__(
            __file__,
            cloud_build_config=BuildConfig(
                requirements=getattr(tasks, task).requirements
            ),
            raise_exception=True,
            parallel=True,
            **kwargs,
        )

        self.task = task
        self.datasets = datasets
        self.checkpoints = checkpoints

        self.id = None

        self.script_dir = tempfile.mkdtemp()
        self.ready = False
        self.monitor = None
        self.progress = 0.0

        self._task_meta: TaskMeta = getattr(tasks, task)

    def run(
        self,
        id: str,
        dataset: str,
        data_config: Dict,
        task_config: Dict,
    ):
        self.id = id

        meta_file_path = dataset + ".meta"

        if not os.path.exists(dataset):
            self.datasets.get(dataset)
        if not os.path.exists(meta_file_path):
            self.datasets.get(meta_file_path)

        with open(meta_file_path) as f:
            meta = json.load(f)

        os.replace(dataset, meta["original_path"])

        file_path = meta["original_path"]

        if zipfile.is_zipfile(file_path):
            with zipfile.ZipFile(file_path, "r") as zf:
                zf.extractall(".")
        elif tarfile.is_tarfile(file_path):
            with tarfile.TarFile(file_path, "r") as tf:
                tf.extractall(".")
        else:
            raise ValueError("Cannot open archive file!")

        logging.info(f"Generating script in: {self.script_dir}")
        self.script_path = os.path.join(self.script_dir, "flash_training.py")

        logging.info("Data config: {data_config}")
        logging.info("Task config: {task_config}")

        generate_script(
            self.script_path,
            "flash_training.jinja",
            task=self.task,
            data_module_import_path=self._task_meta.data_module_import_path,
            data_module_class=self._task_meta.data_module_class,
            task_import_path=self._task_meta.task_import_path,
            task_class=self._task_meta.task_class,
            linked_attributes=self._task_meta.linked_attributes,
            data_config=data_config,
            task_config=task_config,
        )
        logging.info(f"Running script: {self.script_path}")

        self.ready = True
        super().run()

    def _run_tracer(self, init_globals):
        sys.argv = [self.script_path]
        tracer = self.configure_tracer()
        return tracer.trace(
            self.script_path, self, *self.script_args, init_globals=init_globals
        )

    def on_after_run(self, res):
        checkpoint_path = f"{self.id}_checkpoint.pt"
        res["trainer"].save_checkpoint(checkpoint_path)
        self.checkpoints.put(checkpoint_path)

        self.monitor = float(
            res["trainer"].callback_metrics[self._task_meta.monitor].item()
        )

    def on_exit(self):
        shutil.rmtree(self.script_dir)

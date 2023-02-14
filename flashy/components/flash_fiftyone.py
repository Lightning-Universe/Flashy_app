import logging
import os.path
import shutil
import tempfile
from typing import Dict, List, Optional

import lightning as L
from lightning.app.components.python import TracerPythonScript
from lightning.app.storage.path import Path

from flashy.components import tasks
from flashy.components.tasks import TaskMeta
from flashy.components.utilities import generate_script


class FiftyOneBuildConfig(L.BuildConfig):
    def build_commands(self) -> List[str]:
        return [
            "python -m pip install lightning-flash[image]==0.7.5 fiftyone==0.15.1",
            "python -m pip uninstall -y opencv-python",
            "python -m pip uninstall -y opencv-python-headless",
            "python -m pip install opencv-python-headless==4.5.5.64",
        ]


class FlashFiftyOne(TracerPythonScript):
    def __init__(self):
        super().__init__(
            __file__,
            cache_calls=False,
            parallel=True,
            port=5151,
            cloud_build_config=FiftyOneBuildConfig(),
            raise_exception=False,
        )

        self.ready = False

        self.script_dir = tempfile.mkdtemp()
        self.script_path = os.path.join(self.script_dir, "flash_fiftyone.py")
        self._session = None
        self._task_meta: Optional[TaskMeta] = None

    def run(
        self,
        task: str,
        url: str,
        data_config: Dict,
        checkpoint: Path,
    ):
        try:
            import fiftyone

            _ = fiftyone.__version__
        except (ModuleNotFoundError, AttributeError):
            msg = "Please consider installing fiftyone manually using " + "`pip install fiftyone==0.16.0`"
            raise ModuleNotFoundError(msg)

        self._task_meta = getattr(tasks, task)

        generate_script(
            self.script_path,
            "flash_fiftyone.jinja",
            task=task,
            data_module_import_path=self._task_meta.data_module_import_path,
            data_module_class=self._task_meta.data_module_class,
            task_import_path=self._task_meta.task_import_path,
            task_class=self._task_meta.task_class,
            url=url,
            data_config=data_config,
            checkpoint=str(checkpoint),
        )
        super().run()

    def on_after_run(self, res):
        from flash.core.integrations.fiftyone import visualize

        logging.info("Launching FiftyOne")

        if self._session is not None:
            self._session.close()

        predictions = res["predictions"]

        self._session = visualize(predictions, remote=True, address=self.host)

        logging.info(f"Launched at URL: {self._session.url}")
        self.ready = True

    def on_exit(self):
        if self._session is not None:
            self._session.close()
        shutil.rmtree(self.script_dir)

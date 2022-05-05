import functools
import inspect
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import lightning
from jinja2 import Environment, FileSystemLoader
from lightning.frontend import StreamlitFrontend
from lightning.utilities.log import get_frontend_logfile

from flashy import TEMPLATES_ROOT

TARGET_TYPE = TypeVar("TARGET_TYPE", type(Type), Callable)


@functools.lru_cache
def _get_env():
    return Environment(loader=FileSystemLoader(TEMPLATES_ROOT))


_WRAPPER_TYPES = {Union, Optional}


def _is_compatible_type(annotation, target) -> bool:
    origin = get_origin(annotation) or annotation

    if any(
        [
            origin == Any,
            target == origin,
            inspect.isclass(origin)
            and inspect.isclass(target)
            and issubclass(target, origin),
            inspect.isclass(origin)
            and inspect.isclass(target)
            and issubclass(origin, target),
        ]
    ):
        return True

    elif origin in _WRAPPER_TYPES:
        return any(_is_compatible_type(arg, target) for arg in get_args(annotation))

    return False


class StreamlitAutoConfig(StreamlitFrontend):
    """The ``StreamlitAutoConfig`` is a ``StreamlitFrontend`` which automatically populates the ``render_fn`` with a
    configurator for the provided class."""

    def __init__(
        self,
        targets: Union[TARGET_TYPE, List[TARGET_TYPE]],
        render_fn_preamble: Optional[Callable],
        defaults: Optional[Dict] = None,
        ignore: Optional[List[str]] = None,
    ) -> None:
        super().__init__(None)

        if not isinstance(targets, list):
            targets = [targets]
        self.targets = targets
        self.render_fn_preamble = render_fn_preamble
        self.defaults = defaults or {}
        self.ignore = ignore or []

        self.script_dir = None
        self.generated_script = None

    def _render(self):
        args = {}

        for target in self.targets:
            args[target.__name__] = {}

            type_hints = get_type_hints(target)

            logging.info(f"Type Hints: {type_hints}")

            patterns = []

            fullargspec = inspect.getfullargspec(target)
            if fullargspec.varargs:
                patterns.append(fullargspec.varargs)
            if fullargspec.varkw:
                patterns.append(fullargspec.varkw)

            patterns = patterns + self.ignore

            regex = "(" + ")|(".join(patterns) + ")"
            for arg in filter(lambda x: not re.match(regex, x), type_hints.keys()):
                annotation = type_hints[arg]

                # Check for compatible types in order of flexibility (e.g. str can represent float so is more flexible)
                if _is_compatible_type(annotation, str):
                    args[target.__name__][arg] = "string"
                elif _is_compatible_type(annotation, float):
                    args[target.__name__][arg] = "float"
                elif _is_compatible_type(annotation, int):
                    args[target.__name__][arg] = "int"
                elif _is_compatible_type(annotation, bool):
                    args[target.__name__][arg] = "float"

        template = _get_env().get_template("streamlit_render_fn.jinja")

        variables = {
            "render_fn_module_file": inspect.getmodule(
                self.render_fn_preamble
            ).__file__,
            "render_fn_name": self.render_fn_preamble.__name__,
            "targets": [target.__name__ for target in self.targets],
            "args": args,
            "defaults": self.defaults,
        }

        self.script_dir = tempfile.mkdtemp()

        self.generated_script = os.path.join(self.script_dir, "streamlit_render_fn.py")

        with open(self.generated_script, "w") as f:
            logging.info(
                f"Rendering streamlit_render_fn.jinja with variables: {variables}"
            )
            f.write(template.render(**variables))

    def start_server(self, host: str, port: int) -> None:
        self._render()

        env = os.environ.copy()
        env["LIGHTNING_FLOW_NAME"] = self.flow.name
        env["LIGHTNING_RENDER_FUNCTION"] = "render_fn"
        env["LIGHTNING_RENDER_MODULE_FILE"] = self.generated_script
        std_err_out = get_frontend_logfile("error.log")
        std_out_out = get_frontend_logfile("output.log")
        with open(std_err_out, "wb") as stderr, open(std_out_out, "wb") as stdout:
            self._process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    os.path.join(
                        os.path.dirname(lightning.frontend.__file__),
                        "streamlit_base.py",
                    ),
                    "--server.address",
                    str(host),
                    "--server.port",
                    str(port),
                    "--server.baseUrlPath",
                    self.flow.name,
                    "--server.headless",
                    "true",  # do not open the browser window when running locally
                ],
                env=env,
                stdout=stdout,
                stderr=stderr,
            )

    def stop_server(self) -> None:
        super().stop_server()

        if self.script_dir is not None:
            shutil.rmtree(self.script_dir)
            self.generated_script = None
            self.script_dir = None

    def __eq__(self, other):
        if isinstance(other, StreamlitAutoConfig):
            return all(
                [
                    self.targets == other.targets,
                    self.render_fn_preamble == other.render_fn_preamble,
                    self.defaults == other.defaults,
                ]
            )
        return False

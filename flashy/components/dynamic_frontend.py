import logging
import os
import pickle
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Union

from lightning import LightningFlow
from lightning.frontend import Frontend, StaticWebFrontend, StreamlitFrontend
from lightning.utilities.state import AppState


def _app_state_to_flow_scope(
    state: AppState, flow: Union[str, LightningFlow]
) -> AppState:
    """Returns a new AppState with the scope reduced to the given flow, as if the given flow as the root."""
    flow_name = flow.name if isinstance(flow, LightningFlow) else flow
    flow_name_parts = flow_name.split(".")[1:]  # exclude root
    flow_state = state
    for part in flow_name_parts:
        flow_state = getattr(flow_state, part)
    return flow_state


_index_html = """
<doctype html !>
<html>
<body>
<h1>Waiting...</h1>
</body>
</html>
"""


class _DummyFrontend(Frontend):
    def __init__(self):
        super().__init__()

        self._process = None

    def start_server(self, host: str, port: int) -> None:
        env = os.environ.copy()
        env["LIGHTNING_FLOW_NAME"] = self.flow.name
        env["LIGHTNING_HOST"] = host
        env["LIGHTNING_PORT"] = str(port)

        logging.info(f"Opening: {__file__}")

        self._process = subprocess.Popen(
            [
                sys.executable,
                __file__,
            ],
            env=env,
        )

    def stop_server(self) -> None:
        if self._process is not None:
            self._process.kill()


def _frontend_eq(a, b):
    if a == b:
        return True
    if (
        isinstance(a, StreamlitFrontend)
        and isinstance(b, StreamlitFrontend)
        and type(a) == type(b) == StreamlitFrontend
    ):
        return a.render_fn == b.render_fn
    return False


def _configure_layout_dynamic(self):
    frontend = self._configure_layout()

    self.frontend_bytes = pickle.dumps(frontend).decode("raw_unicode_escape")

    return _DummyFrontend()


class LightningFlowDynamic(LightningFlow):
    """Enable dynamic changing of the ``Frontend`` returned by a ``configure_layout`` call.

    .. note::

        The ``Frontend`` objects returned by the wrapped function should support ``__eq__`` to ensure that the frontend
        is only replaced if the object changes.
    """

    def __new__(cls, *args, **kwargs):

        if not hasattr(cls, "_configure_layout"):
            cls._configure_layout = cls.configure_layout
            cls.configure_layout = _configure_layout_dynamic

        return super().__new__(cls, *args, **kwargs)

    def __init__(self):
        super().__init__()

        self.frontend_bytes = None


_run = True


def _handler_stop_signals(signum, frame):
    global _run
    _run = False


class _MockFlow:
    def __init__(self, flow_name, flow_state):
        self.name = flow_name
        self._state = flow_state

    def __getattr__(self, item):
        return getattr(self._state, item)


def _get_flow():
    app_state = AppState()
    flow_state = _app_state_to_flow_scope(
        app_state, flow=os.environ["LIGHTNING_FLOW_NAME"]
    )
    flow = _MockFlow(os.environ["LIGHTNING_FLOW_NAME"], flow_state)
    return flow


if __name__ == "__main__":

    logging.info("Launching")

    web_dir = tempfile.mkdtemp()
    with open(os.path.join(web_dir, "index.html"), "w") as f:
        f.write(_index_html)

    static_frontend = StaticWebFrontend(web_dir)
    static_frontend.flow = _MockFlow(os.environ["LIGHTNING_FLOW_NAME"], None)
    static_frontend.start_server(
        os.environ["LIGHTNING_HOST"], int(os.environ["LIGHTNING_PORT"])
    )

    frontend = static_frontend

    signal.signal(signal.SIGINT, _handler_stop_signals)
    signal.signal(signal.SIGTERM, _handler_stop_signals)

    while _run:
        flow = _get_flow()
        if getattr(flow, "frontend_bytes", None) is not None:
            new_frontend = pickle.loads(
                flow.frontend_bytes.encode("raw_unicode_escape")
            )

            if not _frontend_eq(new_frontend, frontend):
                frontend.stop_server()
                frontend = new_frontend
                frontend.flow = flow
                logging.info(f"Launching {frontend}")
                frontend.start_server(
                    os.environ["LIGHTNING_HOST"], int(os.environ["LIGHTNING_PORT"])
                )

        time.sleep(0.5)

    logging.info("Stopping")
    frontend.stop_server()
    shutil.rmtree(web_dir)

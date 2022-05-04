import functools

from lightning.frontend import Frontend, StreamlitFrontend


class _DummyFrontend(Frontend):
    def __init__(self, dynamic_frontend):
        super().__init__()

        self._dynamic_frontend = dynamic_frontend

    def start_server(self, host: str, port: int) -> None:
        self._dynamic_frontend._host = host
        self._dynamic_frontend._port = port

    def stop_server(self) -> None:
        if self._dynamic_frontend._frontend is not None:
            self._dynamic_frontend._frontend.stop_server()


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


class _DynamicFrontend:
    def __init__(self, configure_layout):
        self._configure_layout = configure_layout

        self._host = None
        self._port = None

        self._frontend = None
        self._dummy_frontend = _DummyFrontend(self)

    def __call__(self, *args, **kwargs):
        new_frontend = self._configure_layout(*args, **kwargs)

        if not _frontend_eq(new_frontend, self._frontend):
            if self._host is not None and self._port is not None:
                if self._frontend is not None:
                    self._frontend.stop_server()
                self._frontend = new_frontend
                if self._frontend is not None:
                    self._frontend.flow = self._dummy_frontend.flow
                    self._frontend.start_server(self._host, self._port)

        return self._dummy_frontend


def dynamic_frontend(configure_layout):
    """Enable dynamic changing of the ``Frontend`` returned by a ``configure_layout`` call.

    .. note::

        The ``Frontend`` objects returned by the wrapped function should support ``__eq__`` to ensure that the frontend
        is only replaced if the object changes.
    """
    frontend = _DynamicFrontend(configure_layout)

    @functools.wraps(configure_layout)
    def wrapper(*args, **kwargs):
        return frontend.__call__(*args, **kwargs)

    return wrapper

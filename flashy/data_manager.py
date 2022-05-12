from typing import Any, Dict, Optional

import streamlit as st
from flash.image import ImageClassificationData
from flash.text import TextClassificationData
from lightning.frontend import StreamlitFrontend
from lightning.utilities.state import AppState

from flashy.components.dynamic_frontend import LightningFlowDynamic
from flashy.components.streamlit_auto_config import StreamlitAutoConfig
from flashy.utilities import add_flashy_styles

_TARGETS = {
    "image_classification": [
        ImageClassificationData.from_folders,
        ImageClassificationData.from_csv,
    ],
    "text_classification": [
        TextClassificationData.from_folders,
        TextClassificationData.from_csv,
    ]
}


class DataManager(LightningFlowDynamic):
    """The DataManager allows a user to configure the data module options for their task.

    Note:: We assume that users will provide validation data.
    """

    def __init__(self):
        super().__init__()

        self.config: Optional[Dict[str, Any]] = {}
        self.selected_task: Optional[str] = None
        self.defaults: Optional[Dict] = None

    def run(self, selected_task: str, defaults: Optional[Dict]):
        self.selected_task = selected_task.lower().replace(" ", "_")
        self.defaults = defaults
        self.config = defaults or {}

    def configure_layout(self):
        if self.selected_task is not None:
            if self.selected_task in _TARGETS:
                return StreamlitAutoConfig(
                    _TARGETS[self.selected_task],
                    render_fn,
                    defaults=self.defaults,
                    ignore=["test*", "predict*"],
                )
        return StreamlitFrontend(render_fn_unsupported)


@add_flashy_styles
def render_fn_unsupported(state: AppState) -> None:
    st.write("Currently only `image_classification` is supported.")


@add_flashy_styles
def render_fn(state: AppState) -> None:
    st.title(f"Load your data! {state.selected_task}")

    url = st.text_input("Data URL", (state.defaults or {}).get("url", ""))

    # TODO: Figure out why dict in state can't be mutated
    if url:
        state.config = {"url": url, **state.config}

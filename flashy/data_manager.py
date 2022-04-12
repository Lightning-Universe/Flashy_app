from typing import Any, Dict, Optional

import streamlit as st
from streamlit.script_request_queue import RerunData
from streamlit.script_runner import RerunException

from lightning import LightningFlow
from lightning.frontend import StreamlitFrontend
from lightning.utilities.state import AppState

import os
import sys

sys.path.append(os.path.dirname(__file__))

from utilities import add_flashy_styles


class DataManager(LightningFlow):
    """The DataManager allows a user to configure the data module options for their task.

    Note:: We assume that users will provide validation data.
    """

    def __init__(self):
        super().__init__()

        self.url: Optional[str] = None
        self.method: Optional[str] = None
        self.config: Optional[Dict[str, Any]] = None
        self.selected_task: Optional[str] = None

    def run(self, selected_task: str):
        self.selected_task = selected_task.lower().replace(" ", "_")

    def configure_layout(self):
        return StreamlitFrontend(render_fn=render_fn)


@add_flashy_styles
def render_fn(state: AppState) -> None:
    st.title("Load your data!")

    # TODO: Auto-generate this
    if state.selected_task == "image_classification":
        state.url = st.text_input("Data URL", "https://pl-flash-data.s3.amazonaws.com/hymenoptera_data.zip")

        state.method = st.selectbox("Data format", options=["folders", "csv"])

        if state.method == "folders":
            train_folder = st.text_input("Train folder", "hymenoptera_data/train/")
            val_folder = st.text_input("Validation folder", "hymenoptera_data/val/")
            if train_folder and val_folder:
                state.config = {
                    "train_folder": train_folder,
                    "val_folder": val_folder,
                }
        elif state.method == "csv":
            train_file = st.text_input("Train file")
            val_file = st.text_input("Validation file")
            if train_file and val_file:
                state.config = {
                    "train_file": train_file,
                    "val_file": val_file,
                }
    else:
        st.write("Currently only `image_classification` is supported.")

        st.write("""
            <a href="http://127.0.0.1:7501/view/Task" target="_parent">Go back</a>
        """, unsafe_allow_html=True)

    if state.config is not None:
        st.write("""
            Now <a href="http://127.0.0.1:7501/view/Model" target="_parent">set-up your model!</a>
        """, unsafe_allow_html=True)

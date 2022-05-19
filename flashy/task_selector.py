import functools

import streamlit as st
import torch
from flash import Trainer
from flash.text import TextClassificationData, TextEmbedder
from lightning import LightningFlow
from lightning.frontend import StreamlitFrontend
from lightning.utilities.state import AppState
from sentence_transformers import util

from flashy.utilities import add_flashy_styles

_DEMOS = {
    "ants & bees": (
        "image_classification",
        {
            "url": "https://pl-flash-data.s3.amazonaws.com/hymenoptera_data.zip",
            "target": "from_folders",
            "train_folder": "hymenoptera_data/train/",
            "val_folder": "hymenoptera_data/val/",
        },
    ),
    "IMDB Text Classification": (
        "text_classification",
        {
            "url": "https://pl-flash-data.s3.amazonaws.com/imdb.zip",
            "target": "from_csv",
            "input_field": "review",
            "target_fields": "sentiment",
            "train_file": "imdb/train.csv",
            "val_file": "imdb/valid.csv",
        },
    ),
}


@functools.lru_cache()
def get_embeddings_embedder():
    embeddings = torch.hub.load_state_dict_from_url(
        "https://grid-hackthon.s3.amazonaws.com/flashy/flashy_embeddings.pt"
    )
    embedder = TextEmbedder("sentence-transformers/all-MiniLM-L6-v2")
    return embeddings, embedder


class TaskSelector(LightningFlow):
    """The TaskSelector Flow enables a user to select the task they want to run."""

    def __init__(self):
        super().__init__()

        self.selected_task = None
        self.defaults = None

    def run(self) -> None:
        pass

    def configure_layout(self):
        return StreamlitFrontend(render_fn=render_fn)


@functools.lru_cache()
def get_suggested_tasks(question):
    query_datamodule = TextClassificationData.from_lists(
        predict_data=[question],
        batch_size=1,
    )

    embeddings, embedder = get_embeddings_embedder()

    trainer = Trainer()
    query_embedding = trainer.predict(embedder, datamodule=query_datamodule)[0][0]

    cos_scores = util.cos_sim(query_embedding, embeddings["corpus_embeddings"])[0]
    top_results = torch.topk(cos_scores, k=cos_scores.size(-1))

    return list(
        {
            embeddings["task_mapping"][int(result.item())]: None
            for result in top_results.indices
        }.keys()
    )[:3]


@add_flashy_styles
def render_fn(state: AppState) -> None:
    st.write("![logo](https://grid-hackthon.s3.amazonaws.com/flashy/logo.png)")

    st.markdown(
        '<p style="font-family:Courier; font-size: 25px;">Choose a pre-configured demo:</p>',
        unsafe_allow_html=True,
    )

    selected_demo = st.radio("", _DEMOS.keys())

    state.selected_task, state.defaults = _DEMOS[selected_demo]

    st.markdown(
        '<p style="font-family:Courier; font-size: 25px;">or describe what you want to build:</p>',
        unsafe_allow_html=True,
    )

    question = st.text_input(
        "",
        placeholder="e.g. an ants bees classifier",
    )

    if question:
        state.selected_task = None
        state.defaults = None
        with st.spinner("Loading..."):
            suggested_tasks = get_suggested_tasks(question)
    else:
        suggested_tasks = []

    if suggested_tasks:
        st.markdown(
            '<p style="font-family:Courier; font-size: 20px;">Suggested tasks</p>',
            unsafe_allow_html=True,
        )
        state.selected_task = st.radio("", suggested_tasks)

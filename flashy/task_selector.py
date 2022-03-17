import functools

import streamlit as st
from sentence_transformers import util
import torch
from flash.text import TextEmbedder, TextClassificationData
from flash import Trainer

from lightning import LightningFlow
from lightning.frontend import StreamlitFrontend
from lightning.utilities.state import AppState

from flashy.utilities import add_flashy_styles


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
        self.question = None

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

    return list({embeddings["task_mapping"][int(result.item())]: None for result in top_results.indices}.keys())[:3]


@add_flashy_styles
def render_fn(state: AppState) -> None:
    st.write("![logo](https://grid-hackthon.s3.amazonaws.com/flashy/logo.png)")

    st.markdown('<p style="font-family:Courier; font-size: 25px;">What do you want to build?</p>', unsafe_allow_html=True)

    question = st.text_input(
        "",
        placeholder="e.g. detect mask wearing in images",
    )

    if question:
        with st.spinner("Loading..."):
            suggested_tasks = get_suggested_tasks(question)
    else:
        suggested_tasks = []

    if suggested_tasks:
        st.markdown('<p style="font-family:Courier; font-size: 20px;">Suggested tasks</p>', unsafe_allow_html=True)
        state.selected_task = st.radio("", suggested_tasks)

        st.write("""
            Now <a href="http://127.0.0.1:7501/view/Data" target="_parent">configure your data!</a>
        """, unsafe_allow_html=True)

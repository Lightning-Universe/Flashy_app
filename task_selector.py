import functools

import streamlit as st
from sentence_transformers import util
import torch
import base64
from flash.text import TextEmbedder, TextClassificationData
from flash import Trainer

from lightning import LightningFlow
from lightning.frontend import StreamlitFrontend
from lightning.utilities.state import AppState


@functools.lru_cache(1)
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

    def configure_layout(self):
        return StreamlitFrontend(render_fn=render_fn)


@functools.lru_cache()
def get_suggested_tasks(question):
    if not question:
        return []
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


def set_bg_hack(main_bg):
    '''
    A function to unpack an image from root folder and set as bg.
    # https://discuss.streamlit.io/t/how-do-i-use-a-background-image-on-streamlit/5067/16

    Returns
    -------
    The background.
    '''
    # set bg name
    main_bg_ext = "png"
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )


def render_fn(state: AppState) -> None:
    st.set_page_config(layout="wide")
    set_bg_hack('Flashy.png')

    st.write("![logo](https://grid-hackthon.s3.amazonaws.com/flashy/logo.png)")

    st.markdown('<p style="font-family:Courier; font-weight:bold; font-size: 40px;">Choose your task</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-family:Courier; font-size: 25px;">What do you want to build?</p>', unsafe_allow_html=True)

    state.question = st.text_input(
        "",
        state.question if state.question else "",
        placeholder="e.g. detect mask wearing in images",
    )

    suggested_tasks = get_suggested_tasks(state.question)

    if suggested_tasks:
        st.markdown('<p style="font-family:Courier; font-size: 20px;">Suggested tasks</p>', unsafe_allow_html=True)
        index = suggested_tasks.index(state.selected_task) if state.selected_task else 0
        state.selected_task = st.radio("", suggested_tasks, index=index)

        st.write("""
            Now <a href="http://127.0.0.1:7501/view/Data" target="_parent">configure your data!</a>
        """, unsafe_allow_html=True)

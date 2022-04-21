import functools

import streamlit as st
from lightning.utilities.state import AppState


def set_bg():
    st.markdown(
        f"""
         <style>
         .stApp {{
             background: url(https://grid-hackthon.s3.amazonaws.com/flashy/background.png);
             background-size: cover
         }}
         </style>
         """,
        unsafe_allow_html=True,
    )


def add_flashy_styles(render_fn):
    @functools.wraps(render_fn)
    def decorator(state: AppState):
        st.set_page_config(layout="wide")
        set_bg()
        st.markdown(
            f"""
             <style>
             .stButton>button {{
                height: 25.59px;
             }}
             * {{
                font-size: 100%;
                font-family: Courier;
             }}
             .stSpinner>div:nth-child(2) {{
                height: 38.59px !important;
                width: 19.59px !important;
             }}
             </style>
             """,
            unsafe_allow_html=True,
        )
        render_fn(state)

    return decorator

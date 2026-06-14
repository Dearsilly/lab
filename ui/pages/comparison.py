"""中英文模型对比页面。"""
import sys, os, json, math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import requests
import plotly.graph_objects as go

API_URL = "http://127.0.0.1:5000/api/v1/score"


def load_lang(locale: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "i18n", f"{locale}.json")
    with open(path) as f:
        return json.load(f)


lang = st.session_state.get("lang", "zh")
t = load_lang(lang)

st.set_page_config(page_title=t["compare_title"], page_icon="🔄", layout="wide")
st.title(f"🔄 {t['compare_title']}")
st.caption(t["compare_description"])

if st.session_state.get("compare_clear_trigger", False):
    st.session_state.compare_input = ""
    st.session_state.compare_clear_trigger = False

essay_text = st.text_area(
    "输入作文",
    height=200,
    placeholder="输入一篇作文，系统将同时用中英文模型分别评分...",
    key="compare_input",
)

if st.button(f"🚀 {t['submit_btn']}", type="primary"):
    if not essay_text or not essay_text.strip():
        st.error(t["error_no_text"])
    elif len(essay_text) > 10000:
        st.error(t["error_too_long"])
    else:
        col_en, col_zh = st.columns(2)

        with col_en:
            st.subheader(f"🇬🇧 {t['compare_en_result']}")
            with st.spinner("Scoring with English model..."):
                try:
                    resp = requests.post(
                        API_URL,
                        json={"text": essay_text, "language": "en"},
                        timeout=30,
                    )
                    data = resp.json()
                    if data.get("success"):
                        score = data["score"]
                        if math.isfinite(score):
                            st.metric("Score", f"{score * 100:.1f}%")
                            st.progress(min(max(score, 0.0), 1.0))
                            scores = data.get("scores", {})
                            if scores:
                                for dim, val in scores.items():
                                    if dim != "total":
                                        st.caption(f"{dim}: {val:.3f}")
                        else:
                            st.warning("Invalid score")
                    else:
                        st.warning(data.get("error", "Failed"))
                except Exception as e:
                    st.error(f"Connection error: {e}")

        with col_zh:
            st.subheader(f"🇨🇳 {t['compare_zh_result']}")
            with st.spinner("正在使用中文模型评分..."):
                try:
                    resp = requests.post(
                        API_URL,
                        json={"text": essay_text, "language": "zh"},
                        timeout=30,
                    )
                    data = resp.json()
                    if data.get("success"):
                        score = data["score"]
                        if math.isfinite(score):
                            st.metric("分数", f"{score * 100:.1f}%")
                            st.progress(min(max(score, 0.0), 1.0))
                            scores = data.get("scores", {})
                            if scores:
                                for dim, val in scores.items():
                                    if dim != "total":
                                        st.caption(f"{dim}: {val:.3f}")
                        else:
                            st.warning("无效分数")
                    else:
                        st.warning(data.get("error", "评分失败"))
                except Exception as e:
                    st.error(f"连接错误: {e}")

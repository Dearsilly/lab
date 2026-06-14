"""AES 自动文本评分系统 — 主入口（评分页面）。"""
import sys, os, json, math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import requests
import plotly.graph_objects as go

from ui.components.radar_chart import render_radar_chart
from ui.components.feedback_card import render_feedback

API_URL = "http://127.0.0.1:5000/api/v1/score"


def load_lang(locale: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "i18n", f"{locale}.json")
    with open(path) as f:
        return json.load(f)


# ── Session init ─────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "zh"
if "result" not in st.session_state:
    st.session_state.result = None

# 处理清空操作：在 widget 创建之前重置值
if st.session_state.get("clear_trigger", False):
    st.session_state.essay_input = ""
    st.session_state.result = None
    st.session_state.clear_trigger = False

t = load_lang(st.session_state.lang)

st.set_page_config(
    page_title=t["app_title"],
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.title(f"⚙️ {t['sidebar_settings']}")

    is_zh = st.session_state.lang == "zh"
    lang_choice = st.radio(
        t["sidebar_language_switch"],
        ["中文", "English"],
        index=0 if is_zh else 1,
        horizontal=True,
    )
    new_lang = "zh" if lang_choice == "中文" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    t = load_lang(st.session_state.lang)

    st.divider()
    st.markdown(f"**{t['model_info']}**")
    try:
        resp = requests.get("http://127.0.0.1:5000/api/v1/models", timeout=2)
        if resp.status_code == 200:
            models = resp.json().get("models", {})
            for key, info in models.items():
                name = info.get("name", key)
                loaded = info.get("loaded")
                status = "✅" if loaded else "❌"
                st.caption(f"{status} {name}")
    except Exception:
        st.caption(f"❌ {t['error_no_api']}")

# ── Header ──────────────────────────────────────────────────────
st.title(f"📝 {t['app_title']}")
st.caption(t["app_subtitle"])
st.divider()

# ── Language selector ───────────────────────────────────────────
lang_choices = [t["language_auto"], t["language_en"], t["language_zh"]]
lang_choice_label = st.radio(
    t["language_label"],
    lang_choices,
    horizontal=True,
    index=0,
    key="content_lang_radio",
    label_visibility="collapsed",
)
lang_map = {t["language_auto"]: "auto", t["language_en"]: "en", t["language_zh"]: "zh"}
selected_lang = lang_map[lang_choice_label]

# ── Placeholder ─────────────────────────────────────────────────
if selected_lang == "zh":
    placeholder = "请在此输入中文作文...\n\n示例：\n在当今数字时代，人工智能技术正在深刻改变教育的方式与内涵..."
elif selected_lang == "en":
    placeholder = "Type or paste an English essay here...\n\nExample:\nTechnology has transformed modern education in profound ways..."
else:
    placeholder = (
        "输入中英文作文均可...\n\n"
        "中文示例：人工智能正在改变教育...\n"
        "English example: Technology has transformed..."
    )

essay_text = st.text_area(
    "作文 Essay",
    value=st.session_state.get("essay_input", ""),
    height=240,
    placeholder=placeholder,
    key="essay_input",
    label_visibility="collapsed",
)

# ── Stats bar ───────────────────────────────────────────────────
if essay_text:
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.caption(f"📊 {t['char_count']}: {len(essay_text)}/10000")
    with s2:
        st.caption(f"🔤 {t['word_count']}: {len(essay_text.split())}")
    with s3:
        zh_chars = len([c for c in essay_text if "一" <= c <= "鿿"])
        st.caption(f"🀄 {t['chinese_chars']}: {zh_chars}")
    with s4:
        prefix = "🌐" if selected_lang == "auto" else ("🇨🇳" if selected_lang == "zh" else "🇬🇧")
        st.caption(f"{prefix} {lang_choice_label}")

# ── Buttons ─────────────────────────────────────────────────────
btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 3])
with btn_c1:
    submit_btn = st.button(
        f"🚀 {t['submit_btn']}", type="primary", use_container_width=True,
        key="submit_main",
    )
with btn_c2:
    if st.button(f"🗑️ {t['clear_btn']}", use_container_width=True, key="clear_main"):
        st.session_state.clear_trigger = True
        st.rerun()

st.divider()

# ── Result Display ──────────────────────────────────────────────

if submit_btn:
    if not essay_text or not essay_text.strip():
        st.error(f"⚠️ {t['error_no_text']}")
    elif len(essay_text) > 10000:
        st.error(f"⚠️ {t['error_too_long']}")
    else:
        with st.spinner(f"⏳ {t['scoring']}"):
            try:
                resp = requests.post(
                    API_URL,
                    json={"text": essay_text, "language": selected_lang},
                    timeout=30,
                )
                data = resp.json()

                if data.get("success"):
                    st.session_state.result = data
                    score = data["score"]
                    scores = data.get("scores", {})
                    feedback = data.get("feedback", {})
                    detected_lang = data.get("language", "en")
                    elapsed = data.get("elapsed_ms", 0)

                    if not math.isfinite(score):
                        st.error("⚠️ 模型返回无效结果，请重试。")
                    else:
                        st.success(f"✅ {t['score_done']} ({elapsed}ms)")

                        # 中文降级提示
                        if selected_lang == "zh" or detected_lang == "zh":
                            try:
                                models_resp = requests.get(
                                    "http://127.0.0.1:5000/api/v1/models", timeout=2
                                )
                                if models_resp.status_code == 200:
                                    cn_loaded = models_resp.json().get(
                                        "models", {}
                                    ).get("zh", {}).get("loaded", False)
                                    if not cn_loaded:
                                        st.info(f"💡 {t['cn_fallback_warning']}")
                            except Exception:
                                pass

                        # ── Scores ──
                        g1, g2, g3 = st.columns([1, 1, 2])

                        with g1:
                            gauge_fig = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=score * 100,
                                number={"suffix": "%", "font": {"size": 36, "color": "#6366F1"}},
                                gauge={
                                    "axis": {"range": [0, 100], "tickwidth": 1},
                                    "bar": {"color": "#6366F1", "thickness": 0.25},
                                    "steps": [
                                        {"range": [0, 40], "color": "#FEE2E2"},
                                        {"range": [40, 70], "color": "#FEF3C7"},
                                        {"range": [70, 100], "color": "#D1FAE5"},
                                    ],
                                },
                            ))
                            gauge_fig.update_layout(
                                height=240, margin=dict(l=10, r=10, t=30, b=10)
                            )
                            st.plotly_chart(gauge_fig, use_container_width=True)

                        with g2:
                            st.metric(t["normalized_score"], f"{score:.4f}")
                            st.metric(t["percent_score"], f"{score * 100:.1f}")
                            st.progress(min(max(score, 0.0), 1.0))
                            lang_display = "🇨🇳 中文" if detected_lang == "zh" else "🇬🇧 English"
                            st.caption(f"{t['detected_language']}: {lang_display}")

                        with g3:
                            dim_labels = {
                                "content": t["content_dim"],
                                "structure": t["structure_dim"],
                                "language": t["language_dim"],
                            }
                            radar_fig = render_radar_chart(scores, labels=dim_labels)
                            st.plotly_chart(radar_fig, use_container_width=True)

                        # ── Feedback ──
                        fb_labels = {
                            "content": t["content_dim"],
                            "structure": t["structure_dim"],
                            "language": t["language_dim"],
                            "overall": t["overall"],
                        }
                        render_feedback(feedback, labels=fb_labels)

                elif resp.status_code >= 500:
                    st.error(f"🔴 {t['error_server']}: {data.get('error', '')}")
                else:
                    st.error(f"⚠️ {data.get('error', '')}")

            except requests.exceptions.ConnectionError:
                st.error(f"🔴 {t['error_no_api']}")
            except requests.exceptions.Timeout:
                st.error(f"⏱️ {t['error_timeout']}")
            except Exception as e:
                st.error(f"❌ {e}")

# ── Initial placeholder ─────────────────────────────────────────
if not st.session_state.get("result") and not submit_btn:
    st.info(f"👆 {t['placeholder_hint']}")

    with st.expander(f"📖 {t['guide_title']}"):
        st.markdown(t["guide_content"])

st.divider()
st.caption(t["footer_text"])

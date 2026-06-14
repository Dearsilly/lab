"""反馈卡片组件。"""
import streamlit as st


def render_feedback(feedback: dict[str, str], labels: dict[str, str] | None = None):
    """渲染三维度反馈卡片。

    Args:
        feedback: {"content": "...", "structure": "...", "language": "...", "overall": "..."}
        labels: 维度名称映射
    """
    if labels is None:
        labels = {
            "content": "内容 Content",
            "structure": "结构 Structure",
            "language": "语言 Language",
            "overall": "总结 Overall",
        }

    st.markdown("---")
    st.subheader(labels.get("overall", "总结"))
    st.info(feedback.get("overall", ""))

    cols = st.columns(3)
    dims = ["content", "structure", "language"]
    colors = ["#10B981", "#6366F1", "#F59E0B"]

    for col, dim, color in zip(cols, dims, colors):
        with col:
            st.markdown(
                f'<div style="background:{color}15;padding:12px;border-radius:8px;'
                f'border-left:3px solid {color};margin:4px 0;">'
                f'<strong style="color:{color}">{labels.get(dim, dim)}</strong>'
                f'<p style="margin:4px 0;font-size:0.9em;">{feedback.get(dim, "")}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )

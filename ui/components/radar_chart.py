"""维度评分雷达图组件。"""
import plotly.graph_objects as go
import plotly.express as px


def render_radar_chart(
    scores: dict[str, float],
    labels: dict[str, str] | None = None,
    height: int = 320,
):
    """渲染三维度雷达图（内容/结构/语言）。

    Args:
        scores: {"content": 0.82, "structure": 0.88, "language": 0.85}
        labels: 维度名称映射，如 {"content": "内容", ...}
        height: 图表高度
    """
    dims = ["content", "structure", "language"]
    if labels is None:
        labels = {"content": "Content", "structure": "Structure", "language": "Language"}

    values = [scores.get(d, 0) for d in dims]
    names = [labels.get(d, d) for d in dims]

    # 闭合雷达图
    values.append(values[0])
    names.append(names[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=names,
        fill="toself",
        fillcolor="rgba(99, 110, 250, 0.3)",
        line=dict(color="#6366F1", width=2),
        name="Score",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickfont=dict(size=10),
                gridcolor="rgba(0,0,0,0.1)",
            ),
            angularaxis=dict(
                gridcolor="rgba(0,0,0,0.1)",
            ),
        ),
        showlegend=False,
        margin=dict(l=30, r=30, t=10, b=10),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig

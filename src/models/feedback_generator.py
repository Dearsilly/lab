"""模板化反馈生成器：基于维度分数生成中英文评语。"""

# 英文反馈模板
EN_TEMPLATES = {
    "content": {
        "high": "Your arguments are clear and well-supported with specific examples. The essay demonstrates strong critical thinking.",
        "mid": "Your main points are present but could benefit from more concrete examples and deeper analysis.",
        "low": "The content lacks clear arguments and supporting evidence. Consider developing your thesis more fully.",
    },
    "structure": {
        "high": "Excellent essay structure with a clear introduction, logical paragraph flow, and a strong conclusion.",
        "mid": "The essay has a basic structure but transitions between paragraphs could be smoother.",
        "low": "The organization needs improvement. Add a clear introduction, use paragraphs effectively, and include a conclusion.",
    },
    "language": {
        "high": "Strong command of language with varied sentence structures and precise vocabulary.",
        "mid": "Generally correct grammar with some variety in sentence structure. Watch for occasional errors.",
        "low": "Frequent grammatical errors and limited vocabulary affect readability. Focus on sentence construction basics.",
    },
}

# 中文反馈模板
ZH_TEMPLATES = {
    "content": {
        "high": "论点明确，论证充分，举例恰当。展现了较强的思辨能力和逻辑思维。",
        "mid": "主要观点清晰，但论证深度和具体例证方面仍有提升空间。建议进一步展开论述。",
        "low": "文章观点不够明确，缺乏有力的论证支撑。建议围绕核心论点展开详细论述。",
    },
    "structure": {
        "high": "结构完整，层次分明。开头点题、段落衔接自然、结尾有力。",
        "mid": "基本结构完整，但段落之间的过渡可以更加流畅。建议加强各部分的逻辑衔接。",
        "low": "文章结构需要优化。建议增加明确的开头引入、合理安排段落层次、完善结尾总结。",
    },
    "language": {
        "high": "语言表达流畅，词汇丰富，句式多样。展现了良好的语言功底。",
        "mid": "语言基本通顺，但词汇和句式较为单一。注意润色表达，减少语病。",
        "low": "存在较多语病和用词不当。建议从基础语法和常用词汇入手，逐步提升表达能力。",
    },
}


def _get_level(score: float) -> str:
    """将 [0, 1] 区间分数映射为等级字符串。"""
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "mid"
    else:
        return "low"


def generate_feedback(
    scores: dict[str, float], language: str = "en"
) -> dict[str, str]:
    """根据维度分数生成反馈文字。

    Args:
        scores: {"total": 0.85, "content": 0.82, "structure": 0.88, "language": 0.85}
        language: "en" | "zh"

    Returns:
        {"content": "...", "structure": "...", "language": "...", "overall": "..."}
    """
    templates = ZH_TEMPLATES if language == "zh" else EN_TEMPLATES

    feedback = {}
    for dim in ["content", "structure", "language"]:
        dim_score = scores.get(dim, scores.get("total", 0.5))
        level = _get_level(dim_score)
        feedback[dim] = templates[dim][level]

    total_score = scores.get("total", 0.5)
    total_level = _get_level(total_score)

    if language == "zh":
        overall_map = {
            "high": f"总分表现优秀（{total_score * 100:.1f}分），文章在内容、结构和语言方面均表现良好。继续努力！",
            "mid": f"总分中等（{total_score * 100:.1f}分），文章有一定基础，建议针对反馈意见进行修改提升。",
            "low": f"总分偏低（{total_score * 100:.1f}分），需要在内容深度、文章结构和语言表达方面进行系统提升。",
        }
    else:
        overall_map = {
            "high": f"Overall score ({total_score * 100:.1f}/100) is strong. The essay performs well across content, structure, and language. Keep it up!",
            "mid": f"Overall score ({total_score * 100:.1f}/100) is adequate. Focus on the feedback suggestions to improve your writing.",
            "low": f"Overall score ({total_score * 100:.1f}/100) needs improvement. Work on developing content, organizing structure, and refining language.",
        }
    feedback["overall"] = overall_map[total_level]
    return feedback

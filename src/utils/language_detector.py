"""语言检测模块：基于 langdetect 自动检测中英文。"""
import re
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 42


def detect_language(text: str) -> str:
    """检测文本语言，返回 'zh' | 'en' | 'unknown'。

    先用简单的字符集规则快速判断，再用 langdetect 细粒度识别。
    """
    if not text or not text.strip():
        return "unknown"

    text = text.strip()

    # 快速规则：中文字符占比
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    english_chars = len(re.findall(r"[a-zA-Z]", text))
    total_chars = chinese_chars + english_chars

    if total_chars == 0:
        return "unknown"

    if chinese_chars / max(total_chars, 1) > 0.5:
        return "zh"
    if english_chars / max(total_chars, 1) > 0.8:
        return "en"

    # 混合文本用 langdetect
    try:
        result = detect(text)
        return "zh" if result.startswith("zh") else "en"
    except Exception:
        return "en"

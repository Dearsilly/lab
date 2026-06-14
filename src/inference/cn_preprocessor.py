"""中文文本预处理：清洗、jieba 分词、BERT tokenizer 封装。"""
import re
from typing import Optional


def clean_chinese_text(text: str) -> str:
    """清洗中文文本：繁简转换占位、全角半角、空白规范化。"""
    if not isinstance(text, str) or not text.strip():
        return ""

    # 全角转半角
    result = []
    for ch in text:
        code = ord(ch)
        if code == 0x3000:          # 全角空格
            result.append(" ")
        elif 0xFF01 <= code <= 0xFF5E:
            result.append(chr(code - 0xFEE0))
        elif 0x2018 <= code <= 0x2019:  # 中文引号
            result.append("'")
        elif 0x201C <= code <= 0x201D:
            result.append('"')
        else:
            result.append(ch)

    text = "".join(result)
    # 移除控制字符，保留中英文、数字、标点
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # 合并多个空白
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def segment_chinese(text: str) -> str:
    """使用 jieba 对中文文本分词（词间加空格，便于 BERT tokenizer 处理）。"""
    try:
        import jieba
    except ImportError:
        return text  # jieba 不可用时返回原文

    # 检测是否包含中文
    if not re.search(r"[一-鿿]", text):
        return text

    words = jieba.cut(text)
    return " ".join(words)


def preprocess_chinese(text: str, use_jieba: bool = True) -> str:
    """中文文本预处理流水线：清洗 → 分词 → 标准化。"""
    text = clean_chinese_text(text)
    if not text:
        return ""
    if use_jieba:
        text = segment_chinese(text)
    return text

"""高级推理引擎：多任务预测 + 语言路由 + 模型集成 + 反馈生成。"""
import math
import torch
import numpy as np
from typing import Optional

from src.inference.model_loader import load_model
from src.inference.preprocessor import preprocess
from src.inference.cn_preprocessor import preprocess_chinese
from src.utils.language_detector import detect_language
from src.models.advanced_model import AESMultiTaskModel, CNScoringModel
from src.models.feedback_generator import generate_feedback


class AdvancedPredictor:
    """多模型、多语言、多任务评分预测器。"""

    def __init__(
        self,
        en_model_path: str = "models/best_model.pt",
        cn_model_path: Optional[str] = None,
        en_model_name: str = "bert-base-uncased",
        cn_model_name: str = "bert-base-chinese",
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.en_model_path = en_model_path
        self.cn_model_path = cn_model_path
        self.en_model_name = en_model_name
        self.cn_model_name = cn_model_name

        self._en_model = None
        self._en_tokenizer = None
        self._cn_model = None
        self._cn_tokenizer = None

    def _get_en_model(self):
        if self._en_model is None:
            self._en_model, self._en_tokenizer, _ = load_model(
                self.en_model_path, self.device
            )
        return self._en_model, self._en_tokenizer

    def _get_cn_model(self):
        if self._cn_model is None and self.cn_model_path:
            self._cn_model, self._cn_tokenizer, _ = load_model(
                self.cn_model_path, self.device,
                model_name=self.cn_model_name,
                model_class=CNScoringModel,
            )
        return self._cn_model, self._cn_tokenizer

    def predict(
        self, text: str, language: str = "auto"
    ) -> dict:
        """预测单篇作文的分数和反馈。

        Args:
            text: 作文文本
            language: "auto" | "en" | "zh"

        Returns:
            {"score": float, "scores": {...}, "feedback": {...}, "language": str, ...}
        """
        if language == "auto":
            language = detect_language(text)

        # 中文且中文模型可用 → 用中文模型
        if language == "zh" and self.cn_model_path:
            return self._predict_chinese(text)

        # 中文但无中文模型 → 降级用英文模型 + 中文反馈
        if language == "zh" and not self.cn_model_path:
            result = self._predict_english(text)
            result["language"] = "zh"
            result["feedback"] = generate_feedback(result["scores"], language="zh")
            return result

        # 英文 → 英文模型 + 英文反馈
        return self._predict_english(text)

    def _predict_english(self, text: str) -> dict:
        text = preprocess(text)
        if not text:
            return self._error_result("Empty text after preprocessing")

        model, tokenizer = self._get_en_model()

        encoded = tokenizer(
            text, max_length=512, truncation=True, padding="max_length",
            return_tensors="pt",
        )
        input_ids = encoded["input_ids"].to(self.device)
        attention_mask = encoded["attention_mask"].to(self.device)

        with torch.no_grad():
            with torch.amp.autocast(
                "cuda" if self.device == "cuda" else "cpu",
                enabled=self.device == "cuda",
            ):
                output = model(input_ids, attention_mask)

            if isinstance(output, torch.Tensor):
                if output.dim() > 0 and output.shape[-1] >= 4:
                    # 多任务模型: 4 维输出
                    scores_np = output.cpu().numpy()[0]
                    scores = {
                        "total": round(float(scores_np[0]), 4),
                        "content": round(float(scores_np[1]), 4),
                        "structure": round(float(scores_np[2]), 4),
                        "language": round(float(scores_np[3]), 4),
                    }
                else:
                    # 单任务模型: 1 维输出
                    total = round(float(output.cpu().item()), 4)
                    scores = self._expand_to_dimensions(total)
            else:
                total = round(float(output.cpu().item()), 4)
                scores = self._expand_to_dimensions(total)

        # NaN 保护
        for k, v in scores.items():
            if not math.isfinite(v):
                scores[k] = 0.0

        feedback = generate_feedback(scores, language="en")

        return {
            "score": scores["total"],
            "scores": scores,
            "feedback": feedback,
            "language": "en",
            "error": None,
        }

    def _predict_chinese(self, text: str) -> dict:
        text = preprocess_chinese(text)
        if not text:
            return self._error_result("中文文本预处理后为空")

        model, tokenizer = self._get_cn_model()
        if model is None:
            return self._error_result("中文模型未加载")

        encoded = tokenizer(
            text, max_length=512, truncation=True, padding="max_length",
            return_tensors="pt",
        )
        input_ids = encoded["input_ids"].to(self.device)
        attention_mask = encoded["attention_mask"].to(self.device)

        with torch.no_grad():
            with torch.amp.autocast(
                "cuda" if self.device == "cuda" else "cpu",
                enabled=self.device == "cuda",
            ):
                output = model(input_ids, attention_mask)

            if output.dim() > 0 and output.shape[-1] >= 4:
                scores_np = output.cpu().numpy()[0]
                scores = {
                    "total": round(float(scores_np[0]), 4),
                    "content": round(float(scores_np[1]), 4),
                    "structure": round(float(scores_np[2]), 4),
                    "language": round(float(scores_np[3]), 4),
                }
            else:
                total = round(float(output.cpu().item()), 4)
                scores = self._expand_to_dimensions(total)

        for k, v in scores.items():
            if not math.isfinite(v):
                scores[k] = 0.0

        feedback = generate_feedback(scores, language="zh")

        return {
            "score": scores["total"],
            "scores": scores,
            "feedback": feedback,
            "language": "zh",
            "error": None,
        }

    def _expand_to_dimensions(self, total: float) -> dict:
        """单任务模型：从总分估算各维度分。"""
        return {
            "total": total,
            "content": round(total * 0.95, 4),
            "structure": round(total * 1.02, 4),
            "language": round(total * 1.03, 4),
        }

    def _error_result(self, msg: str) -> dict:
        return {
            "score": None,
            "scores": {},
            "feedback": {},
            "language": "unknown",
            "error": msg,
        }

    def batch_predict(
        self, items: list[dict]
    ) -> list[dict]:
        """批量预测。items: [{"id": ..., "text": ..., "language": "auto"}, ...]"""
        results = []
        for item in items:
            result = self.predict(
                text=item.get("text", ""),
                language=item.get("language", "auto"),
            )
            result["id"] = item.get("id", "")
            results.append(result)
        return results


# 全局单例
_predictor: Optional[AdvancedPredictor] = None


def get_advanced_predictor(
    en_model_path: str = "models/best_model.pt",
    cn_model_path: Optional[str] = None,
) -> AdvancedPredictor:
    global _predictor
    if _predictor is None:
        _predictor = AdvancedPredictor(
            en_model_path=en_model_path,
            cn_model_path=cn_model_path,
        )
    return _predictor

"""模型注册表：管理多模型的注册、查询和激活。"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelEntry:
    name: str
    path: str
    language: str         # "en" | "zh"
    model_type: str       # "short" | "long" | "multitask"
    version: str = "v1.0"
    qwk: float = 0.0
    loaded: bool = False


class ModelRegistry:
    """管理所有可用模型的注册信息。"""

    def __init__(self):
        self._models: dict[str, ModelEntry] = {}
        self._active: dict[str, str] = {}  # language -> model name

    def register(self, entry: ModelEntry):
        self._models[entry.name] = entry

    def get(self, name: str) -> Optional[ModelEntry]:
        return self._models.get(name)

    def list_all(self) -> list[ModelEntry]:
        return list(self._models.values())

    def list_by_language(self, language: str) -> list[ModelEntry]:
        return [m for m in self._models.values() if m.language == language]

    def activate(self, name: str):
        entry = self._models.get(name)
        if entry:
            self._active[entry.language] = name

    def get_active(self, language: str) -> Optional[ModelEntry]:
        name = self._active.get(language)
        if name:
            return self._models.get(name)
        # 回退：返回该语言第一个可用模型
        candidates = self.list_by_language(language)
        return candidates[0] if candidates else None

    def to_dict(self) -> dict:
        return {
            name: {
                "language": e.language,
                "type": e.model_type,
                "version": e.version,
                "qwk": e.qwk,
            }
            for name, e in self._models.items()
        }


# 全局单例
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry

"""ASAP 英文作文批量翻译为中文（Google Translate 版）。

使用 deep-translator (Google Translate)，质量远优于 Helsinki 模型。
支持断点续传，每 50 条保存一次。
"""
import os
import sys
import time
import argparse
import pandas as pd
from pathlib import Path
from tqdm import tqdm


def translate_text(text: str, retries: int = 3) -> str:
    """翻译单条文本，带重试机制。"""
    from deep_translator import GoogleTranslator

    # 截断过长文本（Google Translate 有长度限制）
    if len(text) > 3000:
        text = text[:3000]

    for attempt in range(retries):
        try:
            result = GoogleTranslator(source="en", target="zh-CN").translate(text)
            return result
        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 2
                time.sleep(wait)
            else:
                print(f"\n  Translation failed after {retries} tries: {e}")
                return text  # 失败时返回原文

    return text


def main():
    parser = argparse.ArgumentParser(description="Translate ASAP essays to Chinese (Google)")
    parser.add_argument("--input", default="data/raw/asap/asap_all.csv")
    parser.add_argument("--output", default="data/raw/chinese/asap_zh.csv")
    parser.add_argument("--max-samples", type=int, default=2000,
                        help="Max essays to translate (default: 2000)")
    parser.add_argument("--delay", type=float, default=0.3,
                        help="Delay between translations in seconds (default: 0.3)")
    parser.add_argument("--no-resume", action="store_true",
                        help="Don't resume from existing output")
    args = parser.parse_args()

    # 加载数据
    df = pd.read_csv(args.input)
    print(f"Source: {len(df)} essays")

    if args.max_samples and len(df) > args.max_samples:
        n_sets = df["essay_set"].nunique()
        per_set = max(1, args.max_samples // n_sets)
        sampled = []
        for es in sorted(df["essay_set"].unique()):
            subset = df[df["essay_set"] == es]
            n = min(len(subset), per_set)
            sampled.append(subset.sample(n=n, random_state=42))
        df = pd.concat(sampled, ignore_index=True)
        print(f"Sampled {len(df)} essays (stratified by essay_set)")

    # 断点续传
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.no_resume and output_path.exists():
        existing = pd.read_csv(output_path)
        done_ids = set(existing["essay_id"].astype(str))
        df = df[~df["essay_id"].astype(str).isin(done_ids)]
        print(f"Resuming: {len(df)} remaining ({len(existing)} done)")
        results = [existing]
    else:
        results = []

    if len(df) == 0:
        print("All done!")
        return

    texts = df["essay_text"].tolist()
    ids = df["essay_id"].tolist()
    sets = df["essay_set"].tolist()
    scores = df["score"].tolist()

    save_interval = 50
    start_time = time.time()

    for i in tqdm(range(len(texts)), desc="Translating"):
        zh = translate_text(texts[i])
        results.append(pd.DataFrame([{
            "essay_id": ids[i],
            "essay_set": sets[i],
            "essay_text": zh,
            "score": scores[i],
        }]))

        if len(results) % save_interval == 0:
            pd.concat(results, ignore_index=True).to_csv(output_path, index=False)

        time.sleep(args.delay)

    final = pd.concat(results, ignore_index=True)
    final.to_csv(output_path, index=False)
    elapsed = time.time() - start_time
    print(f"\nDone! {len(final)} essays in {elapsed:.0f}s ({elapsed/len(final):.1f}s/essay)")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()

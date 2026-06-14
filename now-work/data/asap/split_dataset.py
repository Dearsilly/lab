import pandas as pd
import os

input_file = "training_set_rel3.tsv"
output_dir = "asap_split_sets"
os.makedirs(output_dir, exist_ok=True)

try:
    df = pd.read_csv(input_file, sep="\t", encoding="cp1252")
except UnicodeDecodeError:
    df = pd.read_csv(input_file, sep="\t", encoding="latin1")

print("原始数据形状:", df.shape)

for set_id in sorted(df["essay_set"].unique()):
    subset = df[df["essay_set"] == set_id]
    output_file = os.path.join(output_dir, f"training_set_rel3_set{set_id}.tsv")
    subset.to_csv(output_file, sep="\t", index=False, encoding="utf-8-sig")
    print(f"Set {set_id} -> {len(subset)} essays")

print("拆分完成")
"""批量评分页面：CSV 上传 + 进度 + 结果表格 + 下载。"""
import sys, os, json, io, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:5000/api/v1/batch"


def load_lang(locale: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "i18n", f"{locale}.json")
    with open(path) as f:
        return json.load(f)


lang = st.session_state.get("lang", "zh")
t = load_lang(lang)

st.set_page_config(page_title=t["batch_title"], page_icon="📊", layout="wide")
st.title(f"📊 {t['batch_title']}")

# ── 模板下载 ────────────────────────────────────────────────────

template_csv = "essay_id,text,language\n1,This is a sample English essay for scoring.,en\n2,这是一篇中文作文示例用于评分。,zh"  # noqa

st.download_button(
    f"📥 {t['batch_template_download']}",
    template_csv,
    "batch_template.csv",
    "text/csv",
)

st.caption(f"💡 {t['batch_template_hint']}")

# ── 上传 ────────────────────────────────────────────────────────

uploaded_file = st.file_uploader(t["batch_upload"], type=["csv"])

if uploaded_file:
    # 预览
    df_preview = pd.read_csv(uploaded_file)
    st.write(f"**预览** ({len(df_preview)} 篇作文)")
    st.dataframe(df_preview.head(10), use_container_width=True)

    if st.button(f"🚀 {t['submit_btn']}", type="primary"):
        uploaded_file.seek(0)

        with st.spinner(f"⏳ {t['batch_processing']}"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                resp = requests.post(
                    API_URL,
                    files={"file": ("batch.csv", uploaded_file, "text/csv")},
                    timeout=300,
                )
                data = resp.json()

                if data.get("success"):
                    progress_bar.progress(1.0)
                    status_text.success(f"✅ {t['batch_done']}: {data['completed']}/{data['total']}")

                    # 结果表格
                    results = data.get("results", [])
                    if results:
                        df = pd.DataFrame(results)

                        # 格式化
                        if "score" in df.columns:
                            df["percent"] = df["score"].apply(
                                lambda x: f"{x * 100:.1f}%" if x is not None else "N/A"
                            )

                        st.dataframe(df, use_container_width=True)

                        # 下载
                        csv_out = df.to_csv(index=False)
                        st.download_button(
                            f"📥 {t['batch_download']}",
                            csv_out,
                            f"batch_results_{int(time.time())}.csv",
                            "text/csv",
                        )
                else:
                    st.error(data.get("error", "Batch scoring failed"))

            except requests.exceptions.ConnectionError:
                st.error(f"🔴 {t['error_no_api']}")
            except Exception as e:
                st.error(f"❌ {e}")

import streamlit as st
import requests

st.set_page_config(page_title="作文评分API", page_icon="📝", layout="centered")

st.title("📝 作文评分API测试工具")

# API base URL
api_url = "http://localhost:5000"

# API 状态检查
st.sidebar.header("API 连接")
api_status = st.sidebar.checkbox("启用实时API调用", value=True)

if st.sidebar.button("测试API连接"):
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ API 连接正常")
            st.sidebar.json(response.json())
        else:
            st.sidebar.error("❌ API 返回错误状态")
    except Exception as e:
        st.sidebar.error(f"❌ 连接失败: {e}")

# 获取分数范围
if st.sidebar.button("获取分数范围"):
    try:
        response = requests.get(f"{api_url}/score-ranges")
        ranges = response.json()["score_ranges"]
        st.sidebar.json(ranges)
    except Exception as e:
        st.sidebar.error(f"获取失败: {e}")

# 主界面 - 评分测试
st.subheader("作文评分测试")

col1, col2 = st.columns(2)

with col1:
    essay_text = st.text_area("输入作文", height=200, placeholder="输入你的作文...")
    essay_set = st.selectbox("选择作文Set", [1, 2, 3, 4, 5, 6, 7, 8])

with col2:
    if st.button("🎯 预测分数", type="primary"):
        if essay_text and api_status:
            with st.spinner("正在预测..."):
                try:
                    response = requests.post(
                        f"{api_url}/predict",
                        json={"essay": essay_text, "essay_set": essay_set},
                        timeout=30
                    )
                    result = response.json()
                    
                    if "error" in result:
                        st.error(f"错误: {result['error']}")
                    else:
                        st.success("预测成功!")
                        st.json(result)
                except Exception as e:
                    st.error(f"API调用失败: {e}")
        else:
            st.warning("请输入作文并启用API连接")

# 示例数据
st.markdown("---")
st.subheader("📚 示例作文")
examples = {
    1: "Dear local newspaper, computers have changed our world...",
    2: "I believe books should not be removed from libraries...",
    3: "The author concludes the story with an important lesson...",
}

for essay_set, text in examples.items():
    with st.expander(f"Set {essay_set} 示例"):
        st.code(text, language="text")

# 页脚
st.markdown("---")
st.caption("Flask-RESTful API + Streamlit 作文评分系统")

import streamlit as st
import requests
import json

# 页面配置
st.set_page_config(
    page_title="作文评分系统",
    page_icon="📝",
    layout="centered"
)

# 标题
st.title("📝 作文评分系统")
st.markdown("---")

# 获取分数范围
def get_score_ranges():
    try:
        response = requests.get("http://localhost:5000/score-ranges")
        return response.json()["score_ranges"]
    except:
        return None

# 预测作文分数
def predict_essay(essay, essay_set=None):
    url = "http://localhost:5000/predict"
    data = {"essay": essay}
    if essay_set:
        data["essay_set"] = essay_set
    
    try:
        response = requests.post(url, json=data, timeout=30)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# 检查 API 连接
def check_api_connection():
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# 侧边栏
with st.sidebar:
    st.header("📚 作文题目")
    
    # 获取分数范围
    score_ranges = get_score_ranges()
    if score_ranges:
        essay_set = st.selectbox(
            "选择作文 Set",
            options=list(score_ranges.keys()),
            format_func=lambda x: f"Set {x} ({score_ranges[x][0]}-{score_ranges[x][1]}分)"
        )
    else:
        essay_set = st.selectbox(
            "选择作文 Set",
            options=[1, 2, 3, 4, 5, 6, 7, 8]
        )
    
    # API 状态
    api_status = check_api_connection()
    st.markdown("---")
    if api_status:
        st.success("✅ API 连接正常")
    else:
        st.error("❌ API 连接失败")
    
    st.markdown("### API 信息")
    st.info(f"端点: http://localhost:5000")
    st.info(f"设备: CUDA/CPU (根据API返回)")

# 主区域
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("✏️ 输入作文")
    essay_text = st.text_area(
        "请在此输入你的作文内容...",
        height=250,
        placeholder="Dear local newspaper, I believe that..."
    )

with col2:
    st.subheader("📊 预测分数")
    if score_ranges:
        score_min, score_max = score_ranges[essay_set]
        st.metric(
            label=f"Set {essay_set} 分数范围",
            value=f"{score_min}-{score_max}分"
        )
    
    # 预测按钮
    if st.button("🎯 预测分数", type="primary", use_container_width=True):
        if essay_text and len(essay_text.strip()) > 0:
            with st.spinner("正在分析作文..."):
                result = predict_essay(essay_text, int(essay_set))
            
            if "error" in result:
                st.error(f"预测失败: {result['error']}")
            else:
                # 显示预测结果
                st.markdown("---")
                st.subheader("🎯 预测结果")
                
                predicted_score = result["predicted_score"]
                st.metric(
                    label="预测分数",
                    value=f"{predicted_score:.1f} 分",
                    delta=None
                )
                
                # 分数展示
                st.markdown(f"**作文 Set**: {result['essay_set']}")
                st.markdown(f"**分数范围**: {result['score_range'][0]} - {result['score_range'][1]} 分")
                
                # 进度条显示分数位置
                range_min, range_max = result['score_range']
                percentage = (predicted_score - range_min) / (range_max - range_min)
                st.progress(percentage)
                
                # 评估反馈
                if percentage >= 0.7:
                    st.success("🎉 优秀！作文质量很高")
                elif percentage >= 0.5:
                    st.info("👍 良好！作文质量不错")
                elif percentage >= 0.3:
                    st.warning("✏️ 中等！可以进一步改进")
                else:
                    st.error("📝 需要更多练习和改进")
        else:
            st.warning("⚠️ 请先输入作文内容")

# 显示示例作文
with st.expander("📖 查看示例作文"):
    st.markdown("""
    **示例 1 (Set 1):**
    > Dear local newspaper, I think that computers have greatly changed our society. They help us learn new things and communicate with people around the world.
    
    **示例 2 (Set 2):**
    > I believe that books should not be removed from libraries because they are important for learning and entertainment.
    
    **示例 3 (Set 4):**
    > The author concludes the story by showing that the main character learned an important lesson about friendship.
    """)

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "作文评分系统 - BERT模型驱动 | Flask-RESTful API | Streamlit"
    "</div>",
    unsafe_allow_html=True
)

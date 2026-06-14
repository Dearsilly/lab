# 课题3：基于深度学习的文本作业自动评分系统

## 项目描述

针对纯文本作业（作文、简答题、论述题），通过预训练模型理解语义内容并自动评分，生成基础反馈，提升评分效率与一致性。

## 核心数据集

### ASAP 数据集（Automated Student Assessment Prize）

包含 8 个作文任务的 24,000 篇学生作文及人工评分（1-6 分），覆盖不同学段和主题。

- 下载地址：[Kaggle ASAP 竞赛数据集](https://www.kaggle.com/c/asap-aes)

### PeerRead 数据集

包含 14,000 篇计算机科学论文摘要及同行评审评分，适合学术类文本评分任务。

- 下载地址：[GitHub PeerRead](https://github.com/allenai/peer-read)

### 自建数据集

收集学校课程的简答题 / 论述题（如语文阅读理解、历史论述），标注得分点与对应分数（可通过教育机构合作获取）。

## 关键开源代码与工具

### 文本预处理与模型训练

- **Hugging Face Transformers**（<https://github.com/huggingface/transformers>）：提供 BERT、RoBERTa 等预训练模型，支持文本评分任务微调。
- **spaCy**（<https://github.com/explosion/spaCy>）：用于文本分词、词性标注、实体识别等预处理。
- **文本评分基线代码**（<https://github.com/neuralmind-ai/bert-score>）：基于 BERT 的文本评分示例，可直接适配作业评分场景。

### 系统部署与交互

- **Flask-RESTful**（<https://github.com/flask-restful/flask-restful>）：构建作业上传与评分 API 服务。
- **Streamlit**（<https://github.com/streamlit/streamlit>）：快速开发可视化界面，展示评分结果与文本分析。

## 项目信息

- **地点**：苏州
- **组数**：2 组，每组 3~4 人
- **技术要求**：前后端技术，Python 及常用框架，机器学习基础

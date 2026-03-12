# 项目介绍：
### 1.数据集保存在data/aspa文件目录下，training_set_rel3.tsv是基础数据集，valid_set.tsv是基础数据验证集。
### 2.几个重要的py文件及执行顺序：
```
data_preprocess.py用作数据预处理->
train_model.py在数据与处理的基础上初步训练模型，调用GPU加速（不同的电脑需要根据自己的配置安装GPU，修改相应的代码）->
train_high_score.py是对前者的补充，因为基础数据集包括八个set，每个set的评分标准不一样、满分也不一样（可以自己打开tsv文件查看一下），所以我们提取数据集中的第八组（用的是extract_high_score_essays.py）（这一组集合满分是60）（也可以用分数占满分的比值来进行训练，但效果不是很好，有待进一步优化）->
infer_score.py是最终评分文件，将要评分的作文粘贴到该文件中的main函数下的test_essay参数中，执行就可以得到模型的评分输出
```
### 3.建议在项目根目录下使用虚拟环境venv

### 4.其他的py脚本大部分做测试用，不是重点

### 5.git的使用：
```
每次开始前先fetch比较差异（pull会直接覆盖本地，不显示差异，慎用）
结束时push到git仓库，如果不push别人不知道你的更改；push时有问题谨慎处理，不然会污染仓库
commit时尽量描述清楚行为，包括做了什么、修改了什么、新增了什么、有什么功能等，越详细越好
```
```angular2html
txy 10.27
```
## 10.30补充
## 环境配置指南
### 1. 虚拟环境搭建
```
1. 创建虚拟环境（项目根目录下）
python -m venv .venv

2. 激活虚拟环境（Windows PowerShell）
.venv\Scripts\activate

#若激活失败，尝试执行以下命令后重新激活（解决权限问题）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
### 2. 安装依赖包
```
1. 先更新pip
python.exe -m pip install --upgrade pip

2. 安装项目核心依赖（确保requirements.txt已生成）
pip install -r requirements.txt

3. 安装PyTorch（CUDA 11.7版本，适配NVIDIA 2060等显卡）
pip install torch==1.13.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117

4. 下载spaCy英文模型（必须单独执行）
python -m spacy download en_core_web_sm
```
### 3. 环境验证
```
1. 验证核心库是否安装成功
python test_all_libs.py

2. 验证GPU是否可用（需安装PyTorch后执行）
python test_gpu.py

#若输出均为 ✅ 则环境正常；若出现 ❌ 错误，根据提示修复对应库的安装。
```



# 完整操作流程
## 1. 数据预处理
### 处理原始数据，生成训练/验证集（仅需执行一次）
```
python data_preprocess.py
```
输出文件：data/asap/train_cleaned_essay8.csv（训练集）、
data/asap/valid_cleaned_essay8.csv（验证集）、
data/asap/train_high_score_essay8.csv（高分样本集）
若提示缺少数据集，请确认 data/asap/training_set_rel3.tsv 已存在。

## 2. 模型训练
### 第一步：基础模型训练（使用全部样本）
```
python train_model.py
```

### 第二步：高分样本精调（基于基础模型优化）
```
python train_high_score.py
```
模型保存路径：saved_model/bert_asap_essay8（基础模型）、saved_model/bert_asap_essay8_high_score（精调模型）
训练过程日志保存在 logs_regression 目录，可通过 TensorBoard 查看：tensorboard --logdir=logs_regression

### 第三步：作文评分（推理）
```
运行评分脚本，输出预测分数
python infer_score.py
```
如需评分新作文，修改 infer_score.py 中 test_essay 变量的文本内容即可。
评分范围：10-60 分（与第八组数据集满分一致）。


# 项目结构说明
#### ├── data/asap/ # 数据集目录（原始数据 + 预处理后数据）
#### ├── saved_model/ # 训练好的模型保存目录
#### ├── logs_regression/ # 训练日志
#### ├── requirements.txt # 依赖清单
#### ├── data_preprocess.py # 数据预处理
#### ├── train_model.py # 基础模型训练
#### ├── train_high_score.py # 高分样本精调
#### ├── infer_score.py # 作文评分（推理）
#### └── 各类测试脚本（test_*.py） # 环境验证、功能测试
```angular2html
txy 10.30
```

## 环境配置
### 1.所有人执行

#### (1)创建虚拟环境（项目根目录下）
```python -m venv .venv``` 

#### (2) 激活虚拟环境
```angular2html
.venv\Scripts\activate
```

#### (3) 安装项目核心依赖 (注：我用的是python3.10，建议用python3.10版本相近的，如python3.10，如若安装时报错，建议切换与python3.10接近的版本)
```pip install -r env/requirements_new.txt```

### 2.5060主机另外执行
```pip install -r env/requirements_gpu5060.txt```

### 3.环境检查
####  检查Python依赖
```python env/check_env.py```

#### 检查GPU（5060主机检查）
```python env/check_gpu.py```

### 4.训练
```python -m src.train```
## 数据说明

```data/asap/asap_split_sets```中的文件为```training_set_rel3.tsv```按照```essay_set(1-8)```分为的8个文件
(貌似并没有什么用)

```wjk(25.3.12)```


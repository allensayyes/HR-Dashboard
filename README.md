# HR Attrition & Gap Prediction Platform

## 项目简介
本项目是一个基于 **Streamlit + FastAPI + SQLite** 的可视化人力预测平台，核心功能包括：
- **离职预测（Attrition Prediction）**：基于员工画像、绩效、团队稳定性、薪酬竞争力、竞争对手与宏观环境等特征，输出员工级别的离职概率，并聚合得到预计离职人数。
- **缺口预测（Gap Prediction）**：结合预计离职人数、业务增长、招聘难度（TTF/Offer）、竞争对手、宏观/政策/地区供需，以及编制批复，预测部门级的人力缺口。

## 主要功能
- 📊 **指标大盘**：关键人力指标（任期、离职率、招聘进度）及动态趋势
- 🔎 **风险与亮点**：条件格式化表格，高亮异常点
- 📈 **预测可视化**：
  - Sankey 图展示离职/缺口预测因果链路
  - 特征重要性解释模型逻辑
- ⚙️ **模型方法**：
  - 离职预测模型：逻辑回归 / 随机森林 / XGBoost（可切换）
  - 缺口预测模型：时间序列 + 回归融合
  - 采用校准 (calibration) 输出概率分布

## 技术栈
- **前端**：Streamlit
- **API 层**：FastAPI
- **数据存储**：SQLite
- **建模**：scikit-learn, XGBoost
- **可视化**：Plotly, Matplotlib, Pandas Styler

## 运行方式
1. 克隆仓库
   git clone https://github.com/yourname/hr-attrition-gap.git
   cd hr-attrition-gap

2. 安装依赖
   pip install -r requirements.txt

3. 启动平台
   streamlit run App_full.py

## 文件结构
.
├── App_full.py        # 主应用入口
├── api/               # FastAPI 相关接口
├── data/              # 示例数据
├── models/            # 训练好的模型文件
├── requirements.txt   # 依赖清单
├── README.md
└── .gitignore
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =========================
# 模拟数据
# =========================
np.random.seed(42)
departments = ["产品", "技术", "市场", "运营", "客服"]
levels = ["L3", "L4", "L5", "L6", "L7"]
perf_levels = ["C", "B", "B+", "A", "S"]

df = pd.DataFrame({
    "emp_id": range(1, 301),
    "department": np.random.choice(departments, 300),
    "level": np.random.choice(levels, 300, p=[0.25,0.3,0.25,0.15,0.05]),
    "tenure_months": np.random.randint(1, 120, 300),
    "performance": np.random.choice(perf_levels, 300),
    "promotion_wait": np.random.randint(1, 60, 300),
    "salary": np.random.randint(8, 50, 300) * 1000,
    "leave_prob": np.random.rand(300)
})

recruit = pd.DataFrame({
    "department": departments,
    "hc": [50, 80, 40, 70, 60],
    "forecast_headcount": [45, 75, 38, 60, 55],
    "forecast_gap": [-5, -5, -2, -10, -5],
    "offer_accept_rate": [0.85, 0.78, 0.8, 0.75, 0.7],
    "time_to_fill": [25, 35, 28, 40, 45]
})

# =========================
# 页面设置
# =========================
st.set_page_config(page_title="人力资源分析仪表盘", layout="wide")
st.title("📊 人力资源经营分析 Demo")

# =========================
# KPI 卡片
# =========================
col1, col2, col3 = st.columns(3)
col1.metric("现有员工数", len(df))
col2.metric("预测离职数", int(df["leave_prob"].sum()))
col3.metric("预测缺口数", int(recruit["forecast_gap"].sum()))

st.markdown("---")

# =========================
# 筛选器
# =========================
dept_filter = st.multiselect("选择部门", departments, default=departments)
level_filter = st.multiselect("选择职级", levels, default=levels)
df_filtered = df[df["department"].isin(dept_filter) & df["level"].isin(level_filter)]

# =========================
# 部门/职级分析
# =========================
st.header("👥 部门 & 职级分析")

# 部门员工数
dept_bar = df_filtered.groupby("department")["emp_id"].count().reset_index()
fig_dept = px.bar(dept_bar, x="emp_id", y="department", orientation="h", title="部门员工数")
st.plotly_chart(fig_dept, use_container_width=True)

# 职级员工数
level_bar = df_filtered.groupby("level")["emp_id"].count().reset_index()
fig_level = px.bar(level_bar, x="emp_id", y="level", orientation="h", title="职级员工数")
st.plotly_chart(fig_level, use_container_width=True)

st.markdown("---")

# =========================
# 现存人员详情
# =========================
st.header("📌 现存人员详情")

col1, col2 = st.columns(2)

with col1:
    fig_tenure = px.histogram(df_filtered, x="tenure_months", nbins=20, title="工龄分布（月）")
    st.plotly_chart(fig_tenure, use_container_width=True)

    fig_promo = px.histogram(df_filtered, x="promotion_wait", nbins=20, title="距上次晋升（月）")
    st.plotly_chart(fig_promo, use_container_width=True)

with col2:
    fig_perf = px.histogram(df_filtered, x="performance", title="绩效分布")
    st.plotly_chart(fig_perf, use_container_width=True)

    fig_salary = px.histogram(df_filtered, x="salary", nbins=20, title="薪资分布")
    st.plotly_chart(fig_salary, use_container_width=True)

# 离职概率分布
fig_leave = px.histogram(df_filtered, x="leave_prob", nbins=20, title="离职概率分布")
st.plotly_chart(fig_leave, use_container_width=True)

st.markdown("---")

# =========================
# 招聘数据详情
# =========================
st.header("📈 招聘数据详情")

col1, col2 = st.columns(2)

with col1:
    fig_hc = px.bar(recruit, x="forecast_headcount", y="department", orientation="h",
                    title="部门编制 vs 预测在岗", color="forecast_gap",
                    labels={"forecast_headcount": "预测在岗"})
    st.plotly_chart(fig_hc, use_container_width=True)

with col2:
    fig_offer = px.bar(recruit, x="offer_accept_rate", y="department", orientation="h",
                       title="Offer 接受率", text="offer_accept_rate")
    st.plotly_chart(fig_offer, use_container_width=True)

# Time to Fill
fig_ttf = px.bar(recruit, x="time_to_fill", y="department", orientation="h", title="招聘周期 (TTF, 天)")
st.plotly_chart(fig_ttf, use_container_width=True)

# 数据表
st.subheader("招聘明细数据表")
st.dataframe(recruit)

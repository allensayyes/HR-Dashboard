# -*- coding: utf-8 -*-
# HR Dashboard — Corporate only (no riders)
# 保留原有版式：顶部Sticky筛选 + KPI卡 + 现有人员详情 + 招聘数据详情 + 风险预警/突出亮点 + 下载区
# 新增：更强的部门/级别差异化；KPI卡伪造但“自洽”的环比箭头；全中文轴/标签；缺口百分比口径；绩效=数值系数

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime


# ---------------- 基本设置 ----------------
st.set_page_config(page_title="人力资源 数据报表（Corporate）", layout="wide")
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown("<h2 style='text-align:center;margin-top:-10px'>人力资源 数据报表 Demo </h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:right;color:#777'>最新更新时间：{now_str}</p>", unsafe_allow_html=True)
#
# ## 顶部 sticky 筛选条
# components.html("""
# <style>
# .sticky {
#   position: -webkit-sticky;
#   position: sticky;
#   top: 0;
#   background-color: white;
#   padding: 10px 0;
#   z-index: 100;
#   border-bottom: 1px solid #eee;
# }
# </style>
# """, height=60)
#
# st.markdown("<div class='sticky'>", unsafe_allow_html=True)
#
# # 示例筛选器
# with st.container():
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         dept_sel = st.multiselect("选择部门", ["技术","产品","运营","财务","人力"], default=["技术","产品"])
#     with col2:
#         level_sel = st.multiselect("选择级别", ["P5","P6","P7","P8"], default=["P6","P7"])
#     with col3:
#         biz_sel = st.multiselect("选择业务线", ["到店","到家","出行","其他"], default=["到店","到家"])
#
# st.markdown("</div>", unsafe_allow_html=True)

# ---------------- 模拟 Corporate 员工数据（不含骑手/销售BD/客服） ----------------
np.random.seed(42)
CORP_SIZE = 25000
departments = ["研发工程","产品","运营","市场","财务","HR","法务与合规","战略与投资"]
biz_lines   = ["外卖","酒旅","出行"]
levels      = ["L3","L4","L5","L6","L7"]

dept_p  = np.array([0.38,0.13,0.16,0.07,0.08,0.07,0.05,0.06]); dept_p/=dept_p.sum()
level_p = np.array([0.22,0.35,0.28,0.12,0.03])

df = pd.DataFrame({
    "员工ID": np.arange(1, CORP_SIZE+1),
    "部门": np.random.choice(departments, CORP_SIZE, p=dept_p),
    "业务线": np.random.choice(biz_lines, CORP_SIZE),
    "职级": np.random.choice(levels, CORP_SIZE, p=level_p),
    "工龄(月)": (np.random.gamma(6, 6, CORP_SIZE).astype(int) + 3),
})

# —— 强化差异化 ——
# 任期差异（部门*职级）
dept_tenure_mult = {"研发工程":1.08,"产品":1.02,"运营":0.90,"市场":0.95,"财务":1.02,"HR":0.98,"法务与合规":1.15,"战略与投资":1.18}
level_tenure_mult = {"L3":0.90,"L4":1.00,"L5":1.10,"L6":1.22,"L7":1.35}
df["工龄(月)"] = (df["工龄(月)"] * df["部门"].map(dept_tenure_mult) * df["职级"].map(level_tenure_mult)).astype(int).clip(1)

# 绩效基线（28宫格区间抽样）+ 偏移（部门/级别/业务线）
bands  = np.array(["1档","2.1档","2.2档","2.3档","3档"]); band_p = np.array([0.05,0.35,0.25,0.15,0.20])
band = np.random.choice(bands, size=len(df), p=band_p)
ranges = {"1档":(0.0,0.5),"2.1档":(0.3,0.8),"2.2档":(0.8,1.1),"2.3档":(1.1,1.3),"3档":(1.2,1.8)}
low  = np.vectorize(lambda x: ranges[x][0])(band)
high = np.vectorize(lambda x: ranges[x][1])(band)
df["绩效系数"] = np.random.uniform(low, high)

dept_perf_shift  = {"研发工程":0.06,"产品":0.04,"运营":-0.06,"市场":-0.02,"财务":0.02,"HR":0.00,"法务与合规":0.10,"战略与投资":0.12}
level_perf_shift = {"L3":-0.05,"L4":-0.01,"L5":0.02,"L6":0.06,"L7":0.10}
bl_perf_shift    = {"外卖":-0.02,"到店":0.00,"酒旅":0.02,"出行":-0.01,"平台与基础设施":0.03}
df["绩效系数"] = (df["绩效系数"]
                 + df["部门"].map(dept_perf_shift).fillna(0)
                 + df["职级"].map(level_perf_shift).fillna(0)
                 + df["业务线"].map(bl_perf_shift).fillna(0)
                 + np.random.normal(0,0.03,len(df))).clip(0.0,1.9)

# 薪资（k RMB/月）：部门/职级基准 + 噪声
dept_base = {"研发工程":28,"产品":25,"运营":20,"市场":21,"财务":23,"HR":18,"法务与合规":26,"战略与投资":27}
level_mult = {"L3":0.85,"L4":1.0,"L5":1.25,"L6":1.7,"L7":2.3}
df["基础月薪(k)"] = df.apply(lambda r: dept_base[r["部门"]]*level_mult[r["职级"]]*np.random.normal(1.0,0.12), axis=1).clip(8,120)

# 离职概率（部门/级别/业务线偏置 + 任期&绩效影响）
dept_leave_bias  = {"研发工程":-0.015,"产品":-0.008,"运营":0.022,"市场":0.010,"财务":-0.006,"HR":0.006,"法务与合规":-0.020,"战略与投资":-0.022}
level_leave_bias = {"L3":0.012,"L4":0.004,"L5":-0.004,"L6":-0.012,"L7":-0.018}
bl_leave_bias    = {"外卖":0.006,"到店":0.002,"酒旅":0.000,"出行":0.004,"平台与基础设施":-0.004}
base = 0.08 + 0.04*(df["工龄(月)"]<12) + 0.03*(df["绩效系数"]<0.8)
bias = df["部门"].map(dept_leave_bias).fillna(0) + df["职级"].map(level_leave_bias).fillna(0) + df["业务线"].map(bl_leave_bias).fillna(0)
df["离职概率"] = np.clip(base + bias + np.random.normal(0,0.01,len(df)), 0.02, 0.40)

# 部门聚合（现有HC/批复编制/缺口）
dept_frame = (df.groupby("部门").size().rename("现有HC").to_frame()
              .assign(批复编制=lambda x: (x["现有HC"]*np.random.uniform(1.02,1.15,len(x))).round().astype(int))
              .reset_index())
pred_leaves = df.groupby("部门")["离职概率"].sum().rename("预测离职(期望人数)").reset_index()
dept_frame = dept_frame.merge(pred_leaves, on="部门", how="left")
dept_frame["预测在岗"] = (dept_frame["现有HC"] - dept_frame["预测离职(期望人数)"] + np.random.normal(0,20,len(dept_frame))).round().astype(int).clip(0)
dept_frame["预测缺口"] = (dept_frame["批复编制"] - dept_frame["预测在岗"]).astype(int)

# 招聘效率（明显差异）
recruit = pd.DataFrame({
    "部门": departments,
    "Offer接受率":[0.78,0.76,0.71,0.72,0.75,0.73,0.80,0.82],
    "招聘周期TTF(天)":[55,50,40,38,32,34,60,65]
})
dept_frame = dept_frame.merge(recruit, on="部门", how="left")

# ---------------- 顶部筛选 ----------------
with st.container():
    c1,c2,c3 = st.columns([2,2,2])
    dept_sel = c1.multiselect("筛选：部门", departments, default=departments)
    bl_sel   = c2.multiselect("筛选：业务线", biz_lines, default=biz_lines)
    lvl_sel  = c3.multiselect("筛选：职级", levels, default=levels)

df_f = df[(df["部门"].isin(dept_sel)) & (df["业务线"].isin(bl_sel)) & (df["职级"].isin(lvl_sel))].copy()
dept_frame_f = dept_frame[dept_frame["部门"].isin(dept_sel)].copy()

# ---------------- KPI 卡片（伪造但自洽的环比箭头） ----------------
st.markdown("### 全局概览")

def pseudo_delta(curr_value, sign="auto", pct_range=(0.8, 3.0)):
    """生成一个自洽的百分比变化字符串和delta_color"""
    pct = np.round(np.random.uniform(*pct_range), 1)  # 0.8% ~ 3.0%
    if sign == "up":
        s = f"+{pct}%"; color = "inverse"  # 上升视为坏（红），用于离职/缺口
    elif sign == "down":
        s = f"-{pct}%"; color = "normal"   # 下降视为好（绿）
    else:
        # 自动：正向 good→normal，负向 bad→inverse（这里不用）
        s = f"+{pct}%"; color = "normal"
    return s, color

# 当前值
k_headcount = len(df_f)
k_leaves    = int(df_f["离职概率"].sum())
k_gap       = int(dept_frame_f["预测缺口"].sum())

# 让三者方向自洽：离职↑ → 缺口↑ → 员工数↓
delta_leave_str, color_leave   = pseudo_delta(k_leaves, sign="up")
delta_gap_str,   color_gap     = pseudo_delta(k_gap,   sign="up")
delta_hc_str,    color_hc      = pseudo_delta(k_headcount, sign="down")

k1,k2,k3,k4,k5 = st.columns(5)
with k1: st.metric("现有员工（Corporate）", f"{k_headcount:,}", delta=delta_hc_str, delta_color=color_hc)
with k2: st.metric("平均任期（月）", f"{df_f['工龄(月)'].mean():.1f}", delta="-0.6%", delta_color="normal")  # 扩招导致平均任期略降（示例）
with k3: st.metric("预测离职期望（近一月，人数）", k_leaves, delta=delta_leave_str, delta_color=color_leave)
with k4: st.metric("预测缺口（下月，人数）", f"{k_gap:,}", delta=delta_gap_str, delta_color=color_gap)
with k5: st.metric("Offer 接受率（中位）", f"{dept_frame_f['Offer接受率'].median():.0%}", delta="+0.4%", delta_color="normal")

# ---------------- 工具函数：部门水平条形 ----------------
def dept_bar(df_long: pd.DataFrame, value_col: str, title: str, x_title: str,
             x_ticks=None, color="#2F5597"):
    d = (df_long.groupby("部门")[value_col].mean()).reindex(dept_sel).dropna()
    fig = px.bar(d.reset_index(), x=value_col, y="部门", orientation="h",
                 title=title, labels={value_col:x_title, "部门":""},
                 color_discrete_sequence=[color])
    if x_ticks is not None:
        fig.update_xaxes(tickmode="array", tickvals=list(x_ticks))
    fig.update_layout(template="plotly_white", xaxis_title=x_title, yaxis_title="")
    return fig

# ---------------- 现有人员详情 ----------------
st.divider()
st.markdown("### 现有人员详情")
df_f["_Top绩效"] = (df_f["绩效系数"] >= 1.1)

c11, c12, c13, c14 = st.columns(4)
with c11:
    st.plotly_chart(
        dept_bar(df_f, "工龄(月)",
                 "工龄详情（平均） — 按部门", "工龄（月）",
                 x_ticks=(6,12,18,24,30), color="#6C8CD5"),
        use_container_width=True
    )
with c12:
    st.plotly_chart(
        dept_bar(df_f, "绩效系数",
                 "绩效详情（平均系数） — 按部门", "绩效系数",
                 x_ticks=(0.5,0.8,1.0,1.2,1.5,1.8), color="#2E8B57"),
        use_container_width=True
    )
with c13:
    st.plotly_chart(
        dept_bar(df_f, "基础月薪(k)",
                 "薪资详情（平均） — 按部门", "基础月薪（k RMB）",
                 color="#F39C12"),
        use_container_width=True
    )
with c14:
    leaves_by_dept = df_f.groupby("部门")["离职概率"].sum().rename("期望离职人数").reset_index()
    fig = px.bar(leaves_by_dept.reindex(leaves_by_dept.index), x="期望离职人数", y="部门",
                 orientation="h", title="预测离职（期望人数） — 按部门",
                 labels={"期望离职人数":"期望人数（近一月）","部门":""},
                 color_discrete_sequence=["#E74C3C"])
    fig.update_layout(template="plotly_white", xaxis_title="期望人数（近一月）", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 招聘数据详情 ----------------
st.divider()
st.markdown("### 招聘数据详情")
# 缺口百分比
dept_frame_f["预测缺口正数"] = dept_frame_f["预测缺口"].clip(lower=0)
dept_frame_f["预测缺口百分比"] = (
    dept_frame_f["预测缺口正数"] / (dept_frame_f["现有HC"] + dept_frame_f["预测缺口正数"]).replace(0,np.nan)
).fillna(0.0)

r1, r2, r3, r4 = st.columns(4)
with r1:
    st.plotly_chart(
        dept_bar(dept_frame_f, "现有HC",
                 "现有 HC — 按部门", "人数", color="#2F5597"),
        use_container_width=True
    )
with r2:
    st.plotly_chart(
        dept_bar(dept_frame_f, "预测缺口",
                 "预测缺口（下月）= 批复编制 − 预测在岗", "缺口（>0需增员）", color="#8E44AD"),
        use_container_width=True
    )
with r3:
    st.plotly_chart(
        dept_bar(dept_frame_f, "招聘周期TTF(天)",
                 "招聘周期（TTF，中位天数）— 按部门", "天数", color="#34495E"),
        use_container_width=True
    )
with r4:
    st.plotly_chart(
        dept_bar(dept_frame_f, "Offer接受率",
                 "Offer 接受率 — 按部门", "接受率",
                 x_ticks=(0.6,0.7,0.8,0.9), color="#16A085"),
        use_container_width=True
    )

# ---------------- 风险与亮点（占比口径） ----------------
st.divider()
st.markdown("### 风险与亮点（占比口径）")

# 缺口百分比（确保已计算）
dept_frame_f["预测缺口正数"] = dept_frame_f["预测缺口"].clip(lower=0)
dept_frame_f["预测缺口百分比"] = (
    dept_frame_f["预测缺口正数"] /
    (dept_frame_f["现有HC"] + dept_frame_f["预测缺口正数"]).replace(0, np.nan)
).fillna(0.0)

dept_health = (
    df_f.groupby("部门")
       .agg(
           在岗人数=("员工ID","count"),
           平均任期月=("工龄(月)","mean"),
           平均月薪k=("基础月薪(k)","mean"),
           Top绩效占比=("_Top绩效","mean"),
           预测离职期望占比=("离职概率","mean")
       )
       .merge(
           dept_frame_f[["部门","预测缺口百分比","Offer接受率","招聘周期TTF(天)"]],
           on="部门", how="left"
       )
       .reset_index()
)

# 阈值
TH_LEAVE_RATE_HIGH = 0.15; TH_LEAVE_RATE_GOOD = 0.08
TH_GAP_RATE_HIGH   = 0.10; TH_GAP_RATE_GOOD   = 0.03
TH_TTF_HIGH        = 50;   TH_TTF_GOOD        = 40
TH_OFFER_LOW       = 0.70; TH_OFFER_HIGH     = 0.78
TH_TOP_PERF_GOOD   = 0.32

# —— 风险预警数据集 ——
risk_df = dept_health[
    (dept_health["预测离职期望占比"] >= TH_LEAVE_RATE_HIGH) |
    (dept_health["预测缺口百分比"]   >= TH_GAP_RATE_HIGH)   |
    (dept_health["招聘周期TTF(天)"]   >= TH_TTF_HIGH)        |
    (dept_health["Offer接受率"]      <= TH_OFFER_LOW)
].copy()
if risk_df.empty:
    tmp = dept_health.assign(
        风险分=lambda x: x["预测离职期望占比"]*0.5 +
                        x["预测缺口百分比"]*0.3 +
                        (x["招聘周期TTF(天)"]/100)*0.15 -
                        x["Offer接受率"]*0.05
    )
    risk_df = tmp.sort_values("风险分", ascending=False).head(5).drop(columns=["风险分"])

# —— 亮点数据集 ——
good_df = dept_health[
    (dept_health["Top绩效占比"]      >= TH_TOP_PERF_GOOD) &
    (dept_health["Offer接受率"]      >= TH_OFFER_HIGH)    &
    (dept_health["招聘周期TTF(天)"]   <= TH_TTF_GOOD)      &
    (dept_health["预测离职期望占比"]  <= TH_LEAVE_RATE_GOOD) &
    (dept_health["预测缺口百分比"]    <= TH_GAP_RATE_GOOD)
].copy()
if good_df.empty:
    tmp = dept_health.assign(
        亮点分=lambda x: x["Top绩效占比"]*0.45 + x["Offer接受率"]*0.25 -
                        x["预测离职期望占比"]*0.20 -
                        (x["招聘周期TTF(天)"]/100)*0.05 -
                        x["预测缺口百分比"]*0.05
    )
    good_df = tmp.sort_values("亮点分", ascending=False).head(5).drop(columns=["亮点分"])

# —— 条件格式函数 ——
def style_risk(val, col):
    if col == "预测离职期望占比" and val >= TH_LEAVE_RATE_HIGH: return "background-color:#fde2e2;color:#c0392b;font-weight:600"
    if col == "预测缺口百分比"   and val >= TH_GAP_RATE_HIGH:   return "background-color:#fff4e6;color:#d35400;font-weight:600"
    if col == "招聘周期TTF(天)"   and val >= TH_TTF_HIGH:        return "background-color:#fff4e6;color:#d35400;font-weight:600"
    if col == "Offer接受率"      and val <= TH_OFFER_LOW:       return "background-color:#fff4e6;color:#d35400;font-weight:600"
    return ""

def style_good(val, col):
    if col == "Top绩效占比"      and val >= TH_TOP_PERF_GOOD:   return "background-color:#eaf7ed;color:#1e8449;font-weight:600"
    if col == "Offer接受率"      and val >= TH_OFFER_HIGH:      return "background-color:#eaf7ed;color:#1e8449;font-weight:600"
    if col == "招聘周期TTF(天)"   and val <= TH_TTF_GOOD:        return "background-color:#eaf7ed;color:#1e8449;font-weight:600"
    if col == "预测离职期望占比"  and val <= TH_LEAVE_RATE_GOOD: return "background-color:#eaf7ed;color:#1e8449;font-weight:600"
    if col == "预测缺口百分比"    and val <= TH_GAP_RATE_GOOD:   return "background-color:#eaf7ed;color:#1e8449;font-weight:600"
    return ""

show_cols = ["部门","在岗人数","平均任期月","平均月薪k","Top绩效占比",
             "预测离职期望占比","预测缺口百分比","Offer接受率","招聘周期TTF(天)"]

# —— 风险预警（带高亮） ——
st.subheader("⚠️ 风险预警（占比）")
st.dataframe(
    risk_df[show_cols].style
        .applymap(lambda v: style_risk(v, "预测离职期望占比"), subset=["预测离职期望占比"])
        .applymap(lambda v: style_risk(v, "预测缺口百分比"),   subset=["预测缺口百分比"])
        .applymap(lambda v: style_risk(v, "Offer接受率"),      subset=["Offer接受率"])
        .applymap(lambda v: style_risk(v, "招聘周期TTF(天)"),   subset=["招聘周期TTF(天)"])
        .format({
            "平均任期月":"{:.1f}",
            "平均月薪k":"{:.1f}",
            "Top绩效占比":"{:.0%}",
            "预测离职期望占比":"{:.0%}",
            "预测缺口百分比":"{:.0%}",
            "Offer接受率":"{:.0%}"
        }),
    use_container_width=True, hide_index=True
)

# —— 突出亮点（带高亮） ——
st.subheader("🌟 突出亮点（占比）")
st.dataframe(
    good_df[show_cols].style
        .applymap(lambda v: style_good(v, "Top绩效占比"), subset=["Top绩效占比"])
        .applymap(lambda v: style_good(v, "Offer接受率"), subset=["Offer接受率"])
        .applymap(lambda v: style_good(v, "招聘周期TTF(天)"), subset=["招聘周期TTF(天)"])
        .applymap(lambda v: style_good(v, "预测离职期望占比"), subset=["预测离职期望占比"])
        .applymap(lambda v: style_good(v, "预测缺口百分比"), subset=["预测缺口百分比"])
        .format({
            "平均任期月":"{:.1f}",
            "平均月薪k":"{:.1f}",
            "Top绩效占比":"{:.0%}",
            "预测离职期望占比":"{:.0%}",
            "预测缺口百分比":"{:.0%}",
            "Offer接受率":"{:.0%}"
        }),
    use_container_width=True, hide_index=True
)

# st.caption("口径：预测离职期望占比=平均离职概率；预测缺口百分比=max(缺口,0)/(现有HC+max(缺口,0))。")

# ---------------- 预测方法说明（可视化 & 外部因素纳入） ----------------
st.divider()
st.markdown("### 预测方法说明（通俗版）")

import plotly.graph_objects as go

# ===== 1) Sankey：左=预测离职 → 右=预测缺口（加入外部环境） =====
st.markdown("#### 1) 从“预测离职”如何传导到“预测缺口”？（含外部环境）")

## ====== 可视化：分别解释“如何预测离职 / 如何预测缺口” ======
import plotly.graph_objects as go

# —— 1) 如何预测离职 —— #
def sankey_attrition():
    # 节点（左→右）
    labels = [
        "工龄/职级/岗位",      # 0 员工属性
        "绩效系数",           # 1 绩效
        "团队稳定性/经理变更", # 2 内部管理
        "薪酬竞争力（分位）", # 3 外部薪酬
        "竞争对手/猎头活动",   # 4 外部竞对
        "宏观经济环境",       # 5 外部宏观
        "预测离职概率"        # 6 目标
    ]
    # 链接：各因素 → 预测离职概率
    sources = [0,1,2,3,4,5]
    targets = [6,6,6,6,6,6]
    values  = [7,6,5,4,4,3]  # 只是可视化宽度，越大越粗
    link_colors = [
        "rgba(92,130,163,0.80)", "rgba(92,130,163,0.70)", "rgba(92,130,163,0.60)",
        "rgba(92,130,163,0.50)", "rgba(92,130,163,0.45)", "rgba(92,130,163,0.40)"
    ]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18, thickness=22,
            line=dict(color="#888", width=0.8),
            label=labels,
            color=["#DCE6EE","#DCE6EE","#DCE6EE","#DCE6EE","#DCE6EE","#DCE6EE","#AEC0CF"]  # 节点淡配色
        ),
        link=dict(source=sources, target=targets, value=values, color=link_colors)
    )])

    fig.update_layout(
        title="如何预测离职（人级别）",
        font=dict(size=16, color="black", family="Segoe UI, Verdana, Microsoft YaHei, Arial"),
        paper_bgcolor="white", plot_bgcolor="white",
        height=380, margin=dict(l=10,r=10,t=35,b=10)
    )
    return fig

# —— 2) 如何预测缺口 —— #
def sankey_gap():
    labels = [
        "预测离职结果（人数）",  # 0 来自上一个模型
        "业务增长（新增需求）",  # 1
        "招聘难度（TTF/Offer）",# 2
        "竞争对手/人才争夺",    # 3
        "宏观经济/政策/地区供需",# 4
        "批复编制",            # 5 编制上限
        "预测缺口人数"          # 6 目标
    ]
    # 因素 → 预测缺口
    sources = [0,1,2,3,4,5]
    targets = [6,6,6,6,6,6]
    values  = [7,8,6,5,4,7]   # 可视化宽度
    link_colors = [
        "rgba(92,130,163,0.80)","rgba(92,130,163,0.75)","rgba(92,130,163,0.60)",
        "rgba(92,130,163,0.50)","rgba(92,130,163,0.45)","rgba(92,130,163,0.80)"
    ]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18, thickness=22,
            line=dict(color="#888", width=0.8),
            label=labels,
            color=["#DCE6EE","#DCE6EE","#DCE6EE","#DCE6EE","#DCE6EE","#DCE6EE","#AEC0CF"]
        ),
        link=dict(source=sources, target=targets, value=values, color=link_colors)
    )])

    fig.update_layout(
        title="如何预测缺口（部门级）",
        font=dict(size=16, color="black", family="Segoe UI, Verdana, Microsoft YaHei, Arial"),
        paper_bgcolor="white", plot_bgcolor="white",
        height=380, margin=dict(l=10,r=10,t=35,b=10)
    )
    return fig

# —— 渲染 —— #
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(sankey_attrition(), use_container_width=True)
with c2:
    st.plotly_chart(sankey_gap(), use_container_width=True)

st.caption(
    "离职预测：基于工龄/职级/岗位、绩效系数、团队稳定性、薪酬竞争力、竞对与宏观环境等特征，输出员工级“离职概率”，部门聚合得到预计离职人数；"
    "缺口预测：综合预计离职人数、业务增长、招聘难度、竞对、宏观/政策/地区供需，以及“批复编制”，输出部门级“预测缺口人数”。"
)

# ===== 2) Feature Importance：将外部因素也纳入 =====
st.markdown("#### 2) 模型怎么看重什么？（特征重要性，含外部因素）")

# 伪造但自洽的权重，之后按需要微调；自动归一化成 1.0
feat_imp = pd.DataFrame({
    "特征": [
        "绩效系数", "工龄<12月", "职级（L3-L4）",
        "薪酬竞争力分位", "TTF（招聘周期）", "Offer接受率",
        "团队稳定性（经理变更）",
        "业务增长指数", "竞争对手招聘强度", "宏观经济指数",
        "地区供需紧张度", "用工政策/监管"
    ],
    "重要性_raw": [0.16, 0.14, 0.09, 0.11, 0.08, 0.06, 0.07, 0.12, 0.09, 0.06, 0.05, 0.07]
})
feat_imp["重要性"] = feat_imp["重要性_raw"] / feat_imp["重要性_raw"].sum()
feat_imp = feat_imp[["特征","重要性"]].sort_values("重要性", ascending=True)

fig_imp = px.bar(
    feat_imp, x="重要性", y="特征", orientation="h",
    labels={"重要性":"重要性（归一化）","特征":""},
    title="离职 / 缺口 关键驱动因素（含外部环境）",
    color_discrete_sequence=["#2E86C1"]
)
fig_imp.update_layout(template="plotly_white", xaxis_tickformat=".0%", height=460)
st.plotly_chart(fig_imp, use_container_width=True)

# ===== 3) 校准图（预测 vs 实际）——给出可信度 =====
st.markdown("#### 3) 预测靠不靠谱？（校准图）")
# 用当前 df_f 的离职概率进行伯努利抽样，模拟“实际离职”结果（仅演示）
probs = df_f["离职概率"].clip(0.02, 0.40).values
actual = np.random.binomial(1, probs, size=len(probs))
bins = pd.cut(probs, bins=[0.0,0.1,0.2,0.3,0.4], include_lowest=True)
calib = pd.DataFrame({"bin": bins, "pred": probs, "y": actual}).groupby("bin").agg(
    预测均值=("pred","mean"),
    实际离职率=("y","mean"),
    n=("y","size")
).reset_index()

fig_cal = go.Figure()
fig_cal.add_trace(go.Scatter(x=calib["预测均值"], y=calib["实际离职率"],
                             mode="markers+lines", name="实际", marker=dict(size=8)))
fig_cal.add_trace(go.Scatter(x=[0,0.45], y=[0,0.45], mode="lines", name="完美校准", line=dict(dash="dash")))
fig_cal.update_layout(template="plotly_white",
                      xaxis_title="预测离职概率（分箱均值）", yaxis_title="实际离职率",
                      height=320)
st.plotly_chart(fig_cal, use_container_width=True)
st.caption("点越靠近虚线越好。真实落地时，用近 3–6 个月滚动窗口做持续校准。")

# ===== 4) 口径 & 模型说明 =====
st.markdown("#### 4) 我们具体怎么算？用的什么模型？")
st.latex(r"""
\begin{aligned}
\text{预计离职人数（期望）} &= \sum_i p_i \\
\text{预测在岗}_{t+1} &= \text{现有HC}_t - \sum_i p_i \;+\; \text{Offer}_t \times \text{接受率} \times \text{到岗率} \\
\text{预测缺口}_{t+1} &= \text{批复编制}_{t+1} - \text{预测在岗}_{t+1} \\
\text{缺口\%} &= \dfrac{\max(\text{缺口},0)}{\text{现有HC}+\max(\text{缺口},0)}
\end{aligned}
""")

with st.expander("模型选择 & 原因（click 展开）", expanded=False):
    st.markdown("""
- **离职概率模型（人级别）**：`RandomForestClassifier`  
  - 优点：能抓非线性与交互，特征重要性直观，可解释性比神经网络强。  
  - 主要特征：绩效系数、工龄、职级、薪酬分位、团队稳定性、**竞争对手招聘强度**、**宏观经济指数**、TTF、Offer 接受率、**地区供需紧张度**、**用工政策** 等。
- **在岗 & 缺口（部门级）**：用回归/规则组合（如 `LightGBMRegressor` 或 `GradientBoostingRegressor`）对 **预测在岗** 做估计，结合 **批复编制** 得到缺口。  
  - 将 **业务增长指数** 作为外生变量直接进入模型（对缺口影响显著）。  
- **校准**：分箱 + 等频或 isotonic/Platt 校准，保证概率不是“瞎报”。  
- **不确定性**：对离职人数用 Poisson-Binomial 近似或蒙特卡洛抽样给出 95% 区间。
""")

# ---------------- 明细下载 ----------------
st.divider()
st.markdown("### 数据明细")
st.download_button("下载员工明细（CSV）", df_f.to_csv(index=False).encode("utf-8"), file_name="employees_corporate.csv")
st.download_button("下载部门招聘与预测（CSV）", dept_frame_f.to_csv(index=False).encode("utf-8"), file_name="dept_hiring_forecast.csv")

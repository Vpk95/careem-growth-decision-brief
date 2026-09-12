import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Careem Growth Decision Intelligence", page_icon="🚀", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem;}
.hero {padding: 1.2rem 1.4rem; border-radius: 16px; background: linear-gradient(135deg,#f7f7f7,#ffffff); border:1px solid #e7e7e7; margin-bottom:1rem;}
.badge {display:inline-block; padding:.25rem .65rem; border-radius:999px; background:#111; color:#fff; font-size:.78rem; margin-bottom:.5rem;}
.insight {padding:1rem; border:1px solid #e5e5e5; border-radius:14px; margin:.5rem 0; background:#fff;}
.action {padding:1rem; border-radius:14px; border:1px solid #dcdcdc; background:#fafafa;}
.small {color:#666;font-size:.86rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<span class="badge">GROWTH DECISION INTELLIGENCE</span>
<h1>From performance data → business decision</h1>
<p>Careem Food growth prototype: diagnose performance, surface the highest-value signal, recommend an experiment, and define how success will be measured.</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_default():
    return pd.read_csv("synthetic_growth_data.csv")
@st.cache_data
def load_segments():
    return pd.read_csv("synthetic_customer_segments.csv")

uploaded = st.sidebar.file_uploader("Upload your own CSV", type=["csv"])
data = pd.read_csv(uploaded) if uploaded else load_default()
segments = load_segments()

data["month"] = pd.to_datetime(data["month"])
data = data.sort_values(["month","city"])

st.sidebar.header("Decision guardrails")
target_growth = st.sidebar.slider("Revenue MoM target (%)", 0.0, 10.0, 5.0, 0.5)
max_cac = st.sidebar.slider("Max CAC (AED)", 5.0, 30.0, 18.0, 0.5)
min_promo_roi = st.sidebar.slider("Minimum promo ROI (x)", 3.0, 15.0, 8.0, 0.5)

latest_month = data["month"].max()
prev_month = data["month"].sort_values().unique()[-2]
latest = data[data["month"]==latest_month]
prev = data[data["month"]==prev_month]

def growth(cur, old):
    return (cur/old-1)*100 if old else 0

metrics = {
    "Revenue": (latest.revenue_aed.sum(), prev.revenue_aed.sum()),
    "MAU": (latest.mau.sum(), prev.mau.sum()),
    "OPU": (latest.opu.sum(), prev.opu.sum()),
    "ARPU": (latest.revenue_aed.sum()/latest.opu.sum(), prev.revenue_aed.sum()/prev.opu.sum())
}
rev_growth = growth(*metrics["Revenue"])
mau_growth = growth(*metrics["MAU"])
opu_growth = growth(*metrics["OPU"])
arpu_growth = growth(*metrics["ARPU"])
weighted_cac = np.average(latest.cac_aed, weights=latest.mau)
weighted_churn = np.average(latest.churn_pct, weights=latest.mau)
weighted_roi = np.average(latest.promo_roi, weights=latest.mau)

# Transparent prioritisation engine
signals = []
if rev_growth < target_growth:
    signals.append({
        "priority": "P0", "title":"Revenue is below plan",
        "evidence":f"Revenue grew {rev_growth:.1f}% MoM versus a {target_growth:.1f}% guardrail.",
        "action":"Diagnose the conversion → orders → basket-value chain before increasing acquisition spend.",
        "metric":"Incremental revenue / contribution margin"
    })
if weighted_cac > max_cac:
    signals.append({
        "priority":"P0","title":"Acquisition efficiency needs attention",
        "evidence":f"Weighted CAC is AED {weighted_cac:.1f}, above the AED {max_cac:.1f} guardrail.",
        "action":"Reallocate spend toward high-intent/high-LTV cohorts and cap low-efficiency channels.",
        "metric":"Incremental orders and CAC"
    })
if weighted_churn > 17:
    signals.append({
        "priority":"P1","title":"Retention is a growth lever",
        "evidence":f"Weighted churn is {weighted_churn:.1f}%; retention improvement can compound growth without proportional acquisition cost.",
        "action":"Run a lapsed-user win-back experiment with a holdout group.",
        "metric":"30-day reactivation + incremental orders"
    })
if weighted_roi >= min_promo_roi:
    signals.append({
        "priority":"P1","title":"Promotions show scalable potential",
        "evidence":f"Weighted promotion ROI is {weighted_roi:.1f}x, above the {min_promo_roi:.1f}x floor.",
        "action":"Scale only the highest incremental-ROI offers and protect contribution margin.",
        "metric":"Incremental contribution / promo cost"
    })
if not signals:
    signals.append({
        "priority":"P1","title":"Core growth metrics are healthy",
        "evidence":"No configured guardrail is currently breached.",
        "action":"Use controlled experiments to identify the next growth constraint.",
        "metric":"Incremental revenue"
    })

# Executive KPI row
st.subheader("Executive snapshot")
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Revenue",f"AED {metrics['Revenue'][0]/1e6:.2f}M",f"{rev_growth:+.1f}%")
c2.metric("MAU",f"{metrics['MAU'][0]/1000:.0f}K",f"{mau_growth:+.1f}%")
c3.metric("OPU",f"{metrics['OPU'][0]/1000:.1f}K",f"{opu_growth:+.1f}%")
c4.metric("ARPU",f"AED {metrics['ARPU'][0]:.1f}",f"{arpu_growth:+.1f}%")
c5.metric("CAC",f"AED {weighted_cac:.1f}", "guardrail "+("OK" if weighted_cac<=max_cac else "BREACH"))

tab1,tab2,tab3,tab4 = st.tabs(["Decision Brief","Funnel & Trends","Segments & Cohorts","Experiment Lab"])

with tab1:
    st.subheader("AI-style decision brief")
    st.caption("The reasoning layer is deliberately auditable: every recommendation is tied to a measurable signal.")
    for s in sorted(signals,key=lambda x: x["priority"]):
        st.markdown(f"""<div class="insight">
        <b>{s['priority']} · {s['title']}</b><br>
        <span class="small">Evidence:</span> {s['evidence']}<br>
        <span class="small">Recommended action:</span> <b>{s['action']}</b><br>
        <span class="small">Success metric:</span> {s['metric']}
        </div>""", unsafe_allow_html=True)

    top = sorted(signals,key=lambda x: x["priority"])[0]
    st.markdown("### 🎯 Recommended next move")
    st.markdown(f"""<div class="action"><b>{top['action']}</b><br><br>
    <span class="small">Primary KPI:</span> {top['metric']}<br>
    <span class="small">Decision cadence:</span> 2-week test → weekly readout → scale/stop decision
    </div>""", unsafe_allow_html=True)

with tab2:
    st.subheader("Growth trend")
    trend = data.groupby("month")[["revenue_aed","mau","opu"]].sum()
    st.line_chart(trend)
    st.subheader("City performance")
    city = latest.groupby("city").agg(revenue_aed=("revenue_aed","sum"),mau=("mau","sum"),cac_aed=("cac_aed","mean"),churn_pct=("churn_pct","mean"))
    city["revenue_per_mau"] = city.revenue_aed/city.mau
    st.dataframe(city.style.format({"revenue_aed":"AED {:,.0f}","mau":"{:,.0f}","cac_aed":"AED {:.1f}","churn_pct":"{:.1f}%","revenue_per_mau":"AED {:.2f}"}),use_container_width=True)

with tab3:
    st.subheader("Customer lifecycle")
    latest_seg = segments[segments.month==segments.month.max()].copy()
    st.dataframe(latest_seg.style.format({"users":"{:,.0f}","orders_per_user":"{:.1f}","retention_30d_pct":"{:.1f}%"}),use_container_width=True)
    st.bar_chart(latest_seg.set_index("segment")[["retention_30d_pct"]])
    st.markdown("**Interpretation:** prioritise high-LTV retention and lapsed-user reactivation before indiscriminately scaling acquisition.")

with tab4:
    st.subheader("Experiment recommendation")
    exp = st.selectbox("Choose a growth lever",["Lapsed-user win-back","Basket-building bundle","Acquisition reallocation","Promotion optimisation"])
    experiments = {
        "Lapsed-user win-back":("Target users inactive 30–60 days with personalised offers.","Holdout vs treatment; incremental reactivation and contribution margin.","30-day reactivation rate"),
        "Basket-building bundle":("Offer complementary-item bundles to medium-frequency users.","A/B test bundle exposure vs control.","Incremental basket value + contribution"),
        "Acquisition reallocation":("Move budget from high-CAC cohorts to high-intent/high-LTV cohorts.","Geo/channel holdout where feasible; compare incremental orders.","CAC + incremental orders"),
        "Promotion optimisation":("Scale offers with proven incremental ROI and reduce blanket discounting.","Offer-level experiment with margin guardrail.","Incremental contribution / promo cost")
    }
    hypothesis, design, kpi = experiments[exp]
    st.markdown(f"""<div class="action">
    <b>Hypothesis:</b> {hypothesis}<br><br>
    <b>Test design:</b> {design}<br><br>
    <b>Primary KPI:</b> {kpi}
    </div>""",unsafe_allow_html=True)

st.divider()
st.subheader("Method")
st.write("Input → KPI normalisation → guardrail checks → prioritised signals → recommended action → experiment design → measurable success criterion.")
st.caption("All data in this demo is synthetic. No confidential Careem data is used.")

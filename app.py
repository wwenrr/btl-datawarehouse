"""Streamlit dashboard cho Instacart star schema warehouse."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards


def section(title: str, description: str | None = None) -> None:
    st.header(title, divider="green", anchor=False)
    if description:
        st.caption(description)

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "warehouse" / "instacart.duckdb"
DM_DIR = ROOT / "outputs" / "data_mining"

DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PLOTLY_TEMPLATE = "plotly_dark"
SEQUENTIAL = "Tealgrn"
DIVERGING = "RdBu"
CATEGORICAL = px.colors.qualitative.Set2

PLOT_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
}

st.set_page_config(
    page_title="Instacart DW Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main .block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1400px; }
        h1, h2, h3 { letter-spacing: -0.015em; }
        section[data-testid="stSidebar"] { background: rgba(255, 255, 255, 0.02); }
        div[data-testid="stHorizontalBlock"] { gap: 0.6rem; }
        button[data-baseweb="tab"] {
            font-weight: 600; font-size: 0.95rem; padding-top: 0.6rem; padding-bottom: 0.6rem;
        }
        div[data-testid="stTabs"] div[data-baseweb="tab-list"] { gap: 0.4rem; }
        .hero {
            background: linear-gradient(135deg, rgba(38,208,168,0.18) 0%, rgba(56,178,172,0.06) 50%, rgba(99,102,241,0.10) 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 22px 28px;
            margin-bottom: 18px;
        }
        .hero h1 { margin: 0 0 4px 0; font-size: 1.65rem; font-weight: 700; }
        .hero p { margin: 0; opacity: 0.78; font-size: 0.95rem; }
        .badge {
            display: inline-block; padding: 3px 10px; border-radius: 999px;
            font-size: 0.75rem; font-weight: 600; margin-right: 6px;
            background: rgba(38,208,168,0.15); color: #26d0a8; border: 1px solid rgba(38,208,168,0.35);
        }
        .badge-muted { background: rgba(255,255,255,0.06); color: #c9d1d9; border-color: rgba(255,255,255,0.12); }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_hero(stats: dict[str, int], last_run: str | None) -> None:
    badges = (
        '<span class="badge">DuckDB</span>'
        '<span class="badge">Star schema</span>'
        '<span class="badge">Plotly</span>'
        f'<span class="badge badge-muted">Cập nhật: {last_run or "—"}</span>'
    )
    summary = (
        f"{stats['orders']:,} đơn · {stats['lines']:,} dòng fact · "
        f"{stats['customers']:,} khách · {stats['products']:,} sản phẩm · "
        f"{stats['departments']} departments"
    )
    st.markdown(
        f"""
        <div class="hero">
            <h1>Instacart Data Warehouse</h1>
            <p>{summary}</p>
            <div style="margin-top: 12px;">{badges}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_conn() -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        st.error(
            f"Không tìm thấy warehouse `{DB_PATH}`. Hãy chạy `python etl.py --stage all` trước."
        )
        st.stop()
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(show_spinner=False)
def query_df(sql: str, params: tuple | None = None) -> pd.DataFrame:
    conn = get_conn()
    if params:
        return conn.execute(sql, params).df()
    return conn.execute(sql).df()


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    path = DM_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def fmt_int(value) -> str:
    if pd.isna(value):
        return "0"
    return f"{int(value):,}"


def style_fig(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12),
        title=dict(font=dict(size=15, color="#e6e6e6"), x=0.0, xanchor="left"),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        hoverlabel=dict(font_size=12),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    return fig


def show_fig(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)


def _safe_slider(container, label: str, series: pd.Series, step: float, fmt: str | None = None) -> float:
    series = series.replace([float("inf"), float("-inf")], pd.NA).dropna()
    if series.empty:
        container.caption(f"{label}: không có dữ liệu")
        return float("-inf")
    lo = float(series.min())
    hi = float(series.max())
    if lo == hi:
        container.caption(f"{label}: chỉ 1 giá trị ({lo:.4f})")
        return lo
    return container.slider(label, lo, hi, lo, step=step, format=fmt) if fmt else container.slider(
        label, lo, hi, lo, step=step
    )


def build_filter_clause(branches: list[str], dows: list[str], departments: list[str]) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []
    if branches:
        clauses.append(f"b.branch_name in ({','.join(['?'] * len(branches))})")
        params.extend(branches)
    if dows:
        clauses.append(f"d.day_of_week in ({','.join(['?'] * len(dows))})")
        params.extend(dows)
    if departments:
        clauses.append(f"p.department_name in ({','.join(['?'] * len(departments))})")
        params.extend(departments)
    where = (" where " + " and ".join(clauses)) if clauses else ""
    return where, params


def render_overview(branches: list[str], dows: list[str], departments: list[str]) -> None:
    where, params = build_filter_clause(branches, dows, departments)

    kpi_sql = f"""
        select
            count(distinct f.order_id_nk) as orders,
            count(*) as order_lines,
            count(distinct f.product_key) as products,
            count(distinct f.customer_key) as customers,
            avg(case when f.reordered then 1.0 else 0.0 end) as reorder_rate,
            sum(f.quantity) as total_items
        from fact_order_line f
        join dim_product p on f.product_key = p.product_key
        join dim_branch b on f.branch_key = b.branch_key
        join dim_date d on f.date_key = d.date_key
        {where}
    """
    kpi = query_df(kpi_sql, tuple(params)).iloc[0]

    cols = st.columns(5)
    cols[0].metric("Số đơn", fmt_int(kpi["orders"]))
    cols[1].metric("Số dòng đơn", fmt_int(kpi["order_lines"]))
    cols[2].metric("Tổng items", fmt_int(kpi["total_items"]))
    cols[3].metric("Khách hàng", fmt_int(kpi["customers"]))
    rate = kpi["reorder_rate"] or 0
    cols[4].metric("Reorder rate", f"{rate * 100:.1f}%")
    style_metric_cards(
        background_color="rgba(255,255,255,0.03)",
        border_left_color="#26d0a8",
        border_color="rgba(255,255,255,0.08)",
        box_shadow=False,
    )
    section("Phân bổ theo thời gian & department")

    col_dow, col_dept = st.columns(2)
    with col_dow:
        dow_sql = f"""
            select d.day_of_week, count(distinct f.order_id_nk) as orders
            from fact_order_line f
            join dim_product p on f.product_key = p.product_key
            join dim_branch b on f.branch_key = b.branch_key
            join dim_date d on f.date_key = d.date_key
            {where}
            group by d.day_of_week
        """
        dow_df = query_df(dow_sql, tuple(params))
        if not dow_df.empty:
            dow_df = dow_df.set_index("day_of_week").reindex(DOW_ORDER).fillna(0).reset_index()
            fig = px.bar(
                dow_df,
                x="day_of_week",
                y="orders",
                color="orders",
                color_continuous_scale=SEQUENTIAL,
                title="Đơn theo ngày trong tuần",
            )
            fig.update_traces(hovertemplate="<b>%{x}</b><br>Đơn: %{y:,}<extra></extra>")
            fig.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title="Đơn")
            show_fig(style_fig(fig))
        else:
            st.info("Không có dữ liệu phù hợp filter.")

    with col_dept:
        dept_sql = f"""
            select p.department_name, count(*) as lines
            from fact_order_line f
            join dim_product p on f.product_key = p.product_key
            join dim_branch b on f.branch_key = b.branch_key
            join dim_date d on f.date_key = d.date_key
            {where}
            group by p.department_name
            order by lines desc
            limit 10
        """
        dept_df = query_df(dept_sql, tuple(params))
        if not dept_df.empty:
            dept_df = dept_df.sort_values("lines")
            fig = px.bar(
                dept_df,
                x="lines",
                y="department_name",
                orientation="h",
                color="lines",
                color_continuous_scale=SEQUENTIAL,
                title="Top 10 departments theo số dòng",
            )
            fig.update_traces(hovertemplate="<b>%{y}</b><br>Dòng: %{x:,}<extra></extra>")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Dòng", yaxis_title=None)
            show_fig(style_fig(fig))
        else:
            st.info("Không có dữ liệu.")
    section("Xu hướng theo ngày")

    daily_sql = f"""
        select d.full_date, sum(f.quantity) as items, count(distinct f.order_id_nk) as orders
        from fact_order_line f
        join dim_product p on f.product_key = p.product_key
        join dim_branch b on f.branch_key = b.branch_key
        join dim_date d on f.date_key = d.date_key
        {where}
        group by d.full_date
        order by d.full_date
    """
    daily_df = query_df(daily_sql, tuple(params))
    if not daily_df.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=daily_df["full_date"],
                y=daily_df["items"],
                name="Items",
                mode="lines",
                fill="tozeroy",
                line=dict(color="#26d0a8", width=2.5, shape="spline"),
                fillcolor="rgba(38, 208, 168, 0.18)",
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Items: %{y:,}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=daily_df["full_date"],
                y=daily_df["orders"],
                name="Đơn",
                mode="lines+markers",
                yaxis="y2",
                line=dict(color="#f0a868", width=2, shape="spline"),
                marker=dict(size=6),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Đơn: %{y:,}<extra></extra>",
            )
        )
        fig.update_layout(
            yaxis=dict(title="Items"),
            yaxis2=dict(title="Đơn", overlaying="y", side="right", showgrid=False),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.06))
        show_fig(style_fig(fig, height=420))
    else:
        st.info("Không có dữ liệu.")

    heatmap_sql = f"""
        select d.day_of_week, p.department_name, count(*) as lines
        from fact_order_line f
        join dim_product p on f.product_key = p.product_key
        join dim_branch b on f.branch_key = b.branch_key
        join dim_date d on f.date_key = d.date_key
        {where}
        group by d.day_of_week, p.department_name
    """
    heatmap_df = query_df(heatmap_sql, tuple(params))
    if not heatmap_df.empty:
        pivot = (
            heatmap_df.pivot(index="department_name", columns="day_of_week", values="lines")
            .fillna(0)
            .reindex(columns=DOW_ORDER)
            .dropna(axis=1, how="all")
        )
        pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
        fig = px.imshow(
            pivot,
            color_continuous_scale=SEQUENTIAL,
            aspect="auto",
            labels=dict(color="Dòng"),
            title="Heatmap: department × ngày trong tuần",
        )
        fig.update_traces(hovertemplate="<b>%{y}</b> · %{x}<br>Dòng: %{z:,}<extra></extra>")
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        show_fig(style_fig(fig, height=480))


def render_products(branches: list[str], dows: list[str], departments: list[str]) -> None:
    where, params = build_filter_clause(branches, dows, departments)
    section("Top sản phẩm", "Sắp xếp theo quantity, màu thể hiện reorder rate")
    top_n = st.slider("Top N sản phẩm", 5, 50, 20, step=5)

    sql = f"""
        select
            p.product_name,
            p.aisle_name,
            p.department_name,
            count(*) as lines,
            sum(f.quantity) as quantity,
            avg(case when f.reordered then 1.0 else 0.0 end) as reorder_rate
        from fact_order_line f
        join dim_product p on f.product_key = p.product_key
        join dim_branch b on f.branch_key = b.branch_key
        join dim_date d on f.date_key = d.date_key
        {where}
        group by p.product_name, p.aisle_name, p.department_name
        order by quantity desc
        limit ?
    """
    df = query_df(sql, tuple(params + [top_n]))
    if df.empty:
        st.info("Không có dữ liệu.")
        return

    df_sorted = df.sort_values("quantity")
    fig = px.bar(
        df_sorted,
        x="quantity",
        y="product_name",
        orientation="h",
        color="reorder_rate",
        color_continuous_scale=SEQUENTIAL,
        range_color=[0, 1],
        custom_data=["aisle_name", "department_name", "reorder_rate"],
        title=f"Top {top_n} sản phẩm theo quantity (màu = reorder rate)",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>Aisle: %{customdata[0]}<br>"
            "Department: %{customdata[1]}<br>Quantity: %{x:,}<br>"
            "Reorder rate: %{customdata[2]:.1%}<extra></extra>"
        )
    )
    fig.update_layout(coloraxis_colorbar=dict(title="Reorder", tickformat=".0%"))
    show_fig(style_fig(fig, height=max(420, top_n * 22)))
    section("Phân tích aisle & cấu trúc danh mục")
    col_aisle, col_sun = st.columns([1, 1])

    with col_aisle:
        aisle_sql = f"""
            select
                p.aisle_name,
                count(*) as lines,
                avg(case when f.reordered then 1.0 else 0.0 end) as reorder_rate
            from fact_order_line f
            join dim_product p on f.product_key = p.product_key
            join dim_branch b on f.branch_key = b.branch_key
            join dim_date d on f.date_key = d.date_key
            {where}
            group by p.aisle_name
            order by reorder_rate desc
            limit 20
        """
        aisle_df = query_df(aisle_sql, tuple(params))
        if not aisle_df.empty:
            aisle_df = aisle_df.sort_values("reorder_rate")
            fig = px.bar(
                aisle_df,
                x="reorder_rate",
                y="aisle_name",
                orientation="h",
                color="lines",
                color_continuous_scale=SEQUENTIAL,
                title="Top 20 aisles theo reorder rate",
            )
            fig.update_traces(
                hovertemplate="<b>%{y}</b><br>Reorder rate: %{x:.1%}<br>Dòng: %{marker.color:,}<extra></extra>"
            )
            fig.update_layout(
                xaxis_tickformat=".0%",
                xaxis_title="Reorder rate",
                yaxis_title=None,
                coloraxis_colorbar=dict(title="Dòng"),
            )
            show_fig(style_fig(fig, height=520))

    with col_sun:
        sun_sql = f"""
            select p.department_name, p.aisle_name, count(*) as lines
            from fact_order_line f
            join dim_product p on f.product_key = p.product_key
            join dim_branch b on f.branch_key = b.branch_key
            join dim_date d on f.date_key = d.date_key
            {where}
            group by p.department_name, p.aisle_name
            order by lines desc
        """
        sun_df = query_df(sun_sql, tuple(params))
        if not sun_df.empty:
            fig = px.sunburst(
                sun_df,
                path=["department_name", "aisle_name"],
                values="lines",
                color="lines",
                color_continuous_scale=SEQUENTIAL,
                title="Sunburst: department > aisle",
            )
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>Dòng: %{value:,}<extra></extra>",
                insidetextorientation="radial",
            )
            show_fig(style_fig(fig, height=520))
    section(f"Bảng chi tiết top {top_n} sản phẩm")
    df_display = df.copy()
    df_display["reorder_rate"] = (df_display["reorder_rate"] * 100).round(1)
    st.dataframe(
        df_display,
        width="stretch",
        hide_index=True,
        column_config={
            "quantity": st.column_config.NumberColumn(format="%d"),
            "lines": st.column_config.NumberColumn(format="%d"),
            "reorder_rate": st.column_config.ProgressColumn(
                "Reorder rate (%)", min_value=0, max_value=100, format="%.1f%%"
            ),
        },
    )


def render_customers(branches: list[str], dows: list[str], departments: list[str]) -> None:
    where, params = build_filter_clause(branches, dows, departments)
    section("Chân dung khách hàng", "Phân bổ tier và phân bổ tần suất đặt")

    tier_sql = """
        select membership_tier, count(*) as customers, avg(total_orders) as avg_orders
        from dim_customer
        group by membership_tier
        order by customers desc
    """
    tier_df = query_df(tier_sql)

    col1, col2 = st.columns([1, 1])
    with col1:
        if not tier_df.empty:
            fig = px.pie(
                tier_df,
                names="membership_tier",
                values="customers",
                hole=0.55,
                color_discrete_sequence=CATEGORICAL,
                title="Phân bổ membership tier",
            )
            fig.update_traces(
                textposition="outside",
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Khách: %{value:,}<br>Tỉ lệ: %{percent}<extra></extra>",
            )
            show_fig(style_fig(fig, height=380))

    with col2:
        hist_df = query_df("select total_orders from dim_customer")
        if not hist_df.empty:
            fig = px.histogram(
                hist_df,
                x="total_orders",
                nbins=20,
                color_discrete_sequence=["#26d0a8"],
                title="Phân bổ total_orders / khách",
            )
            fig.update_traces(hovertemplate="Khoảng %{x}<br>Khách: %{y:,}<extra></extra>")
            fig.update_layout(xaxis_title="Total orders", yaxis_title="Số khách", bargap=0.05)
            show_fig(style_fig(fig, height=380))
    section("Top khách hàng")
    top_n = st.slider("Top N khách", 5, 50, 20, step=5, key="cust_top_n")
    cust_sql = f"""
        select
            c.user_id_nk,
            c.membership_tier,
            count(distinct f.order_id_nk) as orders,
            count(*) as lines,
            sum(f.quantity) as quantity
        from fact_order_line f
        join dim_customer c on f.customer_key = c.customer_key
        join dim_product p on f.product_key = p.product_key
        join dim_branch b on f.branch_key = b.branch_key
        join dim_date d on f.date_key = d.date_key
        {where}
        group by c.user_id_nk, c.membership_tier
        order by lines desc
        limit ?
    """
    cust_df = query_df(cust_sql, tuple(params + [top_n]))
    if cust_df.empty:
        st.info("Không có dữ liệu khách hàng phù hợp filter.")
        return

    fig = px.bar(
        cust_df.sort_values("lines"),
        x="lines",
        y="user_id_nk",
        orientation="h",
        color="membership_tier",
        color_discrete_sequence=CATEGORICAL,
        custom_data=["orders", "quantity", "membership_tier"],
        title=f"Top {top_n} khách theo số dòng",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>User %{y}</b><br>Tier: %{customdata[2]}<br>"
            "Đơn: %{customdata[0]:,}<br>Dòng: %{x:,}<br>"
            "Quantity: %{customdata[1]:,}<extra></extra>"
        )
    )
    fig.update_layout(yaxis_title=None, legend_title="Tier")
    show_fig(style_fig(fig, height=max(420, top_n * 22)))

    st.dataframe(
        cust_df,
        width="stretch",
        hide_index=True,
        column_config={
            "orders": st.column_config.NumberColumn(format="%d"),
            "lines": st.column_config.NumberColumn(format="%d"),
            "quantity": st.column_config.NumberColumn(format="%d"),
        },
    )


def render_market_basket() -> None:
    rules = load_csv("association_rules.csv")
    bundles = load_csv("bundle_recommendations.csv")
    threshold = load_csv("threshold_comparison.csv")
    basket = load_csv("basket_summary.csv")

    if rules.empty and bundles.empty and threshold.empty and basket.empty:
        st.warning(
            "Chưa có output data mining trong `outputs/data_mining/`. "
            "Hãy chạy job market basket trước."
        )
        return

    if not basket.empty:
        section("Basket summary")
        st.dataframe(basket, width="stretch", hide_index=True)

    if not rules.empty:
        section("Association rules", "Lọc theo support / confidence / lift")
        cols = st.columns(3)
        min_support = _safe_slider(cols[0], "Min support", rules["support"], step=0.001, fmt="%.4f")
        min_confidence = _safe_slider(cols[1], "Min confidence", rules["confidence"], step=0.01)
        min_lift = _safe_slider(cols[2], "Min lift", rules["lift"], step=0.1)
        filtered = rules[
            (rules["support"] >= min_support)
            & (rules["confidence"] >= min_confidence)
            & (rules["lift"] >= min_lift)
        ].sort_values("lift", ascending=False)
        st.caption(f"Còn {len(filtered)} / {len(rules)} rule sau filter.")

        if not filtered.empty and {"support", "confidence", "lift"}.issubset(filtered.columns):
            scatter_df = filtered.replace([float("inf"), float("-inf")], pd.NA).dropna(
                subset=["support", "confidence", "lift"]
            )
            if not scatter_df.empty:
                fig = px.scatter(
                    scatter_df,
                    x="support",
                    y="confidence",
                    size="lift",
                    color="lift",
                    color_continuous_scale=SEQUENTIAL,
                    hover_data=[c for c in ["antecedents", "consequents"] if c in scatter_df.columns],
                    title="Rule scatter — support × confidence (size/màu = lift)",
                )
                fig.update_layout(xaxis_tickformat=".4f", yaxis_tickformat=".0%")
                show_fig(style_fig(fig, height=420))

        st.dataframe(filtered, width="stretch", hide_index=True)

    if not bundles.empty:
        section("Bundle recommendations")
        st.dataframe(bundles, width="stretch", hide_index=True)

    if not threshold.empty:
        section("Threshold comparison")
        numeric_cols = [
            c for c in threshold.columns if pd.api.types.is_numeric_dtype(threshold[c])
        ]
        if len(numeric_cols) >= 2:
            x_candidates = [c for c in threshold.columns if "support" in c.lower()] or [
                threshold.columns[0]
            ]
            x_col = x_candidates[0]
            y_cols = [c for c in numeric_cols if c != x_col]
            long = threshold.melt(id_vars=[x_col], value_vars=y_cols, var_name="metric", value_name="value")
            fig = px.line(
                long,
                x=x_col,
                y="value",
                color="metric",
                markers=True,
                color_discrete_sequence=CATEGORICAL,
                title=f"Threshold comparison theo {x_col}",
            )
            show_fig(style_fig(fig, height=380))
        st.dataframe(threshold, width="stretch", hide_index=True)


def render_etl_log() -> None:
    log_df = query_df(
        """
        select run_id, stage, started_at, finished_at, status, rows_loaded, watermark_order_id, message
        from etl_log
        order by started_at desc nulls last
        limit 200
        """
    )
    if log_df.empty:
        st.info("etl_log trống.")
        return

    success = (log_df["status"] == "SUCCESS").sum()
    failed = (log_df["status"] == "FAILED").sum()
    cols = st.columns(4)
    cols[0].metric("Tổng run", len(log_df))
    cols[1].metric("Success", int(success))
    cols[2].metric("Failed", int(failed))
    success_rate = (success / len(log_df) * 100) if len(log_df) else 0
    cols[3].metric("Success rate", f"{success_rate:.1f}%")
    style_metric_cards(
        background_color="rgba(255,255,255,0.03)",
        border_left_color="#26d0a8",
        border_color="rgba(255,255,255,0.08)",
        box_shadow=False,
    )
    section("Timeline", "Khoảng thời gian từng stage chạy")
    timeline_df = log_df.dropna(subset=["started_at"]).copy()
    if not timeline_df.empty:
        timeline_df["finished_at"] = timeline_df["finished_at"].fillna(timeline_df["started_at"])
        timeline_df = timeline_df.sort_values("started_at")
        fig = px.timeline(
            timeline_df,
            x_start="started_at",
            x_end="finished_at",
            y="stage",
            color="status",
            color_discrete_map={"SUCCESS": "#26d0a8", "FAILED": "#ef6f6c"},
            hover_data={"rows_loaded": True, "run_id": True, "message": True},
            title="ETL timeline (status theo stage)",
        )
        fig.update_yaxes(autorange="reversed")
        show_fig(style_fig(fig, height=320))
    section("Chi tiết log")
    cols = st.columns(2)
    stage_filter = cols[0].multiselect("Stage", sorted(log_df["stage"].unique().tolist()))
    status_filter = cols[1].multiselect("Status", sorted(log_df["status"].unique().tolist()))
    view = log_df
    if stage_filter:
        view = view[view["stage"].isin(stage_filter)]
    if status_filter:
        view = view[view["status"].isin(status_filter)]
    st.dataframe(
        view,
        width="stretch",
        hide_index=True,
        column_config={
            "rows_loaded": st.column_config.NumberColumn(format="%d"),
            "started_at": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm:ss"),
            "finished_at": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm:ss"),
        },
    )


@st.cache_data(show_spinner=False)
def load_hero_stats() -> tuple[dict[str, int], str | None]:
    row = query_df(
        """
        select
            count(distinct order_id_nk) as orders,
            count(*) as lines,
            count(distinct customer_key) as customers,
            count(distinct product_key) as products
        from fact_order_line
        """
    ).iloc[0]
    departments = query_df("select count(distinct department_name) as n from dim_product").iloc[0]["n"]
    last_run = query_df(
        "select max(finished_at) as t from etl_log where status = 'SUCCESS'"
    ).iloc[0]["t"]
    last_run_str: str | None = None
    if pd.notna(last_run):
        ts = pd.to_datetime(last_run)
        last_run_str = ts.strftime("%Y-%m-%d %H:%M")
    stats = {
        "orders": int(row["orders"]),
        "lines": int(row["lines"]),
        "customers": int(row["customers"]),
        "products": int(row["products"]),
        "departments": int(departments),
    }
    return stats, last_run_str


def main() -> None:
    branches = query_df("select distinct branch_name from dim_branch order by 1")["branch_name"].tolist()
    dows = query_df("select distinct day_of_week from dim_date")["day_of_week"].tolist()
    departments = query_df("select distinct department_name from dim_product order by 1")["department_name"].tolist()
    stats, last_run = load_hero_stats()

    render_hero(stats, last_run)

    with st.sidebar:
        st.markdown("### Tuỳ chọn")
        st.caption(f"DB: `{DB_PATH.relative_to(ROOT)}`")
        st.caption(
            f"{len(branches)} chi nhánh · {len(departments)} department · {len(dows)} ngày trong tuần"
        )
        st.caption(f"Phiên: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if st.button("Clear cache", width="stretch", type="primary"):
            st.cache_data.clear()
            st.rerun()
        st.markdown("##### Hướng dẫn nhanh")
        st.caption(
            "1. Chọn filter ở bộ lọc chung (chi nhánh / ngày / department).\n\n"
            "2. Mỗi tab có chart riêng + bảng chi tiết.\n\n"
            "3. Hover chart để xem tooltip; dùng range slider để zoom timeline."
        )

    with st.expander("Bộ lọc chung — áp dụng cho 3 tab dữ liệu warehouse", expanded=False):
        cols = st.columns(3)
        sel_branches = cols[0].multiselect("Chi nhánh", branches) if len(branches) > 1 else []
        if len(branches) <= 1:
            cols[0].caption(f"Chi nhánh: {branches[0] if branches else '—'} (chỉ 1)")
        sel_dows = cols[1].multiselect("Ngày trong tuần", [d for d in DOW_ORDER if d in dows])
        sel_depts = cols[2].multiselect("Department", departments)

    tabs = st.tabs(["Tổng quan", "Sản phẩm", "Khách hàng", "Market basket", "ETL log"])
    with tabs[0]:
        render_overview(sel_branches, sel_dows, sel_depts)
    with tabs[1]:
        render_products(sel_branches, sel_dows, sel_depts)
    with tabs[2]:
        render_customers(sel_branches, sel_dows, sel_depts)
    with tabs[3]:
        render_market_basket()
    with tabs[4]:
        render_etl_log()


if __name__ == "__main__":
    main()

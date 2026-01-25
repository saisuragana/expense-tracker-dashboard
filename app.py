import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ✅ Absolute file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "expenses.csv")


# -------------------- DATA FUNCTIONS --------------------
def load_data():
    if not os.path.exists(FILE_NAME) or os.path.getsize(FILE_NAME) == 0:
        df = pd.DataFrame(columns=["date", "category", "amount", "note"])
        df.to_csv(FILE_NAME, index=False)
        return df
    return pd.read_csv(FILE_NAME)


def save_data(df):
    df.to_csv(FILE_NAME, index=False)


def append_expense(row):
    df_new = pd.DataFrame([row])

    # If file doesn't exist or empty -> write header
    if (not os.path.exists(FILE_NAME)) or (os.path.getsize(FILE_NAME) == 0):
        df_new.to_csv(FILE_NAME, index=False)
    else:
        # append without header
        df_new.to_csv(FILE_NAME, mode="a", header=False, index=False)



def prepare_df(df):
    """Convert types safely and remove invalid rows."""
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    return df


# -------------------- STREAMLIT CONFIG --------------------
st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")

st.title("💰 Expense Tracker Dashboard")


st.write("Track your daily expenses + visualize analytics 📊")
st.markdown("""
<style>
/* Main background */
.stApp {
    background: linear-gradient(180deg, #0E1117 0%, #0B0F14 100%);
}

/* Make headers look premium */
h1, h2, h3 {
    letter-spacing: 0.5px;
}

/* Cards for metrics */
div[data-testid="stMetric"] {
    background-color: rgba(255,255,255,0.06);
    padding: 16px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Buttons style */
div.stButton > button {
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 600;
}

/* Dataframe container */
div[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Tabs style */
button[data-baseweb="tab"] {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)





# -------------------- LOAD DATA --------------------
try:
    df = load_data()
except Exception as e:
    st.error("❌ Error while loading data.")
    st.code(str(e))
    st.stop()

df = prepare_df(df)

# -------------------- TABS --------------------
tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Expense", "📌 Expenses", "📈 Insights", "📅 Reports"])


# ---------------- TAB 1: ADD EXPENSE ----------------
with tab1:
    st.subheader("➕ Add New Expense")

    with st.form("add_expense_form"):
        date = st.date_input("Date", datetime.today())
        category = st.selectbox(
            "Category",
            ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"],
        )
        amount = st.number_input("Amount (₹)", min_value=1.0, step=1.0)
        note = st.text_input("Note (optional)")

        submitted = st.form_submit_button("Add Expense ✅")

    if submitted:
        new_row = {
            "date": str(date),
            "category": category,
            "amount": float(amount),
            "note": note,
        }
        append_expense(new_row)
        st.success("✅ Expense Added Successfully")
        st.rerun()


# ---------------- TAB 2: EXPENSES + FILTER + DELETE ----------------
with tab2:
    st.subheader("📌 Expenses")

    df = prepare_df(load_data())

    if df.empty:
        st.warning("No expenses yet. Add your first expense ✅")
        st.stop()

    # Filters inside expander (clean UI)
    with st.expander("🔍 Filters", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            selected_category = st.selectbox(
                "Filter by Category",
                ["All"] + sorted(df["category"].dropna().unique().tolist()),
            )

        with col2:
            month_list = sorted(df["date"].dt.strftime("%Y-%m").dropna().unique().tolist())
            selected_month = st.selectbox("Filter by Month", ["All"] + month_list)

    filtered_df = df.copy()

    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    if selected_month != "All":
        filtered_df = filtered_df[filtered_df["date"].dt.strftime("%Y-%m") == selected_month]

    # ✅ ONE clean table with S.No
    show_df = filtered_df.copy().reset_index(drop=True)
    show_df.insert(0, "S.No", range(1, len(show_df) + 1))

    # Nice readable date in table
    show_df["date"] = show_df["date"].dt.strftime("%Y-%m-%d")

    st.dataframe(show_df, use_container_width=True)

    # ✅ Delete by S.No
    st.markdown("### ❌ Delete an Expense")

    if len(show_df) > 0:
        selected_sno = st.selectbox("Select S.No to delete", show_df["S.No"].tolist())

        if st.button("Delete Selected Expense 🚮"):
            row_to_delete = selected_sno - 1
            record = show_df.iloc[row_to_delete]

            # Reload full df (original data)
            df2 = prepare_df(load_data()).reset_index(drop=True)

            # Match record (delete only ONE matching row)
            mask = (
                (df2["date"].dt.strftime("%Y-%m-%d") == record["date"]) &
                (df2["category"] == record["category"]) &
                (df2["amount"] == record["amount"]) &
                (df2["note"].fillna("") == str(record["note"]))
            )

            idx_to_drop = df2[mask].index
            if len(idx_to_drop) > 0:
                df2 = df2.drop(idx_to_drop[0]).reset_index(drop=True)
                save_data(df2)
                st.success("✅ Deleted Successfully!")
                st.rerun()
            else:
                st.error("❌ Could not find that record to delete.")


# ---------------- TAB 3: INSIGHTS (PLOTLY GRAPHS) ----------------
with tab3:
    st.subheader("📈 Insights")

    df = prepare_df(load_data())

    if df.empty:
        st.warning("No expenses to analyze ✅")
        st.stop()

    month_list = sorted(df["date"].dt.strftime("%Y-%m").dropna().unique().tolist())
    selected_month = st.selectbox("Insights Month", ["All"] + month_list)

    analytics_df = df.copy()
    if selected_month != "All":
        analytics_df = analytics_df[analytics_df["date"].dt.strftime("%Y-%m") == selected_month]

    total_spent = analytics_df["amount"].sum()
    avg_spent = analytics_df["amount"].mean()

    colA, colB, colC = st.columns(3)
    colA.metric("Total Spent (₹)", f"{total_spent:.2f}")
    colB.metric("Average Expense (₹)", f"{avg_spent:.2f}")
    colC.metric("Transactions", f"{len(analytics_df)}")

    colX, colY = st.columns(2)

    with colX:
        st.write("✅ Category-wise Spending")
        fig = px.pie(
            analytics_df,
            names="category",
            values="amount",
            title="Category Spending %"
        )
        st.plotly_chart(fig, use_container_width=True)

    with colY:
        st.write("✅ Daily Spending Trend")

        daily_sum = analytics_df.groupby(analytics_df["date"].dt.date)["amount"].sum().reset_index()
        daily_sum.columns = ["date", "amount"]

        fig = px.line(
            daily_sum,
            x="date",
            y="amount",
            title="Daily Spending Trend",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ⬇️ Download Insights Data")
    csv = analytics_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "insights_expenses.csv", "text/csv")


# ---------------- TAB 4: REPORTS (YEAR + MONTH RANGE) ----------------
with tab4:
    st.subheader("📅 Reports (Year & Month Filters)")

    df = prepare_df(load_data())

    if df.empty:
        st.warning("No expenses yet. Add expenses first ✅")
        st.stop()

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["year_month"] = df["date"].dt.to_period("M").astype(str)

    years = sorted(df["year"].unique().tolist())

    colA, colB = st.columns(2)
    with colA:
        start_year = st.selectbox("Start Year", years, index=0)
    with colB:
        end_year = st.selectbox("End Year", years, index=len(years) - 1)

    if start_year > end_year:
        st.error("❌ Start Year cannot be greater than End Year")
        st.stop()

    filtered = df[(df["year"] >= start_year) & (df["year"] <= end_year)]

    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    colC, colD = st.columns(2)
    with colC:
        start_month = st.selectbox(
            "Start Month",
            list(range(1, 13)),
            format_func=lambda x: month_names[x],
            index=0
        )
    with colD:
        end_month = st.selectbox(
            "End Month",
            list(range(1, 13)),
            format_func=lambda x: month_names[x],
            index=11
        )

    if start_month > end_month:
        st.error("❌ Start Month cannot be greater than End Month")
        st.stop()

    filtered = filtered[(filtered["month"] >= start_month) & (filtered["month"] <= end_month)]

    monthly_sum = filtered.groupby("year_month")["amount"].sum().reset_index()

    st.markdown("### 📊 Month-wise Spending (Selected Range)")

    if monthly_sum.empty:
        st.warning("No data found for selected year/month range ✅")
    else:
        fig = px.bar(
            monthly_sum,
            x="year_month",
            y="amount",
            title="Monthly Spending Trend",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

        total = monthly_sum["amount"].sum()
        st.success(f"✅ Total Spending in Selected Range: ₹{total:.2f}")

        st.markdown("### 📌 Monthly Spending Table")
        st.dataframe(monthly_sum, use_container_width=True)

    st.markdown("---")
    st.subheader("⚠️ Danger Zone")
    if st.button("🧹 Clear All Expenses (Reset)"):
        empty_df = pd.DataFrame(columns=["date", "category", "amount", "note"])
        save_data(empty_df)
        st.success("✅ All expenses cleared!")
        st.rerun()


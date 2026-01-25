import plotly.express as px
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "expenses.csv")

st.caption(f"📁 Saving expenses to: {FILE_NAME}")


def load_data():
    if not os.path.exists(FILE_NAME):
        df = pd.DataFrame(columns=["date", "category", "amount", "note"])
        df.to_csv(FILE_NAME, index=False)
        return df

    df = pd.read_csv(FILE_NAME)

    if df.shape[1] == 0:
        df = pd.DataFrame(columns=["date", "category", "amount", "note"])
        df.to_csv(FILE_NAME, index=False)

    return df


def save_data(df):
    df.to_csv(FILE_NAME, index=False)


st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")

st.title("💰 Expense Tracker Dashboard")
st.write("Track your daily expenses + visualize analytics 📊")

# ✅ Load data FIRST (ONLY ONCE)
try:
    df = load_data()
except Exception as e:
    st.error("❌ Error while loading data.")
    st.code(str(e))
    st.stop()

# ✅ Convert types safely
df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# ✅ Tabs UI
tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Expense", "📌 Expenses", "📈 Insights", "📅 Reports"])

# ---------------- TAB 1: ADD EXPENSE ----------------
with tab1:
    st.subheader("➕ Add New Expense")

    date = st.date_input("Date", datetime.today())
    category = st.selectbox(
        "Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"]
    )
    amount = st.number_input("Amount (₹)", min_value=1.0, step=1.0)
    note = st.text_input("Note (optional)")

    if st.button("Add Expense ✅"):
        new_row = {
            "date": str(date),
            "category": category,
            "amount": float(amount),
            "note": note
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)

        # ✅ reload again from CSV
        df = load_data()

        st.success("✅ Expense Added Successfully")
        st.rerun()

# ---------------- TAB 2: EXPENSES + FILTER + DELETE ----------------
with tab2:
    st.subheader("📌 All Expenses")

    if df.empty:
        st.warning("No expenses yet. Add your first expense ✅")
    else:
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

        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("### ❌ Delete an Expense")
        if len(filtered_df) > 0:
            selected_index = st.selectbox(
                "Select a transaction to delete (by index)",
                filtered_df.index.tolist(),
            )

            if st.button("Delete Selected Expense 🚮"):
                df = df.drop(index=selected_index)
                save_data(df)
                st.success("✅ Expense deleted successfully!")
                st.rerun()

# ---------------- TAB 3: ANALYTICS ----------------
with tab3:
    st.subheader("📊 Analytics")

    if df.empty:
        st.warning("No expenses to analyze ✅")
    else:
        # Use same filter idea for analytics
        month_list = sorted(df["date"].dt.strftime("%Y-%m").dropna().unique().tolist())
        selected_month = st.selectbox("Analytics Month", ["All"] + month_list)

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
            cat_sum = (
                analytics_df.groupby("category")["amount"]
                .sum()
                .sort_values(ascending=False)
            )

            fig = px.pie(analytics_df, names="category", values="amount", title="Category Spending %")
            st.plotly_chart(fig, use_container_width=True)


        with colY:
            st.write("✅ Daily Spending Trend")

            daily_sum = analytics_df.groupby(analytics_df["date"].dt.date)["amount"].sum().reset_index()
            daily_sum.columns = ["date", "amount"]

            fig = px.line(daily_sum, x="date", y="amount", title="Daily Spending Trend", markers=True)
            st.plotly_chart(fig, use_container_width=True)


# ---------------- TAB 4: MONTHLY REPORT (YEAR + MONTH RANGE) ----------------
with tab4:
    st.subheader("📅 Monthly Report (Year & Month Filters)")

    if df.empty:
        st.warning("No expenses yet. Add expenses first ✅")
    else:
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
                index=0,
            )
        with colD:
            end_month = st.selectbox(
                "End Month",
                list(range(1, 13)),
                format_func=lambda x: month_names[x],
                index=11,
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
            fig = px.line(
                monthly_sum,
                x="year_month",
                y="amount",
                title="Monthly Spending Trend",
                markers=True
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

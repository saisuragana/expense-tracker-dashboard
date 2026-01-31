import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client

# ---------- Supabase ----------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ---------- DB Functions ----------
def load_data():
    res = supabase.table("expenses").select("*").order("date", desc=True).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["amount"] = pd.to_numeric(df["amount"])
        df["date"] = pd.to_datetime(df["date"])
    return df


def add_expense(row):
    supabase.table("expenses").insert(row).execute()


def delete_expense(expense_id):
    supabase.table("expenses").delete().eq("id", expense_id).execute()


# ---------- UI ----------
st.set_page_config("Expense Tracker", "💰", layout="wide")
st.title("💰 Expense Tracker Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(
    ["➕ Add Expense", "📌 Expenses", "📈 Insights", "📅 Reports"]
)

# ---------- TAB 1 ----------
with tab1:
    st.subheader("Add New Expense")

    with st.form("add_form"):
        date = st.date_input("Date", datetime.today())
        category = st.selectbox(
            "Category",
            ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"]
        )
        amount = st.number_input("Amount", min_value=1.0)
        note = st.text_input("Note")

        submit = st.form_submit_button("Add Expense")

    if submit:
        add_expense({
            "date": str(date),
            "category": category,
            "amount": float(amount),
            "note": note
        })
        st.success("Added!")
        st.rerun()


# ---------- TAB 2 ----------
# ---------------- TAB 2: EXPENSES + CLICK TO DELETE ----------------
with tab2:
    st.subheader("📌 All Expenses")

    df = load_data()

    if df.empty:
        st.warning("No expenses yet. Add your first expense ✅")
    else:
        # Proper types
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Filters
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
            filtered_df = filtered_df[
                filtered_df["date"].dt.strftime("%Y-%m") == selected_month
            ]

        # Show clean table (no id column)
        show_df = filtered_df.copy()
        show_df["date"] = show_df["date"].dt.strftime("%Y-%m-%d")
        clean_df = (
            show_df
            .drop(columns=["id", "created_at"], errors="ignore")
            .reset_index(drop=True)
        )

        st.dataframe(clean_df, use_container_width=True)


        st.markdown("### 🗑️ Tap a row to delete")

        # Click-to-delete dropdown (acts like selecting row)
        selected_id = st.selectbox(
            "Select expense to delete",
            filtered_df["id"],
            format_func=lambda x: f"{filtered_df[filtered_df['id']==x]['date'].values[0]} | "
                                  f"{filtered_df[filtered_df['id']==x]['category'].values[0]} | "
                                  f"₹{filtered_df[filtered_df['id']==x]['amount'].values[0]}"
        )

        if st.button("Delete Selected Expense"):
            delete_expense(selected_id)
            st.success("✅ Expense Deleted")
            st.rerun()


# ---------- TAB 3 ----------
with tab3:
    st.subheader("Insights")

    df = load_data()

    if not df.empty:
        fig = px.pie(df, names="category", values="amount")
        st.plotly_chart(fig, use_container_width=True)

        daily = df.groupby(df["date"].dt.date)["amount"].sum().reset_index()
        fig2 = px.line(daily, x="date", y="amount")
        st.plotly_chart(fig2, use_container_width=True)


# ---------- TAB 4 ----------
with tab4:
    st.subheader("Monthly Report")

    df = load_data()

    if not df.empty:
        df["year_month"] = df["date"].dt.to_period("M").astype(str)
        monthly = df.groupby("year_month")["amount"].sum().reset_index()

        fig = px.bar(monthly, x="year_month", y="amount")
        st.plotly_chart(fig, use_container_width=True)

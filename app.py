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

# ---------- DB FUNCTIONS ----------
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


def clear_all_expenses():
    supabase.table("expenses").delete().neq("id", 0).execute()


# ---------- UI ----------
st.set_page_config("Expense Tracker", "💰", layout="wide")
st.title("💰 Expense Tracker Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(
    ["➕ Add Expense", "📌 Expenses", "📈 Insights", "📅 Reports"]
)

# ---------- TAB 1 : ADD ----------
with tab1:
    st.subheader("Add New Expense")

    with st.form("add_form"):
        date = st.date_input("Date", datetime.today())
        category = st.selectbox(
            "Category",
            ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"],
        )
        amount = st.number_input("Amount (₹)", min_value=1.0)
        note = st.text_input("Note")

        submitted = st.form_submit_button("Add Expense")

    if submitted:
        add_expense(
            {
                "date": str(date),
                "category": category,
                "amount": float(amount),
                "note": note,
            }
        )
        st.success("Expense Added")
        st.rerun()


# ---------- TAB 2 : VIEW + DELETE ----------
with tab2:
    st.subheader("All Expenses")

    df = load_data()

    if df.empty:
        st.warning("No expenses yet")
    else:
        clean_df = (
            df.drop(columns=["created_at"], errors="ignore")
            .reset_index(drop=True)
        )
        clean_df["date"] = clean_df["date"].dt.strftime("%Y-%m-%d")

        st.dataframe(clean_df.drop(columns=["id"]), use_container_width=True)

        st.markdown("### Delete Expense")

        selected_id = st.selectbox(
            "Select expense",
            df["id"],
            format_func=lambda x: f"{df[df['id']==x]['date'].values[0]} | "
                                  f"{df[df['id']==x]['category'].values[0]} | "
                                  f"₹{df[df['id']==x]['amount'].values[0]}",
        )

        if st.button("Delete Selected Expense"):
            delete_expense(selected_id)
            st.success("Deleted")
            st.rerun()


# ---------- TAB 3 : INSIGHTS ----------
with tab3:
    st.subheader("Insights")

    df = load_data()

    if not df.empty:
        fig = px.pie(df, names="category", values="amount")
        st.plotly_chart(fig, use_container_width=True)

        daily = df.groupby(df["date"].dt.date)["amount"].sum().reset_index()
        fig2 = px.line(daily, x="date", y="amount", markers=True)
        st.plotly_chart(fig2, use_container_width=True)


# ---------- TAB 4 : REPORTS ----------
with tab4:
    st.subheader("Monthly Report")

    df = load_data()

    if not df.empty:
        df["year_month"] = df["date"].dt.to_period("M").astype(str)
        monthly = df.groupby("year_month")["amount"].sum().reset_index()

        fig = px.bar(monthly, x="year_month", y="amount", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Danger Zone")
        if st.button("Clear All Expenses"):
            clear_all_expenses()
            st.success("All expenses cleared")
            st.rerun()
    
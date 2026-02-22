""""
for running the app, use the command:
    streamlit run app.py

for sop runing:
      contrlo + c ,

"""""

import streamlit as st
import pandas as pd
from dataclasses import dataclass
from datetime import date as dt_date, datetime
import calendar
from db.db import (
    create_user,
    authenticate_user,
    get_security_question,
    verify_security_answer,
    update_password,
    verify_user_phone,
    get_or_create_month,
    add_category,
    load_categories,
    add_transaction,
    load_transactions
)

SECURITY_QUESTIONS = [
    "What is your favorite color?",
    "What is the name of your first school?",
    "What city were you born in?"
]


st.image("assets/logo.png", width=200)
st.title("Budget Tracker")


tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Forgot Password"])



# LOGIN
with tab1:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.success("Logged in successfully ✅")
            st.session_state["user_id"] = str(user[0])
            st.rerun()
        else:
            st.error("Invalid credentials ❌")

# SIGNUP
with tab2:
    st.subheader("Create Account")
    new_user = st.text_input("Username", key="su1")
    phone = st.text_input("Phone", key="su2")
    new_pass = st.text_input("Password", type="password", key="su3")
    question = st.selectbox(
    "Security Question",
    SECURITY_QUESTIONS,
    key="su4"
)
    answer = st.text_input("Security Answer", key="su5")

    if st.button("Sign Up"):
        try:
            create_user(new_user, phone, new_pass, question, answer)
            st.success("Account created 🎉")
        except Exception as e:
            st.error("User already exists or error occurred")

# FORGOT PASSWORD
with tab3:
    st.subheader("Forgot Password")

    # STEP 1: verify user + phone
    fp_user = st.text_input("Username", key="fp_user")
    fp_phone = st.text_input("Phone Number", key="fp_phone")

    if st.button("Verify User"):
        if verify_user_phone(fp_user, fp_phone):
            st.session_state["fp_verified"] = True
            st.session_state["fp_username"] = fp_user
            st.session_state["fp_question"] = get_security_question(fp_user)
        else:
            st.error("Username or phone number is incorrect ❌")

    # STEP 2: security question + reset
    if st.session_state.get("fp_verified"):
        st.info(st.session_state["fp_question"])

        answer = st.text_input("Security Answer", key="fp_answer")
        new_pass = st.text_input(
            "New Password",
            type="password",
            key="fp_new_pass"
        )

        if st.button("Reset Password"):
            if verify_security_answer(
                st.session_state["fp_username"],
                answer
            ):
                update_password(
                    st.session_state["fp_username"],
                    new_pass
                )
                st.success("Password updated successfully ✅")

                # تنظيف الـ session
                for k in [
                    "fp_verified",
                    "fp_username",
                    "fp_question"
                ]:
                    st.session_state.pop(k, None)
            else:
                st.error("Wrong security answer ❌")

is_logged_in = "user_id" in st.session_state
today = dt_date.today()

month_options = []
for i in range(12):
    m = today.month - i
    y = today.year
    while m <= 0:
        m += 12
        y -= 1
    month_options.append(f"{y}-{m:02d}")
if is_logged_in:



    if st.button("Logout 🚪"):
        st.session_state.clear()
        st.rerun()

# =====================
# AUTH GUARD (VERY IMPORTANT)
# =====================
if "user_id" not in st.session_state:
    st.warning("🔐 Please login to continue")
    st.stop()




def apply_custom_width():
    st.markdown(
        """
        <style>
        /* This targets the main content container */
        .block-container {
            max-width: 65%;

        }
        
        /* Optional: Adjust for medium screens so it doesn't get too narrow */
        @media (max-width: 1500px) {
            .block-container {
                max-width: 80%;
            }
        }

            @media (max-width: 1200px) {
            .block-container {
                max-width: 85%;
            }
        }

        @media (max-width: 900px) {
            .block-container {
                max-width: 95%;
            }
        }

        /* Optional: Full width on mobile */
        @media (max-width: 640px) {
            .block-container {
                max-width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    
# =========================
# Helper Functions
# =========================
def month_key_from_date(d):
    return d.strftime("%Y-%m")

def calc_status(spent, limit):

    return ""

    if limit <= 0.00:
        return "ℹ️"
    ratio = spent / limit
    if ratio < 0.50:
        return "✅"
    if ratio < 0.80:
        return "⚠️"
    if ratio < 1.00:
        return "🔶"
    return "🛑"


def get_progress_color(ratio):
    if ratio < 0.50:
        return "#4CAF50"  # Green (Safe)
    elif ratio < 0.80:
        return "#FFC107"  # Yellow (Alert)
    elif ratio < 1.00:
        return "#FF9800"  # Orange (Warning)
    else:
        return "#F44336"  # Red (Danger)

# =========================
# Data Models
# =========================
@dataclass
class Category:
    name: str
    limit_type: str  # "percent" or "fixed"
    value: float     # percent or SAR

    def calc_limit(self, monthly_budget):
        if self.limit_type == "percent":
            return monthly_budget * (self.value / 100.0)
        return self.value

    def display_limit(self):
        if self.limit_type == "percent":
            return f"{self.value:g}%"
        return f"{self.value:g} SAR"

@dataclass
class Expense:
    expense_id: int
    d: dt_date
    amount: float
    category: str
    description: str

class BudgetMonth:
    def __init__(self, month_key):
        self.month_key = month_key
        self.budget = None
        self.categories = {}
        self.expenses = []
        self._next_expense_id = 1

    def is_setup(self):
        return self.budget is not None and len(self.categories) > 0

    def set_budget(self, new_budget):
        self.budget = new_budget

    def add_category(self, cat):
        name = cat.name.strip()
        if not name or name in self.categories:
            return False
        self.categories[name] = cat
        return True

    def update_category_limit(self, name, limit_type, value):
        if name not in self.categories:
            return False
        self.categories[name].limit_type = limit_type
        self.categories[name].value = value
        return True

    def category_has_expenses(self, name):
        return any(e.category == name for e in self.expenses)


    def delete_category(self, name, move_to_other=False):
        if name not in self.categories:
            return False, "❌ Category not found."
        
        if move_to_other:
            other_name = "Other"
            if other_name not in self.categories:
                # We still give it a limit for the UI, but we will ignore it in math
                self.categories[other_name] = Category(other_name, "fixed", 1000000.0)
            
            for e in self.expenses:
                if e.category == name:
                    e.category = other_name
            
            del self.categories[name]
            return True, f"✅ Category '{name}' deleted. Expenses moved to '{other_name}'."
        
        else:
            self.expenses = [e for e in self.expenses if e.category != name]
            del self.categories[name]
            return True, f"✅ Category '{name}' and its associated expenses deleted successfully."
        



    def add_expense(self, d, amount, category, description):
        exp = Expense(
            expense_id=self._next_expense_id,
            d=d,
            amount=amount,
            category=category,
            description=description.strip()
        )
        self._next_expense_id += 1
        self.expenses.append(exp)
        return exp

    def delete_expense_by_id(self, expense_id):
        for i, e in enumerate(self.expenses):
            if e.expense_id == expense_id:
                self.expenses.pop(i)
                return True
        return False

    def get_expense_by_id(self, expense_id):
        for e in self.expenses:
            if e.expense_id == expense_id:
                return e
        return None

    def total_expenses(self):
        return sum(e.amount for e in self.expenses)

    def total_by_category(self):
        totals = {}
        for e in self.expenses:
            totals[e.category] = totals.get(e.category, 0.0) + e.amount
        return totals

    def top_and_lowest_category(self):
        totals = self.total_by_category()
        if not totals:
            return None, None
        top = max(totals.items(), key=lambda x: x[1])
        low = min(totals.items(), key=lambda x: x[1])
        return top, low

    def highest_spending_day(self):
        if not self.expenses:
            return None
        daily = {}
        for e in self.expenses:
            daily[e.d] = daily.get(e.d, 0.0) + e.amount
        return max(daily.items(), key=lambda x: x[1])

    def status_summary_counts(self):
        counts = {"✅": 0, "⚠️": 0, "🔶": 0, "🛑": 0}
        if self.budget is None:
            return counts
        totals = self.total_by_category()
        for name, cat in self.categories.items():
            limit = cat.calc_limit(self.budget)
            spent = totals.get(name, 0.0)
            icon = calc_status(spent, limit)
            if icon in counts:
                counts[icon] += 1
        return counts

class BudgetTrackerApp:
    def __init__(self):
        self.months = {}
        self.default_categories = [
            Category("Expenses", "percent", 50.0),
            Category("Entertainment", "percent", 10.0),
            Category("Charity", "percent", 10.0),
            Category("Savings", "percent", 10.0),
            Category("Investment", "percent", 10.0),
            Category("Education", "percent", 10.0),
        ]

    def get_month(self, month_key):
        if month_key not in self.months:
            self.months[month_key] = BudgetMonth(month_key)
        return self.months[month_key]

# =========================
# Streamlit UI Components
# =========================
def init_session():
    if 'app' not in st.session_state:
        st.session_state.app = BudgetTrackerApp()

def main():
    st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="wide")
    apply_custom_width()
    init_session()
    app = st.session_state.app

    st.title("💰 Personal Budget Tracker")

    # =====================
    # SIDEBAR (ONLY HERE)
    # =====================
    with st.sidebar:
        st.header("Navigation")

        today = dt_date.today()
        today_key = month_key_from_date(today)

        # Ensure current month exists
        app.get_month(today_key)

        # Generate months (مثال)
        generated_months = []
        for i in range(12):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            generated_months.append(f"{y}-{m:02d}")

        all_month_keys = set(generated_months + list(app.months.keys()))
        month_options = sorted(list(all_month_keys), reverse=True)

        selected_month_key = st.selectbox(
            "Select Month Context",
            month_options
        )

        if st.button("Logout 🚪"):
            st.session_state.clear()
            st.rerun()

    current_month = app.get_month(selected_month_key)

    # Main UI Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Month Setup", "➕ Add Expense", "📊 Overview", "🛠️ Settings"])



    # ------------------ TAB 1: Setup ------------------
    with tab1:
        st.header(f"Setup for {selected_month_key}")
        if current_month.is_setup():
            st.success("✅ This month is already set up! Head to Settings if you need to make changes.")
        else:
            budget_input = st.number_input("Monthly Budget (SAR)", min_value=1.0, value=8000.0, step=100.0)
            cat_choice = st.radio("Category Setup", ["Use Default Categories", "Create Custom Categories"])
            
            if cat_choice == "Use Default Categories":
                st.write("**Default Categories Preview:**")
                preview_data = [{"Category": c.name, "Type": c.limit_type.title(), "Limit": c.display_limit(), "Est. SAR": c.calc_limit(budget_input)} for c in app.default_categories]
                st.dataframe(pd.DataFrame(preview_data), hide_index=True)
                
                if st.button("Save Month Setup"):
                    current_month.set_budget(budget_input)
                    for c in app.default_categories:
                        current_month.add_category(Category(c.name, c.limit_type, c.value))
                    st.success("✅ Month setup saved!")
                    st.rerun()
            else:



                st.subheader("Define Custom Categories")
                
                # Initialize state variables
                if 'temp_cats' not in st.session_state:
                    st.session_state.temp_cats = []
                if 'custom_limit_type' not in st.session_state:
                    st.session_state.custom_limit_type = None

                # --- PHASE 1: Choose Type ---
                if st.session_state.custom_limit_type is None:
                    st.info("Step 1: Choose how you want to define your limits for this month.")
                    chosen_type = st.radio(
                        "Select Global Limit Type", 
                        ["percent", "fixed"], 
                        format_func=lambda x: "Percentage (%)" if x == "percent" else "Fixed Amount (SAR)",
                        horizontal=True
                    )
                    if st.button("Confirm Type & Start Adding"):
                        st.session_state.custom_limit_type = chosen_type
                        st.rerun()
                


                # --- PHASE 2: Add Categories ---
                else:
                    limit_label = "%" if st.session_state.custom_limit_type == "percent" else "SAR"
                    st.markdown(f"**Current Mode:** Limits defined by **{st.session_state.custom_limit_type.title()}**")

                    # 1. Calculate allocation logic
                    allocated_sar = sum(c.calc_limit(budget_input) for c in st.session_state.temp_cats)
                    
                    if st.session_state.custom_limit_type == "percent":
                        allocated_val = sum(c.value for c in st.session_state.temp_cats)
                        remaining_val = 100.0 - allocated_val
                        target_val = 100.0
                    else:
                        allocated_val = allocated_sar
                        remaining_val = budget_input - allocated_sar
                        target_val = budget_input

                    # Display metrics
                    col_info1, col_info2 = st.columns(2)
                    col_info1.metric(f"Total Allocated ({limit_label})", f"{allocated_val:.2f} / {target_val:.2f}")
                    col_info2.metric(f"Remaining to Allocate", f"{max(0.0, remaining_val):.2f} {limit_label}")

                    # NEW: Validation logic for the "Finalize" button
                    # We use a tiny epsilon (1e-7) to account for floating-point math precision
                    is_fully_allocated = abs(remaining_val) < 1e-7

                    if not is_fully_allocated:
                        st.warning(f"⚠️ You must allocate the full {target_val:g} {limit_label} before saving. You are currently missing {remaining_val:.2f} {limit_label}.")
                    else:
                        st.success(f"✅ Full allocation reached! You may now finalize your budget.")

                    # Form to add a category
                    with st.form("custom_cat_adder", clear_on_submit=True):
                        col1, col2 = st.columns([3, 1])
                        new_name = col1.text_input("Category Name", placeholder="e.g. Groceries")
                        new_val = col2.number_input(f"Value ({limit_label})", min_value=0.0, step=1.0)
                        
                        if st.form_submit_button("➕ Add Category"):
                            if new_val <= 0:
                                st.error(f"❌ Value must be greater than zero.")
                            elif not new_name.strip():
                                st.error("❌ Category name is required.")
                            elif any(c.name.lower() == new_name.strip().lower() for c in st.session_state.temp_cats):
                                st.error("❌ This category is already in your list.")
                            elif new_val > (remaining_val + 1e-9):
                                st.error(f"❌ Limit exceeded! You only have {remaining_val:.2f} {limit_label} remaining.")
                            else:
                                st.session_state.temp_cats.append(
                                    Category(new_name.strip(), st.session_state.custom_limit_type, new_val)
                                )
                                st.rerun()

                    # List management
                    if st.session_state.temp_cats:
                        st.write("**Added Categories:**")
                        temp_df = pd.DataFrame([
                            {"Category": c.name, "Limit": c.display_limit(), "SAR Equivalent": f"{c.calc_limit(budget_input):.2f} SAR"} 
                            for c in st.session_state.temp_cats
                        ])
                        st.dataframe(temp_df, hide_index=True, use_container_width=True)

                        col_btn1, col_btn2 = st.columns(2)
                        
                        if col_btn1.button("🔄 Restart (Change Type)", use_container_width=True):
                            st.session_state.temp_cats = []
                            st.session_state.custom_limit_type = None
                            st.rerun()

                        # UPDATED: Button is now disabled unless is_fully_allocated is True
                        if col_btn2.button(
                            "🚀 Finalize & Save All", 
                            type="secondary", 
                            use_container_width=True, 
                            disabled=not is_fully_allocated,
                            help="Full allocation of the budget is required to enable this button."
                        ):
                            current_month.set_budget(budget_input)
                            for c in st.session_state.temp_cats:
                                current_month.add_category(c)
                            # Cleanup
                            st.session_state.temp_cats = [] 
                            st.session_state.custom_limit_type = None
                            st.success("✅ Custom setup saved!")
                            st.rerun()



    # ------------------ TAB 2: Add Expense ------------------
    with tab2:
        st.header("➕ Add a New Expense")

        if not current_month.is_setup():
            st.warning("⚠️ Please set up this month first from 'Month Setup'.")
        else:
            with st.form("add_expense_form", clear_on_submit=True):

                col1, col2 = st.columns(2)

                with col1:
                    exp_date = st.date_input(
                        "Expense Date",
                        value=dt_date.today()
                    )
                    exp_cat = st.selectbox(
                        "Category",
                        list(current_month.categories.keys())
                    )

                with col2:
                    exp_amount = st.number_input(
                        "Amount (SAR)",
                        min_value=0.01,
                        step=10.0
                    )
                    exp_desc = st.text_input("Description")

                submit_expense = st.form_submit_button("💾 Save Expense")

            if submit_expense:

            
                if exp_amount <= 0:
                    st.error("❌ Amount must be greater than 0")
                else:
            
                    month_id, _ = get_or_create_month(
                        st.session_state["user_id"],
                        selected_month_key
                    )

                
                    add_transaction(
                        month_id=month_id,
                        date=exp_date,
                        amount=exp_amount,
                        category=exp_cat,
                        description=exp_desc
                    )

                    current_month.add_expense(
                        exp_date,
                        exp_amount,
                        exp_cat,
                        exp_desc
                    )

        st.success("✅ Expense saved successfully")
        st.rerun()

    # ------------------ TAB 3: Overview ------------------
    with tab3:
        st.header(f"Expenses Overview ({selected_month_key})")

        if current_month.budget is None:
            st.info("ℹ️ This month is not set up yet. Please complete Month Setup first.")
        else:
            # ===== Metrics =====
            total_spent = current_month.total_expenses()
            remaining = current_month.budget - total_spent

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Budget", f"{current_month.budget:.2f} SAR")
            col2.metric("Total Spent", f"{total_spent:.2f} SAR")
            col3.metric("Remaining", f"{remaining:.2f} SAR", delta=f"{-total_spent:.2f} SAR")

            st.divider()

            # ===== Category Progress =====
            st.subheader("Category Limits & Progress")

            totals = current_month.total_by_category()
            for cat_name, cat in current_month.categories.items():
                spent = totals.get(cat_name, 0.0)
                limit = cat.calc_limit(current_month.budget)
                pct = 0 if limit <= 0 else spent / limit
                icon = calc_status(spent, limit)

                st.write(f"**{cat_name}** {icon} ({spent:.2f} / {limit:.2f} SAR)")

                bar_color = get_progress_color(pct)
                width = min(pct * 100, 100)

                st.markdown(
                    f"""
                    <div style="width:100%; background:#444; border-radius:5px; margin-bottom:20px;">
                        <div style="width:{width}%; height:8px; background:{bar_color}; border-radius:5px;"></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # ===== Expense Table =====
            st.subheader("Recent Expenses")
            if not current_month.expenses:
                st.info("No expenses logged yet.")
            else:
                df = pd.DataFrame([vars(e) for e in current_month.expenses])
                st.dataframe(df, use_container_width=True, hide_index=True)
    # ------------------ TAB 4: Settings ------------------

    with tab4:
        st.header("Settings")
        st.write("TAB 4 START")
        if current_month.budget is None:
            st.info("ℹ️ Please complete Month Setup first.")
            st.stop()
        
        with st.expander("Update Monthly Budget"):
                new_budget = st.number_input("New Budget (SAR)", min_value=1.0, value=current_month.budget, step=100.0)
                if st.button("Update Budget"):
                    current_month.set_budget(new_budget)
                    st.success("✅ Budget updated!")
                    st.rerun()

        with st.expander("Manage Categories"):

                st.subheader("Current Allocation")



                # --- STEP 1: Determine Mode & Global Stats ---
                if current_month.categories:
                    # Filter out 'Other' for allocation calculations
                    active_cats = [c for name, c in current_month.categories.items() if name != "Other"]
                    
                    # Use the first non-Other category to find mode, or default to percent
                    first_cat = active_cats[0] if active_cats else list(current_month.categories.values())[0]
                    active_mode = first_cat.limit_type
                else:
                    active_mode = "percent"

                # Calculate real-time allocation EXCLUDING "Other"
                allocated_sar = sum(c.calc_limit(current_month.budget) for name, c in current_month.categories.items() if name != "Other")
                remaining_sar = current_month.budget - allocated_sar
                
                if active_mode == "percent":
                    allocated_val = sum(c.value for name, c in current_month.categories.items() if name != "Other")
                    remaining_val = 100.0 - allocated_val
                    unit = "%"
                else:
                    allocated_val = allocated_sar
                    remaining_val = remaining_sar
                    unit = "SAR"




                # Metrics Overview
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Total Budget", f"{current_month.budget:,.2f} SAR")
                col_m2.metric(f"Allocated ({unit})", f"{allocated_val:g} {unit}")
                col_m3.metric(f"Remaining ({unit})", f"{max(0.0, remaining_val):g} {unit}")

                st.divider()

                # --- SECTION 1: Add Category Form ---
                st.write(f"**➕ Add New {active_mode.title()} Category**")
                with st.form("settings_add_cat_form", clear_on_submit=True):
                    col1, col2 = st.columns([3, 2])
                    new_name = col1.text_input("Category Name", placeholder="e.g., Health")
                    
                    # Form only accepts values for the active mode
                    new_val = col2.number_input(
                        f"Limit Value ({unit})", 
                        min_value=0.0, 
                        step=1.0 if active_mode == "percent" else 50.0
                    )
                    
                    if st.form_submit_button("Add to Budget"):
                        # Validation Logic
                        if not new_name.strip():
                            st.error("❌ Category name cannot be empty.")
                        elif new_name.strip() in current_month.categories:
                            st.error(f"❌ '{new_name}' already exists.")
                        elif new_val <= 0:
                            st.error(f"❌ Value must be greater than zero.")
                        elif new_val > (remaining_val + 1e-9):
                            st.error(f"❌ Limit exceeded! Only {remaining_val:g} {unit} available.")
                        else:
                            # Add the category using the locked-in mode
                            new_cat = Category(new_name.strip(), active_mode, new_val)
                            current_month.add_category(new_cat)
                            st.success(f"✅ Added {new_name} at {new_val}{unit}")
                            st.rerun()

                st.divider()


                # --- SECTION 2: Edit Existing Category ---
                st.write("**📝 Edit Existing Category**")
                
                if not current_month.categories:
                    st.info("No categories available to edit.")
                else:
                    # Dropdown to select which category to modify
                    cat_to_edit_name = st.selectbox(
                        "Select Category to Edit", 
                        options=list(current_month.categories.keys()),
                        key="edit_cat_selector"
                    )
                    
                    target_cat = current_month.categories[cat_to_edit_name]


                    with st.form("edit_category_form"):
                        col1, col2 = st.columns([3, 2])
                        
                        # Check if the selected category is "Other"
                        is_other = (cat_to_edit_name == "Other")
                        
                        # Pre-fill with current values (disabled if it is the 'Other' category)
                        edit_name = col1.text_input("New Category Name", value=target_cat.name, disabled=is_other)
                        
                        if is_other:
                            # Hide the massive numeric value and disable the input completely
                            col2.text_input(f"New Value ({unit})", value="Hidden", disabled=True)
                            edit_val = target_cat.value # Keep the variable defined for the backend
                        else:
                            edit_val = col2.number_input(
                                f"New Value ({unit})", 
                                min_value=0.01, 
                                value=float(target_cat.value),
                                step=1.0 if active_mode == "percent" else 50.0
                            )
                        
                        if is_other:
                            st.caption("The 'Other' category is managed by the system and cannot be edited.")
                        else:
                            st.caption(f"Current Limit: {target_cat.display_limit()}")
                        
                        # Disable the save button so users don't trigger limit validation errors on "Other"
                        submit_edit = st.form_submit_button("💾 Save Changes", disabled=is_other)

                        
                        if submit_edit:
                            # 1. Calculate the 'other' categories' total to check limits
                            other_cats_total = sum(
                                c.value for name, c in current_month.categories.items() 
                                if name != cat_to_edit_name
                            )
                            
                            # 2. Validation
                            if not edit_name.strip():
                                st.error("❌ Name cannot be empty.")
                            # Check if renaming to an existing name (that isn't itself)
                            elif edit_name.strip() != cat_to_edit_name and edit_name.strip() in current_month.categories:
                                st.error(f"❌ A category named '{edit_name}' already exists.")
                            # Check if the new value exceeds the total budget capacity
                            elif (other_cats_total + edit_val) > (100.0 if active_mode == "percent" else current_month.budget) + 1e-9:
                                available = (100.0 if active_mode == "percent" else current_month.budget) - other_cats_total
                                st.error(f"❌ Limit exceeded! Max available for this category is {available:g} {unit}.")
                            else:
                                # 3. Apply changes
                                # If the name changed, we must replace the dictionary key
                                if edit_name.strip() != cat_to_edit_name:
                                    # Update category name in expense records first
                                    for exp in current_month.expenses:
                                        if exp.category == cat_to_edit_name:
                                            exp.category = edit_name.strip()
                                    
                                    # Update the categories dictionary
                                    del current_month.categories[cat_to_edit_name]
                                
                                # Update values
                                target_cat.name = edit_name.strip()
                                target_cat.value = edit_val
                                current_month.categories[target_cat.name] = target_cat
                                
                                st.success(f"✅ Updated '{target_cat.name}' successfully!")
                                st.rerun()



                # --- SECTION 3: Delete Category ---
                st.write("**🗑️ Remove Category**")
                if not current_month.categories:
                    st.info("No categories available to delete.")
                else:
                    cat_list = list(current_month.categories.keys())
                    del_name = st.selectbox("Select Category to Remove", cat_list)
                    
                    is_deleting_other = (del_name == "Other")
                    
                    # The dynamic key forces Streamlit to forget the "checked" state when switching to "Other"
                    move_expenses = st.checkbox(
                        "Move the current expenses to 'Others'", 
                        value=False,
                        disabled=is_deleting_other,
                        key=f"move_exp_{is_deleting_other}" 
                    )
                    
                    if is_deleting_other:
                        st.warning("⚠️ This will permanently delete the 'Other' category and all its expenses.")
                        st.caption("Cannot move expenses to 'Other' when deleting the 'Other' category itself.")
                    elif move_expenses:
                        st.info("💡 Expenses under this category will be moved to new category called 'Other'.")
                    else:
                        st.warning(f"⚠️ This will permanently delete all expenses in '{del_name}'.")
                    
                    if st.button("Delete Selected Category", type="primary"):
                        safe_move = False if is_deleting_other else move_expenses
                        
                        success, message = current_month.delete_category(del_name, move_to_other=safe_move)
                        if success:
                            st.success(message)
                            st.rerun()

                            


    with st.expander("Manage Expenses (Edit/Delete)"):
                if not current_month.expenses:
                    st.info("No expenses to manage.")
                else:
                    exp_options = {e.expense_id: f"ID {e.expense_id}: {e.d} - {e.category} - {e.amount} SAR" for e in current_month.expenses}
                    selected_exp_id = st.selectbox("Select Expense", list(exp_options.keys()), format_func=lambda x: exp_options[x])
                    
                    target_exp = current_month.get_expense_by_id(selected_exp_id)
                    
                    col_del, col_edit = st.columns(2)
                    with col_del:
                        if st.button("🗑️ Delete Expense", type="primary"):
                            current_month.delete_expense_by_id(selected_exp_id)
                            st.success("✅ Expense deleted.")
                            st.rerun()
                    
                    st.write("---")
                    st.write("**Edit Expense details:**")
                    with st.form("edit_exp_form"):
                        edit_amt = st.number_input("New Amount", min_value=0.01, value=float(target_exp.amount), step=10.0)
                        edit_cat = st.selectbox("New Category", list(current_month.categories.keys()), index=list(current_month.categories.keys()).index(target_exp.category))
                        edit_desc = st.text_input("New Description", value=target_exp.description)
                        
                        if st.form_submit_button("💾 Save Changes"):
                            target_exp.amount = edit_amt
                            target_exp.category = edit_cat
                            target_exp.description = edit_desc
                            current_month.save_expense(target_exp)
                            st.success("✅ Expense updated!")
                            st.rerun()

# =====================
# APP ENTRY POINT
# =====================

if "user_id" in st.session_state:
    main()
else:
    st.info("🔐 Please login to continue")


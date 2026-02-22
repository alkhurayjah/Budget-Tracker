from dataclasses import dataclass
from datetime import date as dt_date, datetime

BACK = -1  # user can type -1 to go back anytime


# =========================
# Helper Functions
# =========================

def line():  
    print("-" * 60)   # Print separator line


def input_choice(prompt, valid):
    while True:                # Validate user choice from allowed options
        choice = input(prompt).strip()
        if choice in valid:
            return choice
        print(f"❌ Invalid choice. Choose from: {', '.join(valid)}")


def input_float_or_back(prompt, min_value=0.0):   # Get float input or return None if user goes back
    while True:
        raw = input(prompt).strip()
        if raw == str(BACK):         # Go back option
            return None
        try:
            val = float(raw)    # Convert to float
            if val >= min_value:
                return val
            print(f"❌ Value must be >= {min_value}")
        except ValueError:
            print("❌ Please enter a valid number (or -1 to back).")


def input_int_or_back(prompt, min_value=0):   # Get integer input or return None if user goes back
    while True:
        raw = input(prompt).strip()
        if raw == str(BACK):     
            return None
        try:
            val = int(raw)    # Convert to integer
            if val >= min_value: # Validate minimum value
                return val
            print(f"❌ Value must be >= {min_value}")
        except ValueError:
            print("❌ Please enter a valid integer (or -1 to back).")


def input_date_or_today_or_back(prompt):  # Get date input, today by default, or return None if back
    while True:
        raw = input(prompt).strip()
        if raw == str(BACK):
            return None
        if raw == "":   # Default to today
            return dt_date.today()   
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD, press Enter for today, or -1 to back.")

# Convert date to "YYYY-MM" format (month key)
def month_key_from_date(d: dt_date) -> str:
    return d.strftime("%Y-%m")

# Format float as money (remove trailing zeros)
def fmt_money(x: float) -> str:
    s = f"{x:.2f}"
    return s.rstrip("0").rstrip(".")

# Determine spending status based on ratio
def calc_status(spent: float, limit: float) -> str:
    if limit <= 0:
        return "ℹ️"  # No limit set
    ratio = spent / limit
    if ratio < 0.50:
        return "✅"
    if ratio < 0.80:
        return "⚠️"
    if ratio < 1.00:
        return "🔶"
    return "🛑"   # Exceeded limit

# Return status message based on icon
def status_message(icon: str) -> str:
    if icon == "✅":
        return "✅ Safe: You are below 50% of this category limit."
    if icon == "⚠️":
        return "⚠️ Alert: You reached 50%+ of this category limit."
    if icon == "🔶":
        return "🔶 Warning: You reached 80%+ of this category limit."
    if icon == "🛑":
        return "🛑 Danger: You exceeded this category limit (100%+)."
    return "ℹ️ Info: No limit is set for this category."


# =========================
# Data Models
# =========================

@dataclass
class Category:
    name: str
    value: float  # if month mode is percent -> percent, else fixed SAR


@dataclass
class Expense:
    expense_id: int
    d: dt_date
    amount: float
    category: str
    description: str


class BudgetMonth:
    def __init__(self, month_key: str):
        self.month_key = month_key
        self.budget: float | None = None

        # Unified mode for ALL categories in this month:
        # "percent" OR "fixed"
        self.limit_mode: str | None = None

        self.categories: dict[str, Category] = {}
        self.expenses: list[Expense] = []
        self._next_expense_id = 1

    def is_setup(self) -> bool:
        return self.budget is not None and self.limit_mode in ("percent", "fixed") and len(self.categories) > 0

    # ---- Budget & Mode ----
    def set_budget(self, new_budget: float):
        self.budget = new_budget

    def set_limit_mode(self, mode: str) -> bool:
        if mode not in ("percent", "fixed"):
            return False
        self.limit_mode = mode
        return True

    # ---- Categories ----
    def add_category(self, cat: Category) -> bool:
        name = cat.name.strip()
        if not name:
            return False
        if name in self.categories:
            return False
        self.categories[name] = cat
        return True

    def update_category_value(self, name: str, value: float) -> bool:
        if name not in self.categories:
            return False
        self.categories[name].value = value
        return True

    def category_has_expenses(self, name: str) -> bool:
        return any(e.category == name for e in self.expenses)

    def _ensure_other_category(self):
        if "Other" not in self.categories:
            # big limit so it won't warn
            big = 10**18
            if self.limit_mode == "percent":
                # percent can't be huge meaningfully; but we can use 1e9% anyway
                big = 10**9
            self.categories["Other"] = Category("Other", big)

    def delete_category(self, name: str, move_to_other: bool):
        if name not in self.categories:
            return False, "❌ Category not found."

        if self.category_has_expenses(name):
            if not move_to_other:
                return False, "ℹ️ Deletion cancelled."

            self._ensure_other_category()
            for e in self.expenses:
                if e.category == name:
                    e.category = "Other"

        del self.categories[name]
        return True, f"✅ Category '{name}' deleted successfully."

    # ---- Limit calculations / display ----
    def calc_limit(self, cat: Category) -> float:
        if self.budget is None or self.limit_mode is None:
            return 0.0
        if self.limit_mode == "percent":
            return self.budget * (cat.value / 100.0)
        return cat.value

    def display_value(self, cat: Category) -> str:
        if self.limit_mode == "percent":
            return f"{fmt_money(cat.value)}%"
        return f"{fmt_money(cat.value)} SAR"

    # ---- Expenses ----
    def add_expense(self, d: dt_date, amount: float, category: str, description: str) -> Expense:
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

    def add_existing_expense(self, exp: Expense):
        self.expenses.append(exp)
        if exp.expense_id >= self._next_expense_id:
            self._next_expense_id = exp.expense_id + 1

    def delete_expense_by_id(self, expense_id: int) -> bool:
        for i, e in enumerate(self.expenses):
            if e.expense_id == expense_id:
                self.expenses.pop(i)
                return True
        return False

    def get_expense_by_id(self, expense_id: int) -> Expense | None:
        for e in self.expenses:
            if e.expense_id == expense_id:
                return e
        return None

    # ---- Calculations ----
    def total_expenses(self) -> float:   # Sum of all expenses 
        return sum(e.amount for e in self.expenses)  
    
    def total_by_category(self) -> dict[str, float]:  # Sum expenses grouped by category
        totals: dict[str, float] = {}
        for e in self.expenses:
            totals[e.category] = totals.get(e.category, 0.0) + e.amount
        return totals

    def top_and_lowest_category(self):  # Get highest and lowest category spending
        totals = self.total_by_category()
        if not totals:
            return None, None
        top = max(totals.items(), key=lambda x: x[1])
        low = min(totals.items(), key=lambda x: x[1])
        return top, low

    def highest_spending_day(self):  # Find day with highest total spending
        if not self.expenses:
            return None
        daily: dict[dt_date, float] = {}
        for e in self.expenses:
            daily[e.d] = daily.get(e.d, 0.0) + e.amount
        return max(daily.items(), key=lambda x: x[1])

    def status_summary_counts(self):   # Count categories by status icons
        counts = {"✅": 0, "⚠️": 0, "🔶": 0, "🛑": 0}
        if self.budget is None or self.limit_mode is None:
            return counts
        totals = self.total_by_category()
        for name, cat in self.categories.items():
            limit = self.calc_limit(cat)
            spent = totals.get(name, 0.0)
            icon = calc_status(spent, limit)
            if icon in counts:
                counts[icon] += 1
        return counts

    def category_progress_line(self, cat_name: str):  # Build a progress line for one category
        if self.budget is None or self.limit_mode is None or cat_name not in self.categories:
            return "", "ℹ️"
        totals = self.total_by_category()
        spent = totals.get(cat_name, 0.0)
        limit = self.calc_limit(self.categories[cat_name])
        icon = calc_status(spent, limit)
        pct = 0.0 if limit <= 0 else (spent / limit) * 100.0
        return f"{cat_name}: {fmt_money(spent)} / {fmt_money(limit)} ({pct:.0f}%) {icon}", icon


# =========================
# App
# =========================

class BudgetTrackerApp:
    def __init__(self):
        self.months: dict[str, BudgetMonth] = {}
        self.current_month_key = month_key_from_date(dt_date.today())

        # Default categories are defined as percentages (we convert to fixed if user chooses fixed mode)
        self.default_categories_percent = [
            ("Expenses", 50.0),
            ("Entertainment", 10.0),
            ("Charity", 10.0),
            ("Savings", 10.0),
            ("Investment", 10.0),
            ("Education", 10.0),
        ]

    def get_month(self, month_key: str) -> BudgetMonth: # Get month object (create if not exists)
        if month_key not in self.months:
            self.months[month_key] = BudgetMonth(month_key)
        return self.months[month_key]

    def current_month(self) -> BudgetMonth:   # Get current month object
        return self.get_month(self.current_month_key)

    def ensure_setup(self, month: BudgetMonth) -> bool:  # Check if month setup is completed
        if not month.is_setup():
            print("⚠️ This month is not set up yet. Please run Month Setup first.")
            return False
        return True

    # =========================
    # Run
    # =========================

    def run(self):
        while True:
            self.print_main_menu()
            choice = input_choice("Choose (1-6): ", ["1", "2", "3", "4", "5", "6"])
            if choice == "1":
                self.menu_month_setup()
            elif choice == "2":
                self.menu_add_expense()
            elif choice == "3":
                self.menu_expenses_overview()
            elif choice == "4":
                self.menu_settings()
            elif choice == "5":
                self.menu_switch_month()
            elif choice == "6":
                print("✅ Exiting... Bye!")
                break

    # =========================
    # Menus
    # =========================

    def print_main_menu(self):
        print("\n===========================")
        print(f"   Main Menu ({self.current_month_key})")
        print("===========================")
        print("1) Month Setup")
        print("2) Add Expense")
        print("3) Expenses Overview")
        print("4) Settings")
        print("5) Switch Month")
        print("6) Exit")

    # -------- Month Setup --------

    def preview_default_categories(self, budget: float, mode: str):
        print("\n✅ Default Categories Preview:")
        line()
        for i, (name, pct) in enumerate(self.default_categories_percent, start=1):
            if mode == "percent":
                value_str = f"{fmt_money(pct)}%"
                limit = budget * (pct / 100.0)
                kind = "Percentage"
            else:
                fixed_val = budget * (pct / 100.0)
                value_str = f"{fmt_money(fixed_val)} SAR"
                limit = fixed_val
                kind = "Fixed"
            print(f"{i}) {name:<14} | {kind:<10} | {value_str:<14} | Limit ≈ {fmt_money(limit)} SAR")
        line()

    def apply_default_categories(self, month: BudgetMonth):
        # month.limit_mode is already set
        if month.budget is None or month.limit_mode is None:
            return
        month.categories.clear()

        for name, pct in self.default_categories_percent:
            if month.limit_mode == "percent":
                month.add_category(Category(name, pct))
            else:
                month.add_category(Category(name, month.budget * (pct / 100.0)))

    def copy_setup_from_month(self, source: BudgetMonth, target: BudgetMonth):
        if source.budget is not None:      # Copy budget and mode
            target.budget = source.budget
        target.limit_mode = source.limit_mode
        target.categories.clear()
        for c in source.categories.values():
            target.add_category(Category(c.name, c.value))

    def menu_month_setup(self): 
        month = self.current_month()
        while True:
            print("\n--- Month Setup ---")
            print(f"Current Month: {self.current_month_key}")
            print(f"Type {BACK} to go back anytime.\n")

            budget = input_float_or_back("Enter monthly budget (SAR): ", min_value=1.0)
            if budget is None:
                return

            month.set_budget(budget)  # Save budget

            print("\nChoose ONE unified limit mode for ALL categories in this month:")
            print("1) Percentage (all categories are % of budget)")
            print("2) Fixed (all categories are fixed SAR amounts)")
            print(f"{BACK}) Back")
            mode_choice = input_choice("Choose (1-2 or -1): ", ["1", "2", str(BACK)])
            if mode_choice == str(BACK):
                return

            mode = "percent" if mode_choice == "1" else "fixed"
            month.set_limit_mode(mode)

            self.preview_default_categories(budget, mode)

            print("Do you want to use default categories?")
            print("1) Yes (Default)")
            print("2) No, I will create my own")
            print(f"{BACK}) Back")
            cat_choice = input_choice("Choose (1-2 or -1): ", ["1", "2", str(BACK)])
            if cat_choice == str(BACK):
                return

            month.categories.clear()

            if cat_choice == "1":
                self.apply_default_categories(month)
                print("✅ Default categories added.")
                print(f"✅ Month setup saved for {self.current_month_key}.")
                return
            else:
                ok = self.create_custom_categories(month)
                if ok:
                    print("✅ Custom categories saved.")
                    print(f"✅ Month setup saved for {self.current_month_key}.")
                    return

    def create_custom_categories(self, month: BudgetMonth) -> bool:  # Create user-defined categories
        if month.limit_mode is None:
            print("❌ Month limit mode is not set. Run Month Setup again.")
            return False
        if month.budget is None:
            print("❌ Month budget not set. Run Month Setup again.")
            return False

        # Target total depends on mode
        target_total = 100.0 if month.limit_mode == "percent" else month.budget

        count = input_int_or_back("How many categories do you want to create? (type -1 to back): ", min_value=1)
        if count is None:
            print("ℹ️ Custom setup cancelled.")
            return False

        running_sum = 0.0

        for idx in range(1, count + 1):
            print(f"\nCategory #{idx} (type -1 to back)")
            name = input("Enter category name: ").strip()
            if name == str(BACK):
                print("ℹ️ Custom setup cancelled.")
                return False

            while not name or name in month.categories:
                if not name:
                    print("❌ Name cannot be empty.")
                else:
                    print("❌ Category name already exists.")
                name = input("Enter category name: ").strip()
                if name == str(BACK):
                    print("ℹ️ Custom setup cancelled.")
                    return False

            remaining = max(0.0, target_total - running_sum)

            # If user already used up the total, force remaining categories to be 0
            if remaining <= 1e-9:
                print("ℹ️ You already allocated the full total. This category will be set to 0.")
                value = 0.0
                month.add_category(Category(name, value))
                continue

            if month.limit_mode == "percent":
                # percent must not exceed remaining and total <= 100
                while True:
                    value = input_float_or_back(
                        f"Enter percentage (0-{remaining:.2f}) (type -1 to back): ",
                        min_value=0.0
                    )
                    if value is None:
                        print("ℹ️ Custom setup cancelled.")
                        return False
                    if value <= remaining + 1e-9:
                        break
                    print(f"❌ You exceeded the remaining percentage. Remaining = {remaining:.2f}%")

                month.add_category(Category(name, value))

            else:
                # fixed SAR must not exceed remaining and total <= budget
                while True:
                    value = input_float_or_back(
                        f"Enter fixed amount (SAR) (0-{remaining:.2f}) (type -1 to back): ",
                        min_value=0.0
                    )
                    if value is None:
                        print("ℹ️ Custom setup cancelled.")
                        return False
                    if value <= remaining + 1e-9:
                        break
                    print(f"❌ You exceeded the remaining amount. Remaining = {fmt_money(remaining)} SAR")

                month.add_category(Category(name, value))

            running_sum += value

        # After all categories: if leftover exists, offer to add it to one of created categories
        leftover = target_total - running_sum
        if leftover > 1e-9 and month.categories:
            if month.limit_mode == "percent":
                print(f"\nℹ️ You still have {leftover:.2f}% unallocated.")
                unit = "%"
            else:
                print(f"\nℹ️ You still have {fmt_money(leftover)} SAR unallocated.")
                unit = "SAR"

            print("Do you want to add the remaining amount to one of your categories?")
            print("1) Yes")
            print("2) No")
            ch = input_choice("Choose (1-2): ", ["1", "2"])

            if ch == "1":
                cat_name = self.pick_category_numbered(month, title="Choose category number to add the remaining to (or -1 to back): ")
                if cat_name is not None:
                    month.categories[cat_name].value += leftover
                    print(f"✅ Added remaining {fmt_money(leftover)} {unit} to '{cat_name}'.")
                    running_sum += leftover

        print("✅ Custom categories created successfully.")
        return True

    # -------- Switch Month --------

    def menu_switch_month(self):
        while True:
            print("\n--- Switch Month ---")
            print(f"Current: {self.current_month_key}")
            print("1) View months list")
            print("2) Switch to existing month")
            print("3) Create new month")
            print(f"{BACK}) Back")
            choice = input_choice("Choose (1-3 or -1): ", ["1", "2", "3", str(BACK)])
            if choice == str(BACK):
                return

            if choice == "1":
                self.view_months_list()  # Show list
            elif choice == "2":
                self.switch_to_existing_month()  # Switch month
            else:
                self.create_new_month()   # Create new month

    def view_months_list(self):
        print("\n--- Months List ---")
        if not self.months:
            print("ℹ️ No months yet. Add a setup or expense first.")
            return
        for i, mk in enumerate(sorted(self.months.keys()), start=1):
            tag = " (current)" if mk == self.current_month_key else ""  # Mark current
            month = self.months[mk]
            setup = "✅ setup" if month.is_setup() else "⚠️ not setup"   # Setup status
            print(f"{i}) {mk}{tag} | {setup} | Expenses: {len(month.expenses)}")
        line()

    def switch_to_existing_month(self):
        if not self.months:
            print("ℹ️ No months available.")
            return
        keys = sorted(self.months.keys())
        print("\nChoose month:")
        for i, mk in enumerate(keys, start=1):
            print(f"{i}) {mk}")
        print(f"{BACK}) Back")

        idx = input_int_or_back("Choose month number (or -1): ", min_value=1)
        if idx is None:
            return
        if not (1 <= idx <= len(keys)):  # Validate index
            print("❌ Invalid month number.")
            return

        self.current_month_key = keys[idx - 1]
        print(f"✅ Switched to {self.current_month_key}")

    def create_new_month(self):
        print("\nCreate month by date:")
        d = input_date_or_today_or_back("Enter any date within the month (YYYY-MM-DD) or Enter for today: ")
        if d is None:
            return
        mk = month_key_from_date(d)

        if mk in self.months:
            print("ℹ️ Month already exists. Switching to it.")
            self.current_month_key = mk
            return

        new_month = self.get_month(mk)
        print("Copy setup from current month?")
        print("1) Yes (copy budget + mode + categories)")
        print("2) No")
        ch = input_choice("Choose (1-2): ", ["1", "2"])
        if ch == "1":
            self.copy_setup_from_month(self.current_month(), new_month)  # Copy setup
            print("✅ Setup copied.")

        self.current_month_key = mk  # Set as current
        print(f"✅ Created & switched to {mk}")  

    # -------- Add Expense --------
      
    def pick_category_numbered(self, month: BudgetMonth, title: str): # Pick category using numbered list
        categories = list(month.categories.keys())
        if not categories:
            print("❌ No categories. Run Month Setup.")
            return None

        print("\nChoose category:")
        for i, c in enumerate(categories, start=1):
            print(f"{i}) {c}")
        print(f"{BACK}) Back")

        while True:
            idx = input_int_or_back(title, min_value=1)
            if idx is None:
                return None
            if 1 <= idx <= len(categories):  # Valid selection
                return categories[idx - 1]
            print("❌ Invalid category number.")

    def menu_add_expense(self):  # Add new expense flow
        while True:
            print("\n--- Add Expense ---")
            print(f"Type {BACK} to go back anytime.\n")

            d = input_date_or_today_or_back("Enter date (YYYY-MM-DD) or press Enter for today: ")
            if d is None:
                return

            mk = month_key_from_date(d)
            month = self.get_month(mk)  # Get month object

            if not self.ensure_setup(month):
                print(f"ℹ️ This expense belongs to month {mk}")
                print("✅ Please run Month Setup for that month first.")
                return

            amount = input_float_or_back("Enter amount (SAR): ", min_value=0.01)
            if amount is None:
                return

            if month.budget is not None:  # Block if monthly budget will be exceeded
                current_total = month.total_expenses()
                if current_total + amount > month.budget + 1e-9:
                    print("\n🛑 Monthly budget exceeded!")
                    print(f"Monthly Budget: {fmt_money(month.budget)} SAR")
                    print(f"Current Expenses: {fmt_money(current_total)} SAR")
                    print(f"Attempted Amount: {fmt_money(amount)} SAR")
                    print(f"New Total Would Be: {fmt_money(current_total + amount)} SAR")
                    print("➡️ To continue, please update your monthly budget in Settings.")
                    return

            category = self.pick_category_numbered(month, title="Choose category number (or -1 to back): ")
            if category is None:
                print("ℹ️ Expense entry cancelled.")
                return

            desc = input("Enter description (or -1 to back): ").strip()
            if desc == str(BACK):
                print("ℹ️ Expense entry cancelled.")
                return

            exp = month.add_expense(d=d, amount=amount, category=category, description=desc)

            print("\n✅ Expense saved successfully.")
            print(f"Expense ID: {exp.expense_id}")
            if mk != self.current_month_key:
                print(f"ℹ️ This expense belongs to month {mk}")
                print(f"✅ Saved under {mk}")

            progress_line, icon = month.category_progress_line(category)
            print(progress_line)
            print(status_message(icon))
            return

    # -------- Expenses Overview --------

    def menu_expenses_overview(self):  # Expenses overview menu
        month = self.current_month()
        if not self.ensure_setup(month):
            return

        while True:
            print("\n--- Expenses Overview ---")
            print("1) View All Expenses (Current Month)")
            print("2) View Statistics Summary")
            print("3) Filter by Category")
            print(f"{BACK}) Back")
            choice = input_choice("Choose (1-3 or -1): ", ["1", "2", "3", str(BACK)])

            if choice == "1":
                self.view_all_expenses(month)  # Show all
            elif choice == "2":
                self.view_statistics(month)  # Show stats
            elif choice == "3":
                self.filter_by_category(month)  # Filter by category
            else:
                return

    def view_all_expenses(self, month: BudgetMonth):
        print("\nID | Date       | Amount | Category       | Description")
        line()
        if not month.expenses:
            print("ℹ️ No expenses yet.")
            return

        for e in sorted(month.expenses, key=lambda x: (x.d, x.expense_id)):
            print(f"{e.expense_id:<2} | {e.d} | {fmt_money(e.amount):<6} | {e.category:<13} | {e.description}")

        line()
        print(f"Total Expenses: {fmt_money(month.total_expenses())} SAR")

    def view_statistics(self, month: BudgetMonth):
        if month.budget is None:
            print("❌ Month budget not set.")
            return

        total = month.total_expenses()   # Total spent
        remaining = month.budget - total  # Remaining budget

        top, low = month.top_and_lowest_category()  # Top/lowest categories
        best_day = month.highest_spending_day()  # Highest spending day
        counts = month.status_summary_counts()  # Status counts

        mode_name = "Percentage" if month.limit_mode == "percent" else "Fixed"

        print("\n--- Statistics Summary ---")
        print(f"Budget: {fmt_money(month.budget)} SAR")
        print(f"Limit Mode: {mode_name} (Unified for all categories)")
        print(f"Total Expenses: {fmt_money(total)} SAR")
        print(f"Remaining: {fmt_money(remaining)} SAR")

        if top:  # Top category
            print(f"Top Category: {top[0]} ({fmt_money(top[1])} SAR)")
        else:
            print("Top Category: ℹ️ No spending yet.")

        if low:  # Lowest category
            print(f"Lowest Category: {low[0]} ({fmt_money(low[1])} SAR)")
        else:
            print("Lowest Category: ℹ️ No spending yet.")

        if best_day:  # Highest spending day
            print(f"Highest Spending Day: {best_day[0]} ({fmt_money(best_day[1])} SAR)")
        else:
            print("Highest Spending Day: ℹ️ No spending yet.")

        print("\nStatus Summary:")  # Status summary
        print(f"✅ Safe (<50%): {counts['✅']}")
        print(f"⚠️ Alert (50%-79%): {counts['⚠️']}")
        print(f"🔶 Warning (80%-99%): {counts['🔶']}")
        print(f"🛑 Danger (>=100%): {counts['🛑']}")

        print("\nPer-Category Progress:")
        for cat_name in month.categories.keys():
            progress_line, _ = month.category_progress_line(cat_name)
            print(" - " + progress_line)

    def filter_by_category(self, month: BudgetMonth):
        cat = self.pick_category_numbered(month, title="Choose category number to filter (or -1 to back): ")
        if cat is None:
            return

        filtered = [e for e in month.expenses if e.category == cat]  # Filter expenses

        print(f"\n--- Expenses for {cat} ---")
        if not filtered:
            print("ℹ️ No expenses in this category yet.")
            progress_line, _ = month.category_progress_line(cat)
            print(" - " + progress_line)
            return

        print("ID | Date       | Amount | Description")
        line()
        for e in sorted(filtered, key=lambda x: (x.d, x.expense_id)):
            print(f"{e.expense_id:<2} | {e.d} | {fmt_money(e.amount):<6} | {e.description}")

        line()
        total = sum(e.amount for e in filtered)
        print(f"Category Total: {fmt_money(total)} SAR")
        progress_line, icon = month.category_progress_line(cat)
        print(progress_line)
        print(status_message(icon))

    # -------- Settings --------

    def menu_settings(self):
        month = self.current_month()
        if not self.ensure_setup(month):  # Ensure month is ready
            return

        while True:
            print(f"\n--- Settings (Current Month: {self.current_month_key}) ---")
            print("1) Update Monthly Budget")
            print("2) Manage Categories (Add / Update / Delete)")
            print("3) Manage Expenses (Edit / Delete)")
            print(f"{BACK}) Back")
            choice = input_choice("Choose (1-3 or -1): ", ["1", "2", "3", str(BACK)])

            if choice == "1":
                self.update_monthly_budget(month)  # Update budget
            elif choice == "2":
                self.manage_categories(month)  # Categories menu
            elif choice == "3":
                self.manage_expenses(month)  # Expenses menu
            else:
                return  # Back

    def update_monthly_budget(self, month: BudgetMonth):  # Update month budget
        print("\n--- Update Monthly Budget ---")
        current = month.budget if month.budget is not None else 0.0
        print(f"Current budget: {fmt_money(current)} SAR")
        new_budget = input_float_or_back("Enter new budget (SAR) or -1 to back: ", min_value=1.0)
        if new_budget is None:
            return

        month.set_budget(new_budget)  # Save new budget
        print(f"✅ Budget updated for {month.month_key}.")
        if month.limit_mode == "percent":
            print("ℹ️ Percentage-based limits updated automatically.")
        else:
            print("ℹ️ Fixed limits remain the same amounts.")

        if month.total_expenses() > new_budget:  # Warn if expenses exceed new budget
            print("⚠️ Warning: Expenses exceed new budget!")

    def manage_categories(self, month: BudgetMonth):  # Categories management menu
        while True:
            print("\n--- Manage Categories ---")
            print("1) View Categories")
            print("2) Add Category")
            print("3) Update Category Value")
            print("4) Delete Category")
            print(f"{BACK}) Back")
            choice = input_choice("Choose (1-4 or -1): ", ["1", "2", "3", "4", str(BACK)])

            if choice == "1":
                self.view_categories(month)
            elif choice == "2":
                self.add_category_menu(month)
            elif choice == "3":
                self.update_category_menu_numbered(month)
            elif choice == "4":
                self.delete_category_menu_numbered(month)
            else:
                return

    def view_categories(self, month: BudgetMonth):  # View categories with spending/limits
        print("\n--- Categories ---")
        if month.budget is None or month.limit_mode is None:
            print("❌ Month is not properly set up.")
            return
        if not month.categories:
            print("ℹ️ No categories.")
            return

        totals = month.total_by_category()   # Spent per category
        mode_name = "Percentage" if month.limit_mode == "percent" else "Fixed"
        print(f"Unified Mode: {mode_name}")
        line()
        for i, (name, cat) in enumerate(month.categories.items(), start=1):
            limit = month.calc_limit(cat)
            spent = totals.get(name, 0.0)
            icon = calc_status(spent, limit)
            pct = 0.0 if limit <= 0 else (spent / limit) * 100.0
            print(f"{i}) {name:<14} | {month.display_value(cat):<14} | "
                  f"{fmt_money(spent)} / {fmt_money(limit)} ({pct:.0f}%) {icon}")
        line()

    def add_category_menu(self, month: BudgetMonth):  # Add a new category
        print("\n--- Add Category ---")
        if month.limit_mode is None:
            print("❌ Month limit mode not set. Run Month Setup.")
            return

        name = input("Enter category name (or -1 to back): ").strip()
        if name == str(BACK):
            return
        while not name or name in month.categories:  # Validate name (not empty / not duplicate)
            if not name:
                print("❌ Name cannot be empty.")
            else:
                print("❌ Category already exists.")
            name = input("Enter category name (or -1 to back): ").strip()
            if name == str(BACK):
                return

        if month.limit_mode == "percent":
            value = input_float_or_back("Enter percentage (0-100): ", min_value=0.0)
            if value is None:
                return
            while value > 100.0:  # Cap at 100%
                print("❌ Percentage cannot exceed 100.")
                value = input_float_or_back("Enter percentage (0-100): ", min_value=0.0)
                if value is None:
                    return
            ok = month.add_category(Category(name, value)) # Save %
        else:
            value = input_float_or_back("Enter fixed amount (SAR): ", min_value=0.0)
            if value is None:
                return
            ok = month.add_category(Category(name, value)) # Save SAR

        print("✅ Category added successfully." if ok else "❌ Failed to add category.")

    def update_category_menu_numbered(self, month: BudgetMonth): # Update category value (numbered selection)
        print("\n--- Update Category Value ---")
        cat_name = self.pick_category_numbered(month, title="Choose category number to update (or -1 to back): ")
        if cat_name is None:  # Back
            return

        if month.limit_mode == "percent":
            value = input_float_or_back("Enter new percentage (0-100): ", min_value=0.0)
            if value is None: # Back
                return
            while value > 100.0:
                print("❌ Percentage cannot exceed 100.")
                value = input_float_or_back("Enter new percentage (0-100): ", min_value=0.0)
                if value is None:
                    return
        else:
            value = input_float_or_back("Enter new fixed amount (SAR): ", min_value=0.0)
            if value is None:
                return

        month.update_category_value(cat_name, value)
        print(f"✅ Category '{cat_name}' updated successfully.")

    def delete_category_menu_numbered(self, month: BudgetMonth): # Delete category (handle existing expenses)
        print("\n--- Delete Category ---")
        cat = self.pick_category_numbered(month, title="Choose category number to delete (or -1 to back): ")
        if cat is None:
            return

        if month.category_has_expenses(cat): # Category not empty
            print("⚠️ This category has expenses.")
            print('1) Move expenses to "Other" and delete')
            print("2) Cancel")
            ch = input_choice("Choose (1-2): ", ["1", "2"])
            if ch == "2":
                print("ℹ️ Deletion cancelled.")
                return
            ok, msg = month.delete_category(cat, move_to_other=True)
            print(msg)
        else:
            ok, msg = month.delete_category(cat, move_to_other=True)
            print(msg)

    # -------- Manage Expenses (Edit/Delete/Update Date) --------

    def print_expenses_table(self, month: BudgetMonth): # Print expenses in table format
        print("ID | Date       | Amount | Category       | Description")
        line()
        for e in sorted(month.expenses, key=lambda x: (x.d, x.expense_id)):
            print(f"{e.expense_id:<2} | {e.d} | {fmt_money(e.amount):<6} | {e.category:<13} | {e.description}")
        line()

    def manage_expenses(self, month: BudgetMonth):  # Manage expenses (edit/delete)
        while True:
            print("\n--- Manage Expenses ---")
            print("1) Edit Expense (Amount / Category / Description / Date)")
            print("2) Delete Expense")
            print(f"{BACK}) Back")
            choice = input_choice("Choose (1-2 or -1): ", ["1", "2", str(BACK)])
            if choice == str(BACK):
                return

            if not month.expenses: # No expenses
                print("ℹ️ No expenses yet.")
                return

            self.print_expenses_table(month)

            expense_id = input_int_or_back("Enter Expense ID (or -1 to back): ", min_value=1)
            if expense_id is None:
                continue

            exp = month.get_expense_by_id(expense_id) # Find expense
            if exp is None:
                print("❌ Expense ID not found.")
                continue

            if choice == "2": # Delete expense
                deleted = month.delete_expense_by_id(expense_id)
                print(f"✅ Expense ID {expense_id} deleted successfully." if deleted else "❌ Expense ID not found.")
                continue

            # Edit flow
            while True:
                print(f"\n--- Edit Expense (ID: {exp.expense_id}) ---")
                print(f"Current: {exp.d} | {fmt_money(exp.amount)} SAR | {exp.category} | {exp.description}")
                print("1) Update Amount")
                print("2) Update Category")
                print("3) Update Description")
                print("4) Update Date")
                print(f"{BACK}) Back")
                sub = input_choice("Choose (1-4 or -1): ", ["1", "2", "3", "4", str(BACK)])
                if sub == str(BACK): # Exit edit menu
                    break

                if sub == "1":
                    new_amount = input_float_or_back("Enter new amount (SAR) or -1 to back: ", min_value=0.01)
                    if new_amount is None: # Cancel
                        continue

                    if month.budget is not None:
                        current_total = month.total_expenses()
                        would_be = (current_total - exp.amount) + new_amount
                        if would_be > month.budget + 1e-9:
                            print("\n🛑 Monthly budget exceeded!")
                            print(f"Monthly Budget: {fmt_money(month.budget)} SAR")
                            print(f"Current Expenses: {fmt_money(current_total)} SAR")
                            print(f"New Total Would Be: {fmt_money(would_be)} SAR")
                            print("➡️ To continue, please update your monthly budget in Settings.")
                            continue

                    exp.amount = new_amount  # Update amount
                    print("✅ Amount updated successfully.")
                    progress_line, icon = month.category_progress_line(exp.category)
                    print(progress_line)
                    print(status_message(icon))

                elif sub == "2":
                    old_cat = exp.category
                    new_cat = self.pick_category_numbered(month, title="Choose new category number (or -1 to back): ")
                    if new_cat is None:
                        print("ℹ️ Expense edit cancelled.")
                        continue

                    exp.category = new_cat # Update category
                    print("✅ Category updated successfully.")
                    # Show progress for old/new categories
                    old_line, old_icon = month.category_progress_line(old_cat)
                    new_line, new_icon = month.category_progress_line(new_cat)
                    if old_line:
                        print(old_line)
                        print(status_message(old_icon))
                    if new_line:
                        print(new_line)
                        print(status_message(new_icon))

                elif sub == "3":
                    new_desc = input("Enter new description (or -1 to back): ").strip()
                    if new_desc == str(BACK):  # Cancel
                        print("ℹ️ Expense edit cancelled.")
                        continue
                    exp.description = new_desc # Update description
                    print("✅ Description updated successfully.")

                else:
                    new_date = input_date_or_today_or_back("Enter new date (YYYY-MM-DD) or Enter for today: ")
                    if new_date is None:
                        print("ℹ️ Expense edit cancelled.")
                        continue

                    old_mk = month_key_from_date(exp.d)  # Old month key
                    new_mk = month_key_from_date(new_date)  # New month key

                    old_day = exp.d.day # Save old day
                    exp.d = new_date  # Apply new date

                    if new_mk == old_mk:  # Same month
                        print("✅ Date updated (same month).")
                        continue

                    target_month = self.get_month(new_mk) # Target month

                    if not target_month.is_setup():
                        print(f"⚠️ Target month {new_mk} is not set up. Please run Month Setup for it first.")
                        # revert date safely (same day where possible)
                        try:
                            exp.d = datetime.strptime(old_mk + "-01", "%Y-%m-%d").date().replace(day=old_day)
                        except ValueError:
                            exp.d = datetime.strptime(old_mk + "-01", "%Y-%m-%d").date()
                        print("ℹ️ Date change reverted.")
                        continue

                    if exp.category not in target_month.categories: # Category missing
                        target_month._ensure_other_category()
                        exp.category = "Other"
                        print("ℹ️ Category not found in target month. Moved to 'Other'.")

                    month.delete_expense_by_id(expense_id) # Remove from old month
                    target_month.add_existing_expense(exp) # Add to new month

                    print(f"✅ Date updated and expense moved to month {new_mk}.")
                    break

# Reflection:
# The most challenging part of this project was implementing input validation and making sure the system is
# prepared for all possible user scenarios We had to ensure users cannot exceed their total budget,
# over-allocate category limits (whether percentage or fixed), enter zero or negative values,
# or create conflicts between months.Making the system logically consistent and safe against incorrect inputs
# required careful planning and testing.


# The concept we enjoyed the most was applying Object-Oriented Programming. Designing and connecting
# classes like Category, Expense, BudgetMonth, and the main application class helped us structure
# the system in a clean and scalable way. It was satisfying to see how all components worked together
#  to form a complete financial management system.


# If we had more time, we would focus on adding advanced charts and data visualization. 
# For example, we would implement spending trend line charts, category distribution pie charts,
# and monthly comparison bar charts. This would make the system more analytical and provide clearer insights
# into users’ financial behavior instead of only displaying numerical summaries.






# =========================
# Main
# =========================

def main():
    app = BudgetTrackerApp()  # Create app instance
    app.run() # Start application


if __name__ == "__main__":  # Run only if executed directly
    main()
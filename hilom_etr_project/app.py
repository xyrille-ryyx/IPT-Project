from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from functools import wraps

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "teen_mental_health.csv"
CHART_DIR = BASE_DIR / "static" / "charts"

app = Flask(__name__)
app.secret_key = "hilom123"

# MySQL Configuration
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "mental_health_dashboard"

mysql = MySQL(app)


class DataProcessor:
    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)
        self.df = None

    def load_data(self):
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.csv_path}")

        self.df = pd.read_csv(self.csv_path)
        return self.df

    def preprocess(self):
        if self.df is None:
            self.load_data()

        self.df = self.df.drop_duplicates()

        numeric_cols = self.df.select_dtypes(include="number").columns
        text_cols = self.df.select_dtypes(exclude="number").columns

        for col in numeric_cols:
            self.df[col] = self.df[col].fillna(self.df[col].median())

        for col in text_cols:
            mode_value = self.df[col].mode()
            fill_value = mode_value.iloc[0] if not mode_value.empty else "Unknown"
            self.df[col] = self.df[col].fillna(fill_value)

        return self.df


class MentalHealthAnalytics:
    def __init__(self, dataframe):
        self.data = dataframe.copy()

    def total_records(self):
        return len(self.data)

    def average_sleep(self):
        return round(self.data["sleep_hours"].mean(), 2)

    def average_social_media(self):
        return round(self.data["daily_social_media_hours"].mean(), 2)

    def average_stress(self):
        return round(self.data["stress_level"].mean(), 2)

    def depression_percentage(self):
        return round((self.data["depression_label"].mean()) * 100, 2)

    def platform_usage_counts(self):
        return self.data["platform_usage"].value_counts()

    def high_risk_students(self):
        risk = self.data[
            (self.data["stress_level"] >= 8) |
            (self.data["anxiety_level"] >= 8) |
            (self.data["addiction_level"] >= 8)
        ]
        return risk.head(10)

    def summary_table(self):
        cols = [
            "age",
            "daily_social_media_hours",
            "sleep_hours",
            "screen_time_before_sleep",
            "academic_performance",
            "physical_activity",
            "stress_level",
            "anxiety_level",
            "addiction_level"
        ]

        return self.data[cols].describe().round(2)


from pathlib import Path
import matplotlib.pyplot as plt

class ChartGenerator:
    def __init__(self, dataframe, output_dir):
        self.data = dataframe
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save(self, filename):
        path = self.output_dir / filename
        plt.tight_layout()
        plt.savefig(path, dpi=120, bbox_inches="tight")
        plt.close()
        return f"charts/{filename}"

    def platform_pie(self):
        values = self.data["platform_usage"].value_counts()

        plt.figure(figsize=(6, 4))
        plt.pie(
            values.values,
            labels=values.index,
            autopct="%1.1f%%",
            startangle=90
        )
        plt.title("Platform Usage Distribution")
        plt.legend(values.index, title="Platform")
        return self._save("platform_pie.png")

    def stress_histogram(self):
        plt.figure(figsize=(6, 4))
        plt.hist(self.data["stress_level"], bins=10, edgecolor="black", label="Stress Level")
        plt.title("Stress Level Distribution")
        plt.xlabel("Stress Level")
        plt.ylabel("Number of Students")
        plt.legend()
        return self._save("stress_histogram.png")

    def stress_by_age_line(self):
        stress_age = self.data.groupby("age")["stress_level"].mean()

        plt.figure(figsize=(6, 4))
        plt.plot(stress_age.index, stress_age.values, marker="o", label="Average Stress")
        plt.title("Average Stress Level by Age")
        plt.xlabel("Age")
        plt.ylabel("Average Stress Level")
        plt.grid(True)
        plt.legend()
        return self._save("stress_by_age.png")

    def sleep_vs_social_scatter(self):
        plt.figure(figsize=(6, 4))
        plt.scatter(
            self.data["daily_social_media_hours"],
            self.data["sleep_hours"],
            alpha=0.6,
            label="Student Data"
        )
        plt.title("Social Media Hours vs Sleep Hours")
        plt.xlabel("Daily Social Media Hours")
        plt.ylabel("Sleep Hours")
        plt.legend()
        return self._save("sleep_vs_social.png")

    def depression_by_platform_bar(self):
        values = self.data.groupby("platform_usage")["depression_label"].sum()
        values = values.sort_values(ascending=False)

        plt.figure(figsize=(6, 4))
        plt.bar(values.index, values.values, label="Depression Cases")
        plt.title("Depression Cases by Platform")
        plt.xlabel("Platform")
        plt.ylabel("Number of Depression Labels")
        plt.xticks(rotation=25)
        plt.legend()
        return self._save("depression_by_platform.png")

    def generate_all(self):
        return {
            "platform_pie": self.platform_pie(),
            "stress_histogram": self.stress_histogram(),
            "stress_by_age": self.stress_by_age_line(),
            "sleep_vs_social": self.sleep_vs_social_scatter(),
            "depression_by_platform": self.depression_by_platform_bar()
        }


def get_clean_data():
    processor = DataProcessor(DATA_PATH)
    processor.load_data()
    return processor.preprocess()


def apply_dashboard_filters(df, filters):
    filtered = df.copy()

    gender = filters.get("gender", "").strip()
    platform = filters.get("platform", "").strip()
    social_level = filters.get("social_level", "").strip()
    depression = filters.get("depression", "").strip()

    min_age = filters.get("min_age", "").strip()
    max_age = filters.get("max_age", "").strip()
    min_stress = filters.get("min_stress", "").strip()
    max_stress = filters.get("max_stress", "").strip()

    if gender:
        filtered = filtered[filtered["gender"] == gender]

    if platform:
        filtered = filtered[filtered["platform_usage"] == platform]

    if social_level:
        filtered = filtered[filtered["social_interaction_level"] == social_level]

    if depression in ["0", "1"]:
        filtered = filtered[filtered["depression_label"] == int(depression)]

    try:
        if min_age:
            filtered = filtered[filtered["age"] >= int(min_age)]

        if max_age:
            filtered = filtered[filtered["age"] <= int(max_age)]

        if min_stress:
            filtered = filtered[filtered["stress_level"] >= int(min_stress)]

        if max_stress:
            filtered = filtered[filtered["stress_level"] <= int(max_stress)]

    except ValueError:
        flash("Invalid filter value.", "danger")

    return filtered


def log_action(username, action):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO user_actions (username, action) VALUES (%s, %s)",
            (username, action)
        )
        mysql.connection.commit()
        cursor.close()
    except Exception:
        pass


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


def admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access only.", "danger")
            return redirect(url_for("dashboard"))

        return route_function(*args, **kwargs)

    return wrapper


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()

        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]

            log_action(user["username"], "Logged in")

            # Set a session flag to show alert on dashboard
            session["login_success_alert"] = True
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")

@app.route("/clear_login_alert")
def clear_login_alert():
    session.pop("login_success_alert", None)
    return "", 204

@app.route("/dashboard")
@login_required
def dashboard():
    original_df = get_clean_data()

    filter_values = {
        "gender": request.args.get("gender", ""),
        "platform": request.args.get("platform", ""),
        "social_level": request.args.get("social_level", ""),
        "depression": request.args.get("depression", ""),
        "min_age": request.args.get("min_age", ""),
        "max_age": request.args.get("max_age", ""),
        "min_stress": request.args.get("min_stress", ""),
        "max_stress": request.args.get("max_stress", "")
    }

    df = apply_dashboard_filters(original_df, filter_values)

    if df.empty:
        flash("No records matched your selected filters. Showing the full dataset instead.", "warning")
        df = original_df.copy()

    analytics = MentalHealthAnalytics(df)
    charts = ChartGenerator(df, CHART_DIR).generate_all()

    kpis = {
        "Filtered Records": analytics.total_records(),
        "Average Sleep Hours": analytics.average_sleep(),
        "Average Social Media Hours": analytics.average_social_media(),
        "Average Stress Level": analytics.average_stress(),
        "Depression Label %": f"{analytics.depression_percentage()}%"
    }

    platform_table = (
    analytics.platform_usage_counts()
    .reset_index(name="Count")
    .rename(columns={"index": "Platform", "platform_usage": "Platform"})
)

    filter_options = {
        "genders": sorted(original_df["gender"].dropna().unique()),
        "platforms": sorted(original_df["platform_usage"].dropna().unique()),
        "social_levels": sorted(original_df["social_interaction_level"].dropna().unique()),
        "ages": sorted(original_df["age"].dropna().unique()),
        "stress_levels": sorted(original_df["stress_level"].dropna().unique())
    }

    return render_template(
    "dashboard.html",
    kpis=kpis,
    charts=charts,
    filter_values=filter_values,
    filter_options=filter_options,
    platform_table=platform_table.to_html(
        classes="table table-striped table-bordered platform-table",
        index=False
    ),
    summary_table=analytics.summary_table().to_html(classes="table table-bordered")
)


@app.route("/accounts", methods=["GET", "POST"])
@admin_required
def accounts():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "").strip()

        if not username or not password or not role:
            return "missing_fields", 400

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Check if username exists first
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            return "exists", 409

        try:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, role)
            )
            mysql.connection.commit()
            cursor.close()
            log_action(session["user"], f"Added new {role} account: {username}")
            return "success", 200
        except Exception as e:
            cursor.close()
            return str(e), 500

    # GET request
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, username, role FROM users ORDER BY id ASC")
    users = cursor.fetchall()

    cursor.execute("SELECT * FROM user_actions ORDER BY created_at DESC LIMIT 20")
    actions = cursor.fetchall()
    cursor.close()

    return render_template("accounts.html", users=users, actions=actions)


@app.route("/learnings")
@login_required
def learnings():
    members = [
        {
            "name": "Xyrille Dave Paltep",
            "learning": "What I learned in IPT is that Python is actually more powerful than I expected, especially once you start discovering its built-in packages and methods like Pandas, NumPy, and Matplotlib that can simplify a lot of complex tasks. I used to think programming was just about writing long blocks of code, but this subject showed me that concepts like data cleaning, functions, exception handling, and even object-oriented programming all work together to make your code more organized and efficient. It was challenging at times but it genuinely helped me understand Python on a deeper level and made me more confident in working with data, building logic, and writing code overall."
        },
        {
            "name": "Princess Marcelle Ambrocio",
            "learning": "What I learned is how to approach programming and data analysis in a structured way. I discovered how classes and objects help organize data and tasks efficiently. I also learned to handle datasets with Pandas and NumPy, cleaning data, managing missing values, removing duplicates, and performing statistical calculations such as mean, median, and standard deviation.\n\nI explored data visualization with Matplotlib and analytics. Creating charts and customizing them with labels, legends, and grids helped me present insights clearly. I realized that careful analysis and data management are key to making sense of information. I learned that even small mistakes in cleaning or processing data can affect results significantly. This class helped me appreciate the value of organized coding practices and data handling, which are essential skills not only for programming but also for making informed decisions based on data."
        },
        {
            "name": "John Paul Dela Cruz",
            "learning": "In IPT, I learned that programming is not just writing code but also managing and cleaning data, organizing it with lists and dictionaries, and using loops, conditions, and functions to handle tasks efficiently. Object-oriented programming helped me model real-world data, while libraries like Pandas, NumPy, and Matplotlib made data analysis and visualization easier. Flask introduced me to basic web development, letting me display insights on dashboards. Overall, the course improved my coding, data handling, visualization, and web skills—even though I used to struggle with programming."
        },
        {
            "name": "Renzel Espiritu",
            "learning": "I learned how Python can be used to prepare, organize, process, and analyze data. We discussed important programming concepts such as data cleaning, validation, control structures, functions, exception handling, lists, dictionaries, and object-oriented programming. The topics helped me understand how programs can handle different types of data and perform tasks such as filtering, grouping, counting, and computing results. The lessons showed me that using proper programming techniques can make data processing more organized, efficient, and reliable."
        },
        {
            "name": "Ashley Gapasin",
            "learning": "I learned many topics in IPT such as data cleaning, validation, filtering, working with CSV files, and using Python tools like lists, dictionaries, Pandas, NumPy, Matplotlib, and Flask. I also learned how to process, analyze, and visualize data step by step. I realized that understanding the logic is more important than memorizing the syntax because it helps me solve problems even when the code or situation changes."
        }
    ]

    return render_template("learnings.html", members=members)

@app.route("/logout")
@login_required
def logout():
    username = session.get("user")

    if username:
        log_action(username, "Logged out")

    session.clear()
    flash("You have been logged out.", "info")

    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not username or not password or not confirm_password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, %s)
                """,
                (username, password, "user")
            )
            mysql.connection.commit()
            cursor.close()

            flash("Account created successfully. You can now login.", "success")
            return redirect(url_for("login"))

        except MySQLdb.IntegrityError:
            flash("Username already exists. Please choose another username.", "danger")

        except Exception as error:
            flash(f"Error creating account: {error}", "danger")

    return render_template("register.html")

@app.route("/promote_user/<int:user_id>")
@admin_required
def promote_user(user_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("SELECT username, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("accounts"))

        if user["role"] == "admin":
            flash("This user is already an admin.", "warning")
            return redirect(url_for("accounts"))

        cursor.execute(
            "UPDATE users SET role = %s WHERE id = %s",
            ("admin", user_id)
        )
        mysql.connection.commit()
        cursor.close()

        log_action(session["user"], f"Promoted user to admin: {user['username']}")
        flash(f"{user['username']} has been promoted to admin.", "success")

    except Exception as error:
        flash(f"Error promoting user: {error}", "danger")

    return redirect(url_for("accounts"))


@app.route("/demote_user/<int:user_id>")
@admin_required
def demote_user(user_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("SELECT username, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("accounts"))

        if user["username"] == session["user"]:
            flash("You cannot demote your own account while logged in.", "danger")
            return redirect(url_for("accounts"))

        if user["role"] == "user":
            flash("This account is already a regular user.", "warning")
            return redirect(url_for("accounts"))

        cursor.execute(
            "UPDATE users SET role = %s WHERE id = %s",
            ("user", user_id)
        )
        mysql.connection.commit()
        cursor.close()

        log_action(session["user"], f"Demoted admin to user: {user['username']}")
        flash(f"{user['username']} has been demoted to user.", "success")

    except Exception as error:
        flash(f"Error demoting user: {error}", "danger")

    return redirect(url_for("accounts"))

@app.route("/delete_user/<int:user_id>")
@admin_required
def delete_user(user_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("accounts"))

        if user["username"] == session["user"]:
            flash("You cannot remove your own account while logged in.", "danger")
            return redirect(url_for("accounts"))

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cursor.close()

        log_action(session["user"], f"Removed account: {user['username']}")
        flash("User account removed successfully.", "success")

    except Exception as error:
        flash(f"Error removing user: {error}", "danger")

    return redirect(url_for("accounts"))




if __name__ == "__main__":
    app.run(debug=True)
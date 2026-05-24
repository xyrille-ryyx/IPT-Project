from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.data_processor import DataProcessor
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'mental_health_dashboard'

mysql = MySQL(app)

app.secret_key = "mentalhealthsecret"


def ensure_action_log_table():
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_actions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            action VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    mysql.connection.commit()
    cursor.close()


def log_user_action(username, action):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO user_actions (username, action) VALUES (%s, %s)",
            (username, action)
        )
        mysql.connection.commit()
        cursor.close()
    except Exception as err:
        print(f"User action log error: {err}")


def ensure_user_email_column():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SHOW COLUMNS FROM users LIKE 'email'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255) DEFAULT NULL")
            mysql.connection.commit()
        cursor.close()
    except Exception as err:
        print(f"User email column check error: {err}")

with app.app_context():
    ensure_action_log_table()
    ensure_user_email_column()

# Load Dataset
processor = DataProcessor(
    'dataset/Teen_Mental_Health_Dataset.csv'
)

processor.load_data()
processor.clean_data()

df = processor.get_data()

# ---------------- LOGIN ---------------- #

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Please enter both username and password", "warning")
            return render_template('login.html')

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (username, password)
            )
            user = cursor.fetchone()
        except Exception as err:
            flash("Unable to validate credentials right now. Please try again.", "danger")
            print(f"Login DB error: {err}")
            return render_template('login.html')

        if user:
            session['user'] = user[1]
            session['role'] = user[3]
            log_user_action(user[1], "Logged in")
            flash("Welcome back!", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid credentials", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not username or not password or not confirm_password:
            flash("Please complete all registration fields", "warning")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template('register.html')

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username=%s",
                (username,)
            )
            existing = cursor.fetchone()

            if existing:
                flash("Username already exists", "danger")
                return render_template('register.html')

            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, 'user')
            )
            mysql.connection.commit()
            log_user_action(username, "Created new account")
        except Exception as err:
            flash("Unable to create account right now. Please try again later.", "danger")
            print(f"Register DB error: {err}")
            return render_template('register.html')

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# ---------------- DASHBOARD ---------------- #

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    filtered_df = df.copy()

    selected_gender = request.args.get('gender', '')
    selected_age_min = request.args.get('age_min', '').strip()
    selected_age_max = request.args.get('age_max', '').strip()

    if selected_gender:
        filtered_df = filtered_df[
            filtered_df['gender'].str.lower() == selected_gender.lower()
        ]

    min_age = None
    max_age = None
    try:
        if selected_age_min:
            min_age = int(selected_age_min)
            filtered_df = filtered_df[filtered_df['age'] >= min_age]
        if selected_age_max:
            max_age = int(selected_age_max)
            filtered_df = filtered_df[filtered_df['age'] <= max_age]

        if min_age is not None and max_age is not None and min_age > max_age:
            min_age, max_age = max_age, min_age
            filtered_df = filtered_df[(filtered_df['age'] >= min_age) & (filtered_df['age'] <= max_age)]
    except ValueError:
        flash('Age filters must be entered as numbers.', 'warning')

    total_records = len(filtered_df)

    if selected_gender or selected_age_min or selected_age_max:
        if total_records == 0:
            flash('No matching records found for the selected filters.', 'warning')
        else:
            summary_parts = []
            if selected_gender:
                summary_parts.append(f'{selected_gender.title()}')
            if selected_age_min or selected_age_max:
                age_range_text = f"ages {selected_age_min or int(df['age'].min())} to {selected_age_max or int(df['age'].max())}"
                summary_parts.append(age_range_text)
            flash(f"Showing {total_records} records for {' • '.join(summary_parts)}.", 'success')

    avg_sleep = round(filtered_df['sleep_hours'].astype(float).mean(), 1) if total_records else 0
    avg_stress = round(filtered_df['stress_level'].astype(float).mean(), 1) if total_records else 0
    depression_rate = round(filtered_df['depression_label'].astype(int).mean() * 100, 1) if total_records else 0

    stress_counts = filtered_df['stress_level'].value_counts().sort_index()
    stress_chart_labels = [str(int(value)) for value in stress_counts.index.tolist()]
    stress_chart_values = stress_counts.tolist()

    sleep_by_age = filtered_df.groupby('age')['sleep_hours'].mean().sort_index()
    sleep_chart_labels = [str(int(age)) for age in sleep_by_age.index.tolist()]
    sleep_chart_values = [round(float(val), 1) for val in sleep_by_age.tolist()]

    age_min_bound = int(df['age'].min())
    age_max_bound = int(df['age'].max())

    return render_template(
        'dashboard.html',
        total_records=total_records,
        avg_sleep=avg_sleep,
        avg_stress=avg_stress,
        depression_rate=depression_rate,
        selected_gender=selected_gender,
        selected_age_min=selected_age_min,
        selected_age_max=selected_age_max,
        age_min_bound=age_min_bound,
        age_max_bound=age_max_bound,
        stress_chart_labels=stress_chart_labels,
        stress_chart_values=stress_chart_values,
        sleep_chart_labels=sleep_chart_labels,
        sleep_chart_values=sleep_chart_values
    )

# ---------------- ACCOUNT PAGE ---------------- #

@app.route('/admin')
def admin_dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        flash('Administrator access required.', 'danger')
        return redirect(url_for('dashboard'))

    total_users = 0
    total_admins = 0
    recent_actions = []
    top_actions = []

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role=%s", ('admin',))
        total_admins = cursor.fetchone()[0]
        cursor.execute("SELECT username, action, created_at FROM user_actions ORDER BY created_at DESC LIMIT 15")
        recent_actions = cursor.fetchall()
        cursor.close()
    except Exception as err:
        flash('Unable to load admin metrics right now.', 'danger')
        print(f'Admin dashboard load error: {err}')

    avg_sleep = round(df['sleep_hours'].astype(float).mean(), 1)
    avg_stress = round(df['stress_level'].astype(float).mean(), 1)
    depression_rate = round(df['depression_label'].astype(int).mean() * 100, 1)

    return render_template('admin_dashboard.html', total_users=total_users, total_admins=total_admins, recent_actions=recent_actions, avg_sleep=avg_sleep, avg_stress=avg_stress, depression_rate=depression_rate)


@app.route('/accounts', methods=['GET', 'POST'])
def accounts():

    if 'user' not in session:
        return redirect(url_for('login'))

    current_user = session.get('user')
    current_role = session.get('role', 'user')
    users = []
    activity_log = []

    current_email = ''

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'save_profile':
            new_username = request.form.get('new_username', '').strip()
            email = request.form.get('email', '').strip()
            current_password = request.form.get('current_password', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if not current_password:
                flash('Please enter your current password to save changes.', 'warning')
                return redirect(url_for('accounts'))

            try:
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT password, email FROM users WHERE username=%s", (current_user,))
                user_record = cursor.fetchone()

                if not user_record:
                    flash('Unable to verify current account.', 'danger')
                    cursor.close()
                    return redirect(url_for('accounts'))

                stored_password, current_email = user_record
                if stored_password != current_password:
                    flash('Current password is incorrect.', 'danger')
                    cursor.close()
                    return redirect(url_for('accounts'))

                if new_password and new_password != confirm_password:
                    flash('New password confirmation does not match.', 'danger')
                    cursor.close()
                    return redirect(url_for('accounts'))

                changes = []
                params = []

                if new_username and new_username != current_user:
                    cursor.execute("SELECT id FROM users WHERE username=%s", (new_username,))
                    if cursor.fetchone():
                        flash('That username is already in use.', 'danger')
                        cursor.close()
                        return redirect(url_for('accounts'))
                    changes.append('username=%s')
                    params.append(new_username)

                if email:
                    changes.append('email=%s')
                    params.append(email)

                if new_password:
                    changes.append('password=%s')
                    params.append(new_password)

                if changes:
                    params.append(current_user)
                    cursor.execute(f"UPDATE users SET {', '.join(changes)} WHERE username=%s", tuple(params))
                    mysql.connection.commit()
                    if new_username:
                        session['user'] = new_username
                        current_user = new_username
                    flash('Your profile has been updated successfully.', 'success')
                    log_user_action(current_user, 'Updated profile settings')
                else:
                    flash('No changes were detected.', 'info')

                cursor.close()
            except Exception as err:
                flash('Unable to update your profile right now. Please try again later.', 'danger')
                print(f'Profile update error: {err}')

            return redirect(url_for('accounts'))

        if current_role != 'admin':
            flash('Admin access is required to perform this action.', 'danger')
            return redirect(url_for('accounts'))

        target_id = request.form.get('user_id')

        if action in ['remove', 'promote'] and target_id:
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT id, username, role FROM users WHERE id=%s", (target_id,))
                target_user = cursor.fetchone()

                if not target_user:
                    flash('The selected user could not be found.', 'warning')
                elif target_user[1] == current_user and action == 'remove':
                    flash('Administrators cannot remove their own account through this panel.', 'danger')
                else:
                    if action == 'remove':
                        cursor.execute("DELETE FROM users WHERE id=%s", (target_id,))
                        mysql.connection.commit()
                        flash(f'User {target_user[1]} was removed successfully.', 'success')
                        log_user_action(current_user, f'Removed user {target_user[1]}')
                    elif action == 'promote':
                        if target_user[2] == 'admin':
                            flash(f'{target_user[1]} is already an admin.', 'info')
                        else:
                            cursor.execute("UPDATE users SET role=%s WHERE id=%s", ('admin', target_id))
                            mysql.connection.commit()
                            flash(f'User {target_user[1]} has been promoted to admin.', 'success')
                            log_user_action(current_user, f'Promoted user {target_user[1]} to admin')
                cursor.close()
            except Exception as err:
                flash('Unable to update users at this time. Please try again later.', 'danger')
                print(f'User management error: {err}')

        return redirect(url_for('accounts'))

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM users WHERE username=%s", (current_user,))
        email_record = cursor.fetchone()
        current_email = email_record[0] if email_record and email_record[0] else ''
        cursor.close()
    except Exception as err:
        print(f'Could not load current email: {err}')

    if current_role == 'admin':
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id, username, role FROM users ORDER BY username ASC")
            users = cursor.fetchall()
            cursor.execute("SELECT username, action, created_at FROM user_actions ORDER BY created_at DESC LIMIT 20")
            activity_log = cursor.fetchall()
            cursor.close()
        except Exception as err:
            flash('Unable to load user management data.', 'danger')
            print(f'User management load error: {err}')

    return render_template('accounts.html', users=users, activity_log=activity_log, current_role=current_role, current_user=current_user)

# ---------------- LEARNINGS PAGE ---------------- #

@app.route('/learnings')
def learnings():

    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('learnings.html')

# ---------------- LOGOUT ---------------- #

@app.route('/logout', methods=['GET', 'POST'])
def logout():

    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'continue':
            log_user_action(session.get('user'), 'Logged out')
            session.pop('user', None)
            session.pop('role', None)
            flash('You have been logged out successfully.', 'success')
            return redirect(url_for('login'))

    return redirect(url_for('dashboard'))

# ---------------- ERROR PAGE ---------------- #

@app.errorhandler(404)
def page_not_found(error):
    return "<h1>404 Page Not Found</h1>", 404

# ---------------- RUN APP ---------------- #

if __name__ == '__main__':
    app.run(debug=True)
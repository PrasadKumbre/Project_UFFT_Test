from flask import Blueprint, render_template, request, redirect, flash, current_app,url_for,session
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_mail import Message
from apscheduler.schedulers.background import BackgroundScheduler
import mysql.connector
from db_connection import get_connection
from flask_mail import Mail, Message


# # Database configuration
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_PASSWORD = "Krishna1919@"
# DB_NAME = "projectufft"

# def get_db_connection():
#     """Establish and return a database connection."""
#     return mysql.connector.connect(
#         host=DB_HOST,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         database=DB_NAME
#     )
    

def allowed_file(filename):
    """Check if the uploaded file is allowed based on extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'pdf'}

def send_budget_alerts():
    """Send alerts for budgets exceeding thresholds."""
    #connection = get_db_connection()
    connection=get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM budgets')
    budgets = cursor.fetchall()

    for budget in budgets:
        if budget['amount'] > budget['threshold_value']:
            send_alert_email(budget['category_id'], budget['amount'], budget['threshold_value'])

    connection.close()

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_budget_alerts, trigger='interval', minutes=60)
scheduler.start()

def send_alert_email(user_mail,name, total_expenses, threshold_value):
        """Send an alert email to the user when budget threshold is exceeded."""
        mail = current_app.extensions['mail']  # Use the current app's mail instance
        subject = f"Budget Alert: {name} Expenses Exceeded"
        body = f"""
        Dear User,

        Your expenses for the category '{name}' have exceeded the budget threshold.
        
        Total Expenses: ${total_expenses}
        Threshold: ${threshold_value}
        
        Please review your spending.
        
        Regards,
        Budget Tracker Team
        """
        message = Message(subject=subject, recipients=[user_mail], body=body)

        try:
            mail.send(message)
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
        
        
        
# def send_user_alert_email(user_email, total_expenses, user_budget):
#     message = Message(
#         "Personal Budget Alert",
#         sender="krishna939078@gmail.com",
#         recipients=[user_email]
#     )
#     msg.body = (
#         f"Alert! Your total expenses have exceeded your personal budget.\n"
#         f"Total Expenses: ${total_expenses}\n"
#         f"Your Budget: ${user_budget}"
#     )
#     mail.send(message)

def send_user_alert_email(user_email, total_expenses, user_budget):
    """Send an alert email to the user when budget for user is exceeded."""
    mail = current_app.extensions['mail']  # Use the current app's mail instance
    subject = f" Personal Budget Alert: User budget Exceeded"
    body = f"""
    Dear User,

    Alert! Your total expenses have exceeded your personal budget.
    
    Total Expenses: ${total_expenses}
    Threshold: ${user_budget}
    
    Please review your spending.
    
    Regards,
    Budget Tracker Team
    """
    message = Message(subject=subject, recipients=[user_email], body=body)

    try:
        mail.send(message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")



# Blueprint definition
budget_bp = Blueprint('budget', __name__, template_folder='templates', static_folder='static')
# Routes for the blueprint (as provided earlier)


# Add routes and logic here (e.g., `/add_budget`, `/report`, etc.)


# Budget routes
@budget_bp.route('/')
def home():
    # connection = get_db_connection()
    connection=get_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch category budgets
    cursor.execute('''
        SELECT 
            budgets.*,
            categories.name 
        FROM 
            budgets
        INNER JOIN 
            categories 
        ON 
            budgets.category_id = categories.category_id
    ''')
    category_budgets = cursor.fetchall()
    
    # Fetch user budgets
    cursor.execute('''
        SELECT 
            budgets.*,
            users.user_name AS name
        FROM 
            budgets
        INNER JOIN 
            users 
        ON 
            budgets.user_id = users.user_id
    ''')
    user_budgets = cursor.fetchall()
    
    connection.close()
    return render_template('home2.html', 
                           category_budgets=category_budgets, 
                           user_budgets=user_budgets)


@budget_bp.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        # connection = get_db_connection()
        connection=get_connection()
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO categories (name)
            VALUES (%s)
        ''', (name,))
        connection.commit()
        connection.close()

        flash('Category added successfully!', 'success')
        return redirect('/budget')

    return render_template('add_category.html')

@budget_bp.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        budget_type = request.form['budget_type']  # 'category' or 'user'
        amount = request.form['amount']
        threshold_value = request.form['threshold_value']
        recurring = bool(int(request.form['recurring']))
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # connection = get_db_connection()
        connection=get_connection()
        cursor = connection.cursor()

        if budget_type == 'category':
            category_id = request.form['category_id']
            if not category_id:
                flash('Category is required for Category Budget!', 'danger')
                return redirect('budget.add_budget')
            cursor.execute('''
                INSERT INTO budgets (category_id, amount, start_date, end_date, recurring, threshold_value, user_id) 
                VALUES (%s, %s, %s, %s, %s, %s, NULL)
            ''', (category_id, amount, start_date, end_date, recurring, threshold_value))

        elif budget_type == 'user':
            user_id = request.form['user_id']
            if not user_id:
                flash('User is required for User Budget!', 'danger')
                return redirect('budget.add_budget')
            cursor.execute('''
                INSERT INTO budgets (user_id, amount, start_date, end_date, recurring, threshold_value, category_id) 
                VALUES (%s, %s, %s, %s, %s, %s, NULL)
            ''', (user_id, amount, start_date, end_date, recurring, threshold_value))

        connection.commit()
        connection.close()

        flash('Budget added successfully!', 'success')
        return redirect(url_for('budget.home'))

    # connection = get_db_connection()
    connection=get_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch categories and users for the dropdown
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    connection.close()

    return render_template('add_budget.html', categories=categories, users=users)
@budget_bp.route('/edit_budget/<int:id>', methods=['GET', 'POST'])

def edit_budget(id):
    budget_type = request.args.get('budget_type', 'category')
    
    # connection = get_db_connection()
    connection=get_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch the appropriate budget based on the type (category or user)
    if budget_type == 'category':
        cursor.execute('SELECT * FROM budgets WHERE budget_id = %s', (id,))
    else:
        cursor.execute('''
            SELECT budgets.*, users.user_name AS name
            FROM budgets
            INNER JOIN users ON budgets.user_id = users.user_id
            WHERE budget_id = %s
        ''', (id,))
    
    budget = cursor.fetchone()
    
    if not budget:
        flash('Budget not found!', 'danger')
        return redirect('/budget')

    if request.method == 'POST':
        # Get updated fields
        amount = request.form['amount']
        threshold_value = request.form['threshold_value']
        recurring = bool(int(request.form['recurring']))
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Update the budget in the database
        if budget_type == 'category':
            category_id = request.form['category_id']
            cursor.execute(''' 
                UPDATE budgets 
                SET category_id = %s, amount = %s, threshold_value = %s, recurring = %s, start_date = %s, end_date = %s 
                WHERE budget_id = %s
            ''', (category_id, amount, threshold_value, recurring, start_date, end_date, id))
        else:
            user_id = request.form['user_id']
            cursor.execute(''' 
                UPDATE budgets 
                SET user_id = %s, amount = %s, threshold_value = %s, recurring = %s, start_date = %s, end_date = %s 
                WHERE budget_id = %s
            ''', (user_id, amount, threshold_value, recurring, start_date, end_date, id))

        connection.commit()
        connection.close()

        flash('Budget updated successfully!', 'success')
        return redirect('/budget')
    # Fetch categories or users for the dropdown
    if budget_type == 'category':
        cursor.execute('SELECT * FROM categories')
        dropdown = cursor.fetchall()
    else:
        cursor.execute('SELECT * FROM users')
        dropdown = cursor.fetchall()

    connection.close()
    return render_template('edit_budget.html', budget=budget, dropdown=dropdown, budget_type=budget_type)


@budget_bp.route('/expenses', methods=['GET', 'POST'])
def expenses():
    # connection = get_db_connection()
    connection=get_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form['date']
        category_id = int(request.form['category_id'])
        family_id=session['family_id']

        # Validate user_id and fetch email
        cursor.execute('SELECT email FROM users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()

        if not user:
            flash('Please enter a valid User ID.', 'error')
            connection.close()
            return redirect('/budget')

        user_email = user['email']

        # Insert the new expense
        cursor.execute('''
            INSERT INTO expenses (user_id, description, amount, date, category_id, family_id)
            VALUES (%s, %s, %s, %s, %s,%s)
        ''', (user_id, description, amount, date, category_id, family_id))
        connection.commit()

        # Calculate user's total expenses dynamically
        cursor.execute('''
            SELECT SUM(amount) AS total_expenses
            FROM expenses
            WHERE user_id = %s
        ''', (user_id,))
        total_expenses = cursor.fetchone()['total_expenses'] or 0

        # Fetch user's personal budget from budgets table
        cursor.execute('SELECT amount AS user_budget FROM budgets WHERE user_id = %s', (user_id,))
        budget_data = cursor.fetchone()

        # Send email if user's total expenses exceed their budget
        if budget_data and total_expenses > budget_data['user_budget']:
            pass
            #send_user_alert_email(user_email, total_expenses, budget_data['user_budget'])

        # Check if total expenses exceed the category threshold
        cursor.execute('''
            SELECT 
                budgets.amount AS budget_amount,
                budgets.threshold_value,
                categories.name AS category_name
            FROM budgets
            INNER JOIN categories ON budgets.category_id = categories.category_id
            WHERE budgets.category_id = %s
        ''', (category_id,))
        budget = cursor.fetchone()

        cursor.execute('''
            SELECT SUM(amount) AS category_total_expenses
            FROM expenses
            WHERE category_id = %s
        ''', (category_id,))
        category_total_expenses = cursor.fetchone()['category_total_expenses'] or 0

        # Send email if category total expenses exceed the category threshold
        if budget and category_total_expenses > budget['threshold_value']:
            send_alert_email(user_email, budget['category_name'], category_total_expenses, budget['threshold_value'])

        flash('Expense added successfully!', 'success')
        connection.close()
        return redirect('/budget')

    # Fetch categories for the dropdown
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    connection.close()

    return render_template('expenses.html', categories=categories)


@budget_bp.route('/report')
def report():
    # Get report type from query parameters (default to 'category')
    report_type = request.args.get('report_type', 'category')
    # connection = get_db_connection()
    connection=get_connection()
    cursor = connection.cursor(dictionary=True)

    report_data = []

    if report_type == 'category':
        # Fetch Category Budgets
        cursor.execute('''
            SELECT 
                budgets.category_id,
                budgets.amount AS budget_amount,
                budgets.threshold_value,
                categories.name
            FROM 
                budgets
            INNER JOIN 
                categories 
            ON 
                budgets.category_id = categories.category_id
        ''')
        budgets = cursor.fetchall()

        # Calculate total expenses for each category
        cursor.execute('''
            SELECT 
                category_id,
                SUM(amount) AS total_expenses
            FROM 
                expenses
            GROUP BY 
                category_id
        ''')
        expenses = cursor.fetchall()

        # Map expenses to categories
        expenses_dict = {expense['category_id']: expense['total_expenses'] for expense in expenses}

        # Prepare category report data
        for budget in budgets:
            category_id = budget['category_id']
            total_expenses = expenses_dict.get(category_id, 0)
            remaining = budget['budget_amount'] - total_expenses

            report_data.append({
                'name': budget['name'],
                'budget_amount': budget['budget_amount'],
                'threshold_value': budget['threshold_value'],
                'total_expenses': total_expenses,
                'remaining': remaining
            })

    elif report_type == 'user':
        # Fetch User Budgets
        cursor.execute('''
            SELECT 
                budgets.user_id,
                budgets.amount AS budget_amount,
                budgets.threshold_value,
                users.user_name AS name
            FROM 
                budgets
            INNER JOIN 
                users 
            ON 
                budgets.user_id = users.user_id
        ''')
        budgets = cursor.fetchall()

        # Calculate total expenses for each user
        cursor.execute('''
            SELECT 
                user_id,
                SUM(amount) AS total_expenses
            FROM 
                expenses
            GROUP BY 
                user_id
        ''')
        expenses = cursor.fetchall()

        # Map expenses to users
        expenses_dict = {expense['user_id']: expense['total_expenses'] for expense in expenses}

        # Prepare user report data
        for budget in budgets:
            user_id = budget['user_id']
            total_expenses = expenses_dict.get(user_id, 0)
            remaining = budget['budget_amount'] - total_expenses

            report_data.append({
                'name': budget['name'],
                'budget_amount': budget['budget_amount'],
                'threshold_value': budget['threshold_value'],
                'total_expenses': total_expenses,
                'remaining': remaining
            })

    connection.close()

    # Render the report template
    return render_template(
        'report.html',
        report_data=report_data,
        report_type=report_type
    )
from flask import Flask, render_template, request, redirect, session
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = "secret123"

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    ).fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        return redirect('/dashboard')
    else:
        return render_template(
        'login.html',
        error="Invalid Email or Password. Please correct and try again."
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
    
@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()

    try:
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        conn.commit()
        conn.close()
        return redirect('/')
    
    except:
        conn.close()

    return render_template(
        'register.html',
        error="User already exists with this email"
    )
    
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']
    conn = get_db_connection()

    # Total Income
    income = conn.execute(
        "SELECT SUM(amount) as total FROM income WHERE user_id=?",
        (user_id,)
    ).fetchone()['total'] or 0

    # Total Expense
    expense = conn.execute(
        "SELECT SUM(amount) as total FROM expense WHERE user_id=?",
        (user_id,)
    ).fetchone()['total'] or 0

    savings = income - expense

    # Budget Alerts
    alerts = []

    budgets = conn.execute(
        "SELECT category, amount FROM budget WHERE user_id=?",
        (user_id,)
    ).fetchall()

    for b in budgets:

        spent = conn.execute(
            """
            SELECT SUM(amount) as total
            FROM expense
            WHERE user_id=? AND category=?
            """,
            (user_id, b['category'])
        ).fetchone()['total'] or 0

        if spent > b['amount']:
            alerts.append(
                f"Budget exceeded for {b['category']}"
            )

    # Expense Pie Chart
    expenses_data = conn.execute(
        """
        SELECT category, SUM(amount) as total
        FROM expense
        WHERE user_id=?
        GROUP BY category
        """,
        (user_id,)
    ).fetchall()

    categories = [row['category'] for row in expenses_data]
    amounts = [row['total'] for row in expenses_data]

    investment_total = conn.execute(
    """
    SELECT SUM(amount) as total
    FROM investment
    WHERE user_id=?
    """,
    (user_id,)
    ).fetchone()['total'] or 0

    investment_total = conn.execute(
        """
        SELECT SUM(amount) as total
        FROM investment
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()['total'] or 0
    
    # Budget vs Expense Graph
    expense_categories = conn.execute(
        """
        SELECT category, SUM(amount) as spent
        FROM expense
        WHERE user_id=?
        GROUP BY category
        """,
        (user_id,)
    ).fetchall()

    budget_labels = []
    budget_values = []
    spent_values = []

    for item in expense_categories:

        category = item['category']
        spent = item['spent']

        budget = conn.execute(
            """
            SELECT amount
            FROM budget
            WHERE user_id=? AND category=?
            """,
            (user_id, category)
        ).fetchone()

        budget_amount = budget['amount'] if budget else 0

        budget_labels.append(category)
        budget_values.append(budget_amount)
        spent_values.append(spent)

    conn.close()

    return render_template(
        'dashboard.html',
        income=income,
        expense=expense,
        savings=savings,
        alerts=alerts,
        categories=categories,
        amounts=amounts,
        budget_labels=budget_labels,
        budget_values=budget_values,
        spent_values=spent_values,
        investment_total=investment_total
        
    )

@app.route('/add_income')
def add_income_page():  
    if 'user_id' not in session:
        return redirect('/')
    return render_template('add_income.html')

@app.route('/add_income', methods=['POST'])
def add_income():
    if 'user_id' not in session:
        return redirect('/')

    source = request.form['source']
    amount = request.form['amount']
    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO income (user_id, source, amount) VALUES (?, ?, ?)",
        (user_id, source, amount)
    )
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/add_expense')
def add_expense_page():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('add_expense.html')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect('/')

    category = request.form['category']
    amount = request.form['amount']
    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO expense (user_id, category, amount) VALUES (?, ?, ?)",
        (user_id, category, amount)
    )
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/add_investment')
def add_investment_page():

    if 'user_id' not in session:
        return redirect('/')

    return render_template('add_investment.html')

@app.route('/add_investment', methods=['POST'])
def add_investment():

    if 'user_id' not in session:
        return redirect('/')

    investment_type = request.form['type']
    amount = request.form['amount']
    user_id = session['user_id']

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO investment (user_id, type, amount)
        VALUES (?, ?, ?)
        """,
        (user_id, investment_type, amount)
    )

    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']
    conn = get_db_connection()

    income = conn.execute(
        "SELECT SUM(amount) as total FROM income WHERE user_id=?",
        (user_id,)
    ).fetchone()['total'] or 0

    expense = conn.execute(
        "SELECT SUM(amount) as total FROM expense WHERE user_id=?",
        (user_id,)
    ).fetchone()['total'] or 0

    # category-wise expense
    expenses = conn.execute(
        "SELECT category, SUM(amount) as total FROM expense WHERE user_id=? GROUP BY category",
        (user_id,)
    ).fetchall()

    expense_list = conn.execute(
            "SELECT * FROM expense WHERE user_id=?",
            (user_id,)
        ).fetchall()

    categories = [row['category'] for row in expenses]
    amounts = [row['total'] for row in expenses]
    conn.close()

    savings = income - expense

    return render_template('reports.html',
                           income=income,
                           expense=expense,
                           savings=savings,
                           categories=categories,
                           amounts=amounts,
                           expense_list=expense_list)


@app.route('/budget', methods=['GET', 'POST'])
def budget():

    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']
    conn = get_db_connection()

    # SAVE BUDGET
    if request.method == 'POST':

        category = request.form['category']
        amount = request.form['amount']

        conn.execute(
            "DELETE FROM budget WHERE user_id=? AND category=?",
            (user_id, category)
        )

        conn.execute(
            "INSERT INTO budget (user_id, category, amount) VALUES (?, ?, ?)",
            (user_id, category, amount)
        )

        conn.commit()

        return redirect('/budget')

    # GET BUDGETS
    budgets_raw = conn.execute(
        "SELECT * FROM budget WHERE user_id=?",
        (user_id,)
    ).fetchall()

    budgets = []

    for b in budgets_raw:

        spent = conn.execute(
            "SELECT SUM(amount) as total FROM expense WHERE user_id=? AND category=?",
            (user_id, b['category'])
        ).fetchone()['total'] or 0

        remaining = b['amount'] - spent

        percentage = 0

        if b['amount'] > 0:
            percentage = (spent / b['amount']) * 100

        budgets.append({
            'category': b['category'],
            'budget': b['amount'],
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage
        })


    conn.close()

    return render_template('budget.html', budgets=budgets)

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):

    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()

    expense = conn.execute(
        "SELECT * FROM expense WHERE id=?",
        (id,)
    ).fetchone()

    if request.method == 'POST':

        category = request.form['category']
        amount = request.form['amount']

        conn.execute(
            "UPDATE expense SET category=?, amount=? WHERE id=?",
            (category, amount, id)
        )

        conn.commit()
        conn.close()

        return redirect('/reports')

    conn.close()

    return render_template(
        'edit_expense.html',
        expense=expense
    )

if __name__ == '__main__':
    app.run(debug=True)
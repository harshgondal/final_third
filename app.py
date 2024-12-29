from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup
import oracledb
import time
import datetime
import os
app = Flask(__name__)
app.secret_key = 'your_secret_key'

con = oracledb.connect(user="SYSTEM", password="Harsh123", dsn="localhost/xepdb1")
cur = con.cursor()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if (username == "Aryan" and password == "Aryan123") or (username == "Harsh" and password == "Harsh321"):
            return redirect(url_for('menu'))
        else:
            flash('Incorrect username or password')
    
    return render_template('login.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/update_prod_status', methods=['GET', 'POST'])
def update_prod_status():
    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        new_prod_status = request.form['new_prod_status']
        
        sql = "UPDATE vehicle SET production_status = :status WHERE vehicle_id = :vehicle_id"
        val = {"status": new_prod_status, "vehicle_id": vehicle_id}

        cur.execute(sql, val)
        con.commit() 

        cur.execute("SELECT * FROM vehicle WHERE vehicle_id = :vehicle_id", {"vehicle_id": vehicle_id})
        res = cur.fetchone()
        if res==None:
            flash("Vehicle Not found")
        else:
            flash(f"Employee Salary Updated: {res}")
        # flash(f"Production Status Updated: {res}")

    return render_template('update_prod_status.html')

@app.route('/update_emp_salary', methods=['GET', 'POST'])
 # Import the datetime module

def update_emp_salary():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        new_salary = request.form['new_salary']
        
        # Update employee salary
        sql = "UPDATE employee SET salary = :new_salary WHERE e_id = :emp_id"
        val = {"emp_id": emp_id, "new_salary": new_salary}
        cur.execute(sql, val)
        con.commit()

        # Retrieve updated employee data
        cur.execute("SELECT * FROM employee WHERE e_id = :emp_id", {"emp_id": emp_id})
        res = cur.fetchone()

        # Initialize formatted_message with a default value
        formatted_message = ""

        if res is None:
            flash("Employee Not found")
        else:
            # Mapping fields to descriptive labels
            formatted_message = (
                f"Employee ID: {res[0]}<br>"
                f"Name: {res[1]}<br>"
                f"Phone Number: {res[2]}<br>"
                f"Gender: {res[3]}<br>"
                f"Address: {res[4]}<br>"
                f"Date of Joining: {res[5].strftime('%Y-%m-%d')}<br>"
                f"Salary: {res[6]}<br>"
                f"Scheme ID: {res[7]}"
            )

        # Mark the message as HTML-safe
        flash(Markup(f"Employee Salary Updated:<br>{formatted_message}"), "success")

    return render_template('update_emp_salary.html')



@app.route('/view_notifications')
def view_notifications():
    try:
        cur.execute("BEGIN DBMS_OUTPUT.ENABLE(); END;")
        cur.callproc("check_due_date_warning")
    
        lines = []
        status_var = cur.var(int)
        line_var = cur.var(str)
    
        while True:
            cur.callproc("DBMS_OUTPUT.GET_LINE", (line_var, status_var))
            if status_var.getvalue() != 0:
                break
            lines.append(line_var.getvalue())
    
        notification_message = "\n".join(lines) if lines else "No notifications found."
        flash(notification_message)
    
    except oracledb.DatabaseError as e:
        flash(str(e))

    return render_template('view_notifications.html')

@app.route('/total_vehicles_produced', methods=['GET', 'POST'])
def total_vehicles_produced():
    if request.method == 'POST':
        line_id = request.form['line_id']
        
        sql = """
            SELECT 
                a.line_id,
                a.line_name,
                SUM((ei.hours_worked * a.production_rate)) AS vehicles_produced
            FROM 
                assembly a
            JOIN 
                employee_info ei ON a.line_id = ei.assembly_line_id
            WHERE 
                a.line_id = :line_id
            GROUP BY 
                a.line_id, a.line_name
        """

        val = {"line_id": line_id}
        cur.execute(sql, val)
        results = cur.fetchall()

        message = ""
        for row in results:
            message += f"Line ID: {row[0]}, Line Name: {row[1]}, Vehicles Produced: {row[2]}\n"

        flash(message if message else "No data found for the specified line ID.")
    
    return render_template('total_vehicles_produced.html')

@app.route('/update_supplier_status', methods=['GET', 'POST'])
def update_supplier_status():
    if request.method == 'POST':
        sup_id = request.form['sup_id']
        up_status = request.form['up_status']
        
        sql = """
            UPDATE supplier
            SET status = :new_status
            WHERE supplier_id = :supplier_id
        """

        val = {"new_status": up_status, "supplier_id": sup_id}
        cur.execute(sql, val)
        con.commit()

        cur.execute("SELECT * FROM supplier WHERE supplier_id = :supplier_id", {"supplier_id": sup_id})
        updated_row = cur.fetchone()

        flash(f"Updated Row: {updated_row}" if updated_row else "No row found with the specified Supplier ID.")
    
    return render_template('update_supplier_status.html')

@app.route('/generate_monthly_expense_report', methods=['GET', 'POST'])
def generate_monthly_expense_report():
    if request.method == 'POST':
        year = request.form['year']
        month = request.form['month']
        
        try:
            cur.execute("BEGIN DBMS_OUTPUT.ENABLE(); END;")
            cur.callproc("generate_monthly_expense_report", [year, month])
            con.commit()
            time.sleep(5)

            lines = []
            line_var = cur.var(str)
            status_var = cur.var(int)
            while True:
                cur.callproc("DBMS_OUTPUT.GET_LINE", (line_var, status_var))
                if status_var.getvalue() != 0:
                    break
                lines.append(line_var.getvalue())
            report = '\n'.join(lines)
            flash(report)
        
        except oracledb.DatabaseError as e:
            flash(str(e))
    
    return render_template('generate_monthly_expense_report.html')

@app.route('/machines_per_assembly_line', methods=['GET', 'POST'])
def machines_per_assembly_line():
    if request.method == 'POST':
        assembly_id = request.form['assembly_id']
        
        sql = """
            SELECT a.line_id, m.machine_name, SUM(no_of_machines) AS num_machines
            FROM assembly a
            LEFT JOIN machine_inventory m ON a.line_id = m.assembly_id
            WHERE a.line_id = :assembly_id
            GROUP BY a.line_id, m.machine_name
        """
        cur.execute(sql, {"assembly_id": assembly_id})
        results = cur.fetchall()  # Fetch all rows that satisfy the condition

        if results:
            messages = [
                f"Assembly ID: {row[0]}, Machine Name: {row[1]}, Number of Machines: {row[2]}"
                for row in results
            ]
        else:
            messages = ["No machines found for the specified assembly ID."]

        for message in messages:
            flash(message)

    return render_template('machines_per_assembly_line.html')


@app.route('/view_production_status')
def view_production_status():
    try:
        result = cur.callfunc("update_production_status", oracledb.NUMBER)
        flash(f"Function executed successfully with result: {result}")
        con.commit()

        cur.execute("SELECT * FROM vehicle")
        records = cur.fetchall()

        message = "Updated Vehicle Records:\n" + "\n".join([str(record) for record in records])
        flash(message)
    
    except oracledb.DatabaseError as e:
        flash(str(e))

    return render_template('view_production_status.html')

@app.route('/increase_salary_if_above_avg')
def increase_salary_if_above_avg():
    try:
        cur.execute("SELECT AVG(hours_worked) FROM employee_info")
        avg_hours_worked = cur.fetchone()[0]

        sql = """
            UPDATE employee
            SET salary = salary * 1.05
            WHERE e_id IN (
                SELECT e_id
                FROM employee_info
                WHERE hours_worked > :avg_hours_worked
            )
        """
        cur.execute(sql, {"avg_hours_worked": avg_hours_worked})
        con.commit()

        flash("Salary increased by 5% for employees who worked more than the average hours.")
    
    except oracledb.DatabaseError as e:
        flash(str(e))

    return render_template('increase_salary_if_above_avg.html')

@app.route('/view_supplier_limit')
def view_supplier_limit():
    try:
        cur.callproc("DBMS_OUTPUT.ENABLE")

        plsql_block = """
            DECLARE
                v_expense_amount NUMBER;
                v_supplier_max_cost NUMBER;
            BEGIN
                SELECT SUM(amount) INTO v_expense_amount FROM expense;
                SELECT MAX(total_cost) INTO v_supplier_max_cost FROM supplier;

                IF v_expense_amount > v_supplier_max_cost THEN
                    RAISE_APPLICATION_ERROR(-20001, 'Total expense amount exceeds maximum supplier cost');
                ELSE
                    DBMS_OUTPUT.PUT_LINE('Expense amount is within supplier limits.');
                END IF;

                DBMS_OUTPUT.PUT_LINE('Total expense amount: ' || v_expense_amount);
                DBMS_OUTPUT.PUT_LINE('Maximum supplier cost: ' || v_supplier_max_cost);
            EXCEPTION
                WHEN OTHERS THEN
                    DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);
            END;
        """
        cur.execute(plsql_block)

        output = []
        line_var = cur.var(str)
        status_var = cur.var(int)
        while True:
            cur.callproc("DBMS_OUTPUT.GET_LINE", (line_var, status_var))
            if status_var.getvalue() != 0:
                break
            output.append(line_var.getvalue())

        message = "\n".join(output)
        flash(message)

    except oracledb.DatabaseError as e:
        flash(str(e))

    return render_template('view_supplier_limit.html')



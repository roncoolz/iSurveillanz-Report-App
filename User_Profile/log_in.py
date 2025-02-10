from flask import Flask, render_template, redirect, url_for, flash, request, session
from pymongo import MongoClient
from App_Setting import collection

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ensure you have a secret key for sessions

@app.route('/')
def index():
    if 'logged_in' in session:
        username = session.get('username', '')
        return render_template('report_master.html', username=username)
    return render_template('report_master.html')

@app.route('/log_in.html')
def log_in():
    return render_template('log_in.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Find the user in MongoDB and check the password directly
    user = collection.find_one({'username': username, 'password': password})

    if user:  
        session['logged_in'] = True
        session['username'] = username  # Store the username in the session
        # flash('Login successful!', 'success')
        return redirect(url_for('index'))  # Redirect to the registration form after login
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('log_in'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)  # Remove username from session
    # flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/register_form')
def register_form():
    return render_template('register_form.html')

if __name__ == '__main__':
    app.run(debug=True)

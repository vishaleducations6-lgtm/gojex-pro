from flask import Flask, render_template, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = "gojex_super_secret_key_pro"

ADMIN_USER = "zenitsu"
ADMIN_PASS = "godcreation"

@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect('/dashboard')
        else:
            return "❌ Wrong Details! Tum Zenitsu nahi ho.", 401
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

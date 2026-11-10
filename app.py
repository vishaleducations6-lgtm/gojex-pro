from flask import Flask, render_template, request, redirect, session
import os
from supabase import create_client

app = Flask(__name__)
app.secret_key = "gojex_super_secret_key_pro"

ADMIN_USER = "zenitsu"
ADMIN_PASS = "godcreation"

# ☁️ Supabase Cloud Vault Config
SUPABASE_URL = "https://pinfpgaybbrxtknnvbnf.supabase.co"
SUPABASE_KEY = "sb_publishable_2_dv36ZkyQlgIirREoHPyA_albdgTSB"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'): return redirect('/dashboard')
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect('/dashboard')
        return "❌ Wrong Details! Tum Zenitsu nahi ho.", 401
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    return render_template('dashboard.html')

@app.route('/templates', methods=['GET', 'POST'])
def templates():
    if not session.get('logged_in'): return redirect('/')
    
    # Jab tu video upload karke submit dabayega
    if request.method == 'POST':
        file = request.files.get('reel_video')
        if file:
            filename = file.filename.replace(" ", "_") # Space hata dega error se bachne ke liye
            
            # 1. Video seedha Supabase cloud me jayegi
            supabase.storage.from_("reels").upload(
                file=file.read(), 
                path=filename, 
                file_options={"content-type": "video/mp4"}
            )
            
            # 2. Upload hone ke baad permanent public link nikal lenge
            public_url = supabase.storage.from_("reels").get_public_url(filename)
            return f"<h2 style='color:green;'>✅ Upload Success!</h2><p>Video URL: <a href='{public_url}'>{public_url}</a></p><br><a href='/templates'>Go Back</a>"

    return render_template('templates_vault.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

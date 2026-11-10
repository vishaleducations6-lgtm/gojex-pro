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
        return "❌ Wrong Details!", 401
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    return render_template('dashboard.html')

@app.route('/manual')
def manual():
    if not session.get('logged_in'): return redirect('/')
    return "<h1 style='color:white; background:black; padding:20px;'>📤 Manual Upload Jald Aa Raha Hai!</h1><br><a href='/dashboard' style='color:yellow;'>Back</a>"

@app.route('/templates', methods=['GET', 'POST'])
def templates():
    if not session.get('logged_in'): return redirect('/')
    
    # Jab naya template upload ho
    if request.method == 'POST':
        file = request.files.get('reel_video')
        caption = request.form.get('caption', '') # User ka caption layega
        
        if file:
            filename = file.filename.replace(" ", "_")
            try:
                # 1. Video upload to Storage
                supabase.storage.from_("reels").upload(
                    file=file.read(), path=filename, file_options={"content-type": "video/mp4"}
                )
                public_url = supabase.storage.from_("reels").get_public_url(filename)
                
                # 2. Link & Caption Save to Database
                supabase.table("reels_bank").insert({
                    "video_url": public_url,
                    "caption": caption,
                    "status": "pending"
                }).execute()
                
                return redirect('/templates') # Upload hote hi page refresh kar dega
            except Exception as e:
                return f"<h2 style='color:red;'>❌ Error: {str(e)}</h2><br><a href='/templates'>Back</a>"

    # Database se saari 'pending' reels nikaal kar Gallery ko bhejna
    response = supabase.table("reels_bank").select("*").eq("status", "pending").order("created_at", desc=True).execute()
    pending_reels = response.data

    return render_template('templates_vault.html', reels=pending_reels)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

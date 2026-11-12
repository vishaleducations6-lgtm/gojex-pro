from flask import Flask, render_template, request, redirect, session
import os
import requests
import time
import threading
from datetime import timedelta
from supabase import create_client

app = Flask(__name__)
# Session config
app.secret_key = "gojex_ultimate_secret_v3"
app.config['SESSION_COOKIE_NAME'] = 'gojex_vip_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30) 

ADMIN_USER = "zenitsu"
ADMIN_PASS = "godcreation"

# ☁️ Supabase Cloud Config
SUPABASE_URL = "https://pinfpgaybbrxtknnvbnf.supabase.co"
SUPABASE_KEY = "sb_publishable_2_dv36ZkyQlgIirREoHPyA_albdgTSB"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🌐 Meta App Config
IG_ID = "17841437629311591"

# --- BACKGROUND PUBLISHING BOT ---
def blast_reels_to_instagram(selected_accounts_ids, selected_reel_ids):
    print(f"🔥 Blast Mode Initiated...")
    
    # Database se saari reels aur accounts nikalo
    all_reels = supabase.table("reels_bank").select("*").execute().data
    all_accs = supabase.table("connected_accounts").select("*").execute().data
    
    # Sirf jo Tick kiye hain, unko filter karo
    reels_to_post = [r for r in all_reels if str(r['id']) in selected_reel_ids]
    accounts_to_post = [a for a in all_accs if str(a['id']) in selected_accounts_ids]
    
    for reel in reels_to_post:
        for acc in accounts_to_post:
            ig_id = acc['id']
            access_token = acc['token']
            try:
                # 1. Create Container
                create_url = f"https://graph.facebook.com/v18.0/{ig_id}/media"
                payload = {
                    "media_type": "REELS", 
                    "video_url": reel['video_url'], 
                    "caption": reel['caption'], 
                    "access_token": access_token
                }
                
                create_res = requests.post(create_url, data=payload).json()
                creation_id = create_res.get("id")
                if not creation_id: 
                    print(f"❌ Container Error for {acc.get('username')}:", create_res)
                    continue

                # 2. Wait for Processing (Meta needs time)
                time.sleep(30) 

                # 3. Publish to Feed
                pub_url = f"https://graph.facebook.com/v18.0/{ig_id}/media_publish"
                pub_res = requests.post(pub_url, data={"creation_id": creation_id, "access_token": access_token}).json()
                print(f"✅ Posted Reel ID {reel['id']} on @{acc.get('username')}")
                
            except Exception as e:
                print(f"Error for @{acc.get('username')}:", e)
                
        # ⚠️ HUM STATUS UPDATE NAHI KAR RAHE. REEL HAMESHA VAULT ME RAHEGI!

# --- FLASK ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'): return redirect('/dashboard')
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session.permanent = True 
            session['logged_in'] = True
            return redirect('/dashboard')
        return "❌ Wrong Details!", 401
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    try:
        accounts = supabase.table("connected_accounts").select("*").execute().data
    except:
        accounts = []
    return render_template('dashboard.html', accounts=accounts)

@app.route('/templates', methods=['GET', 'POST'])
def templates():
    if not session.get('logged_in'): return redirect('/')
    
    if request.method == 'POST':
        # Ab koi file nahi, seedha URL aayega!
        video_url = request.form.get('video_url')
        caption = request.form.get('caption', '')
        
        if video_url:
            try:
                supabase.table("reels_bank").insert({
                    "video_url": video_url,
                    "caption": caption,
                    "status": "active" # Pending ki jagah active kardiya
                }).execute()
                return redirect('/templates')
            except Exception as e:
                return f"<h2 style='color:red;'>❌ Save Error: {str(e)}</h2><br><a href='/templates'>Back</a>"

    try:
        reels_data = supabase.table("reels_bank").select("*").order("created_at", desc=True).execute().data
        accounts = supabase.table("connected_accounts").select("*").execute().data
    except Exception as e:
        reels_data = []
        accounts = []

    return render_template('templates_vault.html', reels=reels_data, accounts=accounts)

@app.route('/post_batch', methods=['POST'])
def post_batch():
    if not session.get('logged_in'): return redirect('/')
    
    selected_reels = request.form.getlist('selected_reels')
    selected_accounts = request.form.getlist('selected_accounts')
    
    if not selected_reels:
        return "<h2 style='color:red;'>❌ Kam se kam 1 Reel toh select karo!</h2><br><a href='/templates'>Back</a>"
    
    if not selected_accounts:
        return "<h2 style='color:red;'>❌ Kam se kam 1 Account toh select karo!</h2><br><a href='/templates'>Back</a>"
        
    # Start blast in background with selected IDs
    thread = threading.Thread(target=blast_reels_to_instagram, args=(selected_accounts, selected_reels))
    thread.start()
    
    return """
    <body style="background:#0f172a; color:white; font-family:Arial; text-align:center; padding:50px;">
        <h1 style="color:#22c55e;">🚀 Super Blast Initiated!</h1>
        <p>Posting <b>{}</b> reels to <b>{}</b> accounts in the background.</p>
        <p style="color:#94a3b8; font-size:14px;">(It takes about 30 seconds per reel per account. You can close this page!)</p>
        <br><br>
        <a href='/templates' style="background:#eab308; color:black; padding:10px 20px; text-decoration:none; border-radius:6px; font-weight:bold;">🔙 Back to Vault</a>
    </body>
    """.format(len(selected_reels), len(selected_accounts))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

from flask import Flask, render_template, request, redirect, session, jsonify
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
META_APP_ID = "1412413731007169"
META_APP_SECRET = "46dd9dd47263567e27916e85eb086e0b"
REDIRECT_URI = "https://gojex-pro.onrender.com/meta_callback"

# LIVE STATUS TRACKER
BLAST_STATUS = {
    'is_running': False,
    'total_tasks': 0,
    'completed_tasks': 0,
    'logs': []
}

# --- BACKGROUND PUBLISHING BOT ---
def blast_reels_to_instagram(selected_accounts_ids, selected_reel_ids):
    global BLAST_STATUS
    BLAST_STATUS['is_running'] = True
    BLAST_STATUS['logs'].insert(0, "🔥 Blast Mode Engine Started...")
    
    all_reels = supabase.table("reels_bank").select("*").execute().data
    all_accs = supabase.table("connected_accounts").select("*").execute().data
    
    reels_to_post = [r for r in all_reels if str(r['id']) in selected_reel_ids]
    accounts_to_post = [a for a in all_accs if str(a['id']) in selected_accounts_ids]
    
    for reel in reels_to_post:
        for acc in accounts_to_post:
            ig_id = acc['id']
            access_token = acc['token']
            username = acc.get('username', 'Unknown')
            
            BLAST_STATUS['logs'].insert(0, f"⏳ Uploading to @{username} (Link: {reel['video_url'][:30]}...)")
            
            try:
                # 👇 FIX: Changed graph.facebook.com to graph.instagram.com
                create_url = f"https://graph.instagram.com/v21.0/{ig_id}/media"
                payload = {
                    "media_type": "REELS", 
                    "video_url": reel['video_url'], 
                    "caption": reel['caption'], 
                    "access_token": access_token
                }
                
                create_res = requests.post(create_url, data=payload).json()
                creation_id = create_res.get("id")
                
                if not creation_id: 
                    error_msg = create_res.get('error', {}).get('message', str(create_res))
                    BLAST_STATUS['logs'].insert(0, f"❌ ERROR on @{username}: {error_msg}")
                    BLAST_STATUS['completed_tasks'] += 1
                    continue

                BLAST_STATUS['logs'].insert(0, f"⌛ Processing Video for @{username} (Waiting 30 seconds...)")
                time.sleep(30) 

                # 👇 FIX: Changed graph.facebook.com to graph.instagram.com
                pub_url = f"https://graph.instagram.com/v21.0/{ig_id}/media_publish"
                pub_res = requests.post(pub_url, data={"creation_id": creation_id, "access_token": access_token}).json()
                
                if "id" in pub_res:
                    BLAST_STATUS['logs'].insert(0, f"✅ SUCCESS: Reel Live on @{username}! (ID: {pub_res['id']})")
                else:
                    error_msg = pub_res.get('error', {}).get('message', str(pub_res))
                    BLAST_STATUS['logs'].insert(0, f"❌ PUBLISH ERROR on @{username}: {error_msg}")
                    
            except Exception as e:
                BLAST_STATUS['logs'].insert(0, f"❌ SYSTEM ERROR on @{username}: {str(e)}")
            
            BLAST_STATUS['completed_tasks'] += 1
            
    BLAST_STATUS['is_running'] = False
    BLAST_STATUS['logs'].insert(0, "🏁 BLAST MODE COMPLETED FULLY!")

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

@app.route('/meta_login')
def meta_login():
    if not session.get('logged_in'): return redirect('/')
    auth_url = f"https://www.instagram.com/oauth/authorize?client_id={META_APP_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=instagram_business_basic,instagram_business_content_publish"
    return redirect(auth_url)

@app.route('/meta_callback')
def meta_callback():
    code = request.args.get('code')
    if not code: return "❌ Login Cancelled by User.<br><a href='/dashboard'>Back</a>"
    
    token_url = "https://api.instagram.com/oauth/access_token"
    payload = {"client_id": META_APP_ID, "client_secret": META_APP_SECRET, "grant_type": "authorization_code", "redirect_uri": REDIRECT_URI, "code": code}
    
    token_res = requests.post(token_url, data=payload).json()
    access_token = token_res.get('access_token')
    user_id = token_res.get('user_id')
    
    if access_token:
        username = f"Insta_{str(user_id)[-4:]}"
        try:
            user_info = requests.get(f"https://graph.instagram.com/me?fields=username&access_token={access_token}").json()
            if 'username' in user_info: username = user_info['username']
        except: pass

        try:
            supabase.table("connected_accounts").upsert({"id": str(user_id), "username": username, "token": access_token}).execute()
        except Exception as e:
            return f"❌ Database Save Error: {e}<br><a href='/dashboard'>Back</a>"
            
        return redirect('/dashboard')
    else: return f"❌ Token Error: {token_res}"

@app.route('/templates', methods=['GET', 'POST'])
def templates():
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        video_url = request.form.get('video_url')
        caption = request.form.get('caption', '')
        if video_url:
            try:
                supabase.table("reels_bank").insert({"video_url": video_url, "caption": caption, "status": "active"}).execute()
                return redirect('/templates')
            except Exception as e: return f"<h2 style='color:red;'>❌ Save Error: {str(e)}</h2><br><a href='/templates'>Back</a>"

    try:
        reels_data = supabase.table("reels_bank").select("*").order("created_at", desc=True).execute().data
        accounts = supabase.table("connected_accounts").select("*").execute().data
    except: reels_data, accounts = [], []

    return render_template('templates_vault.html', reels=reels_data, accounts=accounts)

@app.route('/post_batch', methods=['POST'])
def post_batch():
    if not session.get('logged_in'): return redirect('/')
    
    selected_reels = request.form.getlist('selected_reels')
    selected_accounts = request.form.getlist('selected_accounts')
    
    if not selected_reels or not selected_accounts:
        return "<h2 style='color:red;'>❌ Kam se kam 1 Reel aur 1 Account select karo!</h2><br><a href='/templates'>Back</a>"
        
    global BLAST_STATUS
    BLAST_STATUS['total_tasks'] = len(selected_reels) * len(selected_accounts)
    BLAST_STATUS['completed_tasks'] = 0
    BLAST_STATUS['logs'] = []
    
    thread = threading.Thread(target=blast_reels_to_instagram, args=(selected_accounts, selected_reels))
    thread.start()
    
    return redirect('/live_monitor')

@app.route('/api/status')
def api_status():
    global BLAST_STATUS
    return jsonify(BLAST_STATUS)

@app.route('/live_monitor')
def live_monitor():
    if not session.get('logged_in'): return redirect('/')
    return render_template('monitor.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

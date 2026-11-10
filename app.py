from flask import Flask, render_template, request, redirect, session
import os
import requests
import time
import threading
from supabase import create_client

app = Flask(__name__)
app.secret_key = "gojex_super_secret_key_pro"

ADMIN_USER = "zenitsu"
ADMIN_PASS = "vishal@"

# ☁️ Supabase Config
SUPABASE_URL = "https://pinfpgaybbrxtknnvbnf.supabase.co"
SUPABASE_KEY = "sb_publishable_2_dv36ZkyQlgIirREoHPyA_albdgTSB"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🌐 Meta App Config (Teri di hui Original Keys)
META_APP_ID = "1412413731007169"
META_APP_SECRET = "46dd9dd47263567e27916e85eb086e0b"
REDIRECT_URI = "https://gojex-pro.onrender.com/meta_callback"

# Permanent ID for Blast (Tera DB abhi connected nahi hai isliye ye backup me rakha hai)
IG_ID = "17841437629311591"

# --- BACKGROUND PUBLISHING BOT ---
def blast_reels_to_instagram(access_token):
    print("🔥 Blast Mode Initiated...")
    res = supabase.table("reels_bank").select("*").eq("status", "pending").order("created_at").execute()
    
    for reel in res.data:
        try:
            create_url = f"https://graph.facebook.com/v18.0/{IG_ID}/media"
            payload = {"media_type": "REELS", "video_url": reel['video_url'], "caption": reel['caption'], "access_token": access_token}
            if reel.get('cover_url'): payload['cover_url'] = reel['cover_url']
            
            create_res = requests.post(create_url, data=payload).json()
            creation_id = create_res.get("id")
            if not creation_id: continue

            time.sleep(30) # Processing time

            pub_res = requests.post(f"https://graph.facebook.com/v18.0/{IG_ID}/media_publish", data={"creation_id": creation_id, "access_token": access_token}).json()
            if "id" in pub_res:
                supabase.table("reels_bank").update({"status": "published"}).eq("id", reel["id"]).execute()
        except Exception as e:
            print("Error:", e)

# --- ROUTES ---
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
    return render_template('dashboard.html', is_connected=session.get('meta_connected', False))

# 👇 TERA ASLI CONNECT ROUTE
@app.route('/meta_login')
def meta_login():
    if not session.get('logged_in'): return redirect('/')
    # Ye tujhe sach me Meta ke page par le jayega
    auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={META_APP_ID}&redirect_uri={REDIRECT_URI}&scope=pages_show_list,instagram_basic,instagram_content_publish&response_type=code"
    return redirect(auth_url)

# 👇 META SE WAPAS AANE WALA ROUTE
@app.route('/meta_callback')
def meta_callback():
    code = request.args.get('code')
    if not code:
        return "❌ Login Cancelled by User.<br><a href='/dashboard'>Back</a>"
    
    # Code ko Token me convert karna
    token_url = f"https://graph.facebook.com/v18.0/oauth/access_token?client_id={META_APP_ID}&redirect_uri={REDIRECT_URI}&client_secret={META_APP_SECRET}&code={code}"
    token_res = requests.get(token_url).json()
    
    access_token = token_res.get('access_token')
    if access_token:
        session['meta_token'] = access_token
        session['meta_connected'] = True
        return redirect('/dashboard')
    else:
        return f"❌ Token Error: {token_res}"

@app.route('/templates', methods=['GET', 'POST'])
def templates():
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        file = request.files.get('reel_video')
        cover = request.files.get('cover_image')
        caption = request.form.get('caption', '')
        
        if file:
            filename = file.filename.replace(" ", "_")
            supabase.storage.from_("reels").upload(file=file.read(), path=filename, file_options={"content-type": "video/mp4"})
            public_url = supabase.storage.from_("reels").get_public_url(filename)
            
            cover_url = ""
            if cover and cover.filename:
                cover_name = "cover_" + cover.filename.replace(" ", "_")
                supabase.storage.from_("reels").upload(file=cover.read(), path=cover_name, file_options={"content-type": cover.content_type})
                cover_url = supabase.storage.from_("reels").get_public_url(cover_name)

            supabase.table("reels_bank").insert({"video_url": public_url, "cover_url": cover_url, "caption": caption, "status": "pending"}).execute()
            return redirect('/templates')

    res = supabase.table("reels_bank").select("*").eq("status", "pending").order("created_at", desc=True).execute()
    return render_template('templates_vault.html', reels=res.data)

@app.route('/post_batch', methods=['POST'])
def post_batch():
    if not session.get('logged_in'): return redirect('/')
    # Jo token login se mila, wahi posting ke liye bhej rahe hain
    token = session.get('meta_token')
    threading.Thread(target=blast_reels_to_instagram, args=(token,)).start()
    return "<body style='background:#0f172a; color:#22c55e; text-align:center; padding:50px;'><h1>🚀 Blast Initiated!</h1><p>Reels posting in background...</p><br><a href='/templates' style='color:yellow;'>Back</a></body>"

@app.route('/manual')
def manual(): return "<h1 style='color:white; background:black;'>📤 Manual Jald Aa Raha Hai!</h1>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=True)

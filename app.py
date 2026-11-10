from flask import Flask, render_template, request, redirect, session
import os
import requests
import time
import threading
from supabase import create_client

app = Flask(__name__)
app.secret_key = "gojex_super_secret_key_pro"

ADMIN_USER = "zenitsu"
ADMIN_PASS = "godcreation"

# ☁️ Supabase Cloud Vault Config
SUPABASE_URL = "https://pinfpgaybbrxtknnvbnf.supabase.co"
SUPABASE_KEY = "sb_publishable_2_dv36ZkyQlgIirREoHPyA_albdgTSB"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🌐 Meta / Instagram App Config (Teri Original Keys)
META_APP_ID = "1412413731007169"
META_APP_SECRET = "46dd9dd47263567e27916e85eb086e0b"
REDIRECT_URI = "https://gojex-pro.onrender.com/meta_callback"

# Permanent IG ID
IG_ID = "17841437629311591"

# --- BACKGROUND PUBLISHING BOT ---
def blast_reels_to_instagram(access_token):
    print("🔥 Blast Mode Initiated...")
    res = supabase.table("reels_bank").select("*").eq("status", "pending").order("created_at").execute()
    
    for reel in res.data:
        try:
            # 1. Create Container
            create_url = f"https://graph.facebook.com/v18.0/{IG_ID}/media"
            payload = {
                "media_type": "REELS", 
                "video_url": reel['video_url'], 
                "caption": reel['caption'], 
                "access_token": access_token
            }
            if reel.get('cover_url'): 
                payload['cover_url'] = reel['cover_url']
            
            create_res = requests.post(create_url, data=payload).json()
            creation_id = create_res.get("id")
            if not creation_id: 
                print("❌ Container Error:", create_res)
                continue

            # 2. Wait for Processing
            time.sleep(30) 

            # 3. Publish to Feed
            pub_url = f"https://graph.facebook.com/v18.0/{IG_ID}/media_publish"
            pub_res = requests.post(pub_url, data={"creation_id": creation_id, "access_token": access_token}).json()
            
            if "id" in pub_res:
                print(f"✅ SUCCESSFULLY POSTED! Post ID: {pub_res['id']}")
                supabase.table("reels_bank").update({"status": "published"}).eq("id", reel["id"]).execute()
            else:
                print("❌ Publish Error:", pub_res)
                
        except Exception as e:
            print("Error processing reel:", e)

# --- FLASK ROUTES ---
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
    is_connected = session.get('meta_connected', False)
    return render_template('dashboard.html', is_connected=is_connected)

# 👇 TERA ASLI INSTAGRAM CONNECT ROUTE
@app.route('/meta_login')
def meta_login():
    if not session.get('logged_in'): return redirect('/')
    auth_url = f"https://www.instagram.com/oauth/authorize?client_id={META_APP_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=instagram_business_basic,instagram_business_content_publish"
    return redirect(auth_url)

# 👇 INSTAGRAM SE WAPAS AANE WALA ROUTE
@app.route('/meta_callback')
def meta_callback():
    code = request.args.get('code')
    if not code:
        return "❌ Login Cancelled by User.<br><a href='/dashboard'>Back</a>"
    
    token_url = "https://api.instagram.com/oauth/access_token"
    payload = {
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    
    token_res = requests.post(token_url, data=payload).json()
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
            try:
                supabase.storage.from_("reels").upload(file=file.read(), path=filename, file_options={"content-type": "video/mp4"})
                public_url = supabase.storage.from_("reels").get_public_url(filename)
                
                cover_url = ""
                if cover and cover.filename:
                    cover_name = "cover_" + cover.filename.replace(" ", "_")
                    supabase.storage.from_("reels").upload(file=cover.read(), path=cover_name, file_options={"content-type": cover.content_type})
                    cover_url = supabase.storage.from_("reels").get_public_url(cover_name)

                supabase.table("reels_bank").insert({
                    "video_url": public_url,
                    "cover_url": cover_url,
                    "caption": caption,
                    "status": "pending"
                }).execute()
                
                return redirect('/templates')
            except Exception as e:
                return f"<h2 style='color:red;'>❌ Error: {str(e)}</h2><br><a href='/templates'>Back</a>"

    response = supabase.table("reels_bank").select("*").eq("status", "pending").order("created_at", desc=True).execute()
    return render_template('templates_vault.html', reels=response.data)

@app.route('/post_batch', methods=['POST'])
def post_batch():
    if not session.get('logged_in'): return redirect('/')
    
    token = session.get('meta_token')
    if not token:
        return "<h2 style='color:red;'>❌ Connect Instagram First!</h2><br><a href='/dashboard'>Back</a>"
        
    thread = threading.Thread(target=blast_reels_to_instagram, args=(token,))
    thread.start()
    
    return """
    <body style="background:#0f172a; color:white; font-family:Arial; text-align:center; padding:50px;">
        <h1 style="color:#22c55e;">🚀 Blast Initiated!</h1>
        <p>GojexBot is working in the background. Your reels will appear on Instagram one by one.</p>
        <p style="color:#94a3b8; font-size:14px;">(It takes about 30 seconds per reel for Meta to process).</p>
        <br><br>
        <a href='/templates' style="background:#eab308; color:black; padding:10px 20px; text-decoration:none; border-radius:6px; font-weight:bold;">🔙 Back to Vault</a>
    </body>
    """

@app.route('/manual')
def manual():
    if not session.get('logged_in'): return redirect('/')
    return "<h1 style='color:white; background:black; padding:20px;'>📤 Manual Upload Jald Aa Raha Hai!</h1><br><a href='/dashboard' style='color:yellow;'>Back</a>"

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('meta_connected', None)
    session.pop('meta_token', None)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

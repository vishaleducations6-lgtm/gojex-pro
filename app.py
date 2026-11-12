from flask import Flask, render_template, request, redirect, session
import os
import requests
import time
import threading
from datetime import timedelta
from supabase import create_client

app = Flask(__name__)
# 👇 PRO FIX: Nayi Secret Key aur Cookie Name taaki purana kachra saaf ho jaye
app.secret_key = "gojex_ultimate_secret_v3"
app.config['SESSION_COOKIE_NAME'] = 'gojex_vip_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30) # 30 Din tak no logout!

ADMIN_USER = "zenitsu"
ADMIN_PASS = "godcreation"

# ☁️ Supabase Cloud Vault Config
SUPABASE_URL = "https://pinfpgaybbrxtknnvbnf.supabase.co"
SUPABASE_KEY = "sb_publishable_2_dv36ZkyQlgIirREoHPyA_albdgTSB"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🌐 Meta / Instagram App Config
META_APP_ID = "1412413731007169"
META_APP_SECRET = "46dd9dd47263567e27916e85eb086e0b"
REDIRECT_URI = "https://gojex-pro.onrender.com/meta_callback"

# --- BACKGROUND PUBLISHING BOT (MULTI-ACCOUNT) ---
def blast_reels_to_instagram(accounts_list):
    print(f"🔥 Blast Mode Initiated for {len(accounts_list)} accounts...")
    res = supabase.table("reels_bank").select("*").eq("status", "pending").order("created_at").execute()
    
    for reel in res.data:
        for acc in accounts_list:
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
                if reel.get('cover_url'): 
                    payload['cover_url'] = reel['cover_url']
                
                create_res = requests.post(create_url, data=payload).json()
                creation_id = create_res.get("id")
                if not creation_id: 
                    continue

                # 2. Wait for Processing
                time.sleep(30) 

                # 3. Publish to Feed
                pub_url = f"https://graph.facebook.com/v18.0/{ig_id}/media_publish"
                requests.post(pub_url, data={"creation_id": creation_id, "access_token": access_token}).json()
                
            except Exception as e:
                print(f"Error for {acc.get('username')}:", e)
                
        # Status Update in Vault
        supabase.table("reels_bank").update({"status": "published"}).eq("id", reel["id"]).execute()


# --- FLASK ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'): return redirect('/dashboard')
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session.permanent = True # 👇 PRO FIX: Session ko hamesha ke liye lock kar diya
            session['logged_in'] = True
            return redirect('/dashboard')
        return "❌ Wrong Details!", 401
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    try:
        res = supabase.table("connected_accounts").select("*").execute()
        accounts = res.data
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
    user_id = token_res.get('user_id')
    
    if access_token:
        # Username API Call
        username = f"Insta_{str(user_id)[-4:]}"
        try:
            user_info = requests.get(f"https://graph.instagram.com/me?fields=username&access_token={access_token}").json()
            if 'username' in user_info:
                username = user_info['username']
        except:
            pass

        # Save directly to Database
        try:
            supabase.table("connected_accounts").upsert({
                "id": str(user_id),
                "username": username,
                "token": access_token
            }).execute()
        except Exception as e:
            return f"❌ Database Save Error: {e}<br><a href='/dashboard'>Back</a>"
            
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
                return f"<h2 style='color:red;'>❌ Upload Error: {str(e)}</h2><br><a href='/templates'>Back</a>"

    # 👇 PRO FIX: Vault Load ko Crash-Proof bana diya
    try:
        response = supabase.table("reels_bank").select("*").eq("status", "pending").order("created_at", desc=True).execute()
        reels_data = response.data
    except Exception as e:
        print("Vault Load Error:", e)
        reels_data = []

    return render_template('templates_vault.html', reels=reels_data)

@app.route('/post_batch', methods=['POST'])
def post_batch():
    if not session.get('logged_in'): return redirect('/')
    
    try:
        res = supabase.table("connected_accounts").select("*").execute()
        accounts = res.data
    except:
        accounts = []
    
    if not accounts:
        return "<h2 style='color:red;'>❌ Connect Instagram First!</h2><br><a href='/dashboard'>Back</a>"
        
    thread = threading.Thread(target=blast_reels_to_instagram, args=(accounts,))
    thread.start()
    
    return """
    <body style="background:#0f172a; color:white; font-family:Arial; text-align:center; padding:50px;">
        <h1 style="color:#22c55e;">🚀 Super Blast Initiated!</h1>
        <p>GojexBot is working in the background and posting to ALL connected accounts.</p>
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
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

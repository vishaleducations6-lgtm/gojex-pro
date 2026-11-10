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

# 🌐 Meta (Instagram) Graph API Config
IG_ID = "17841437629311591"
META_TOKEN = "EAAXnmnSu1ZBEBSzuLlYT6vj4ZBObTFuOzw5P3VYG1YcseUSCW7Tj9aAdNvUDlPOwMtvZBTuaoGoqTHtzbHfpi7PvlnNHJiqQdJL8ie8DQ55YAnsy20mGifNZC7PXePJQF98FCZASVUvtv4XIzmMYT7yBfCqoEvteAbgWY2uhb6nNA4EK3MxYzQLguQm663uuGWAZDZD"

# --- BACKGROUND PUBLISHING BOT ---
def blast_reels_to_instagram():
    print("🔥 Blast Mode Initiated in Background...")
    # Get all pending reels
    res = supabase.table("reels_bank").select("*").eq("status", "pending").order("created_at").execute()
    pending_reels = res.data

    for reel in pending_reels:
        try:
            # 1. Create Meta Container
            create_url = f"https://graph.facebook.com/v18.0/{IG_ID}/media"
            payload = {
                "media_type": "REELS",
                "video_url": reel['video_url'],
                "caption": reel['caption'],
                "access_token": META_TOKEN
            }
            if reel.get('cover_url'):
                payload['cover_url'] = reel['cover_url']

            print(f"📦 Creating container for Reel ID: {reel['id']}")
            create_res = requests.post(create_url, data=payload).json()
            creation_id = create_res.get("id")

            if not creation_id:
                print("❌ Container Error:", create_res)
                continue

            # 2. Wait for Instagram to process the video
            print(f"⏳ Waiting 30 seconds for Instagram processing...")
            time.sleep(30)

            # 3. Publish to Feed
            publish_url = f"https://graph.facebook.com/v18.0/{IG_ID}/media_publish"
            pub_res = requests.post(publish_url, data={"creation_id": creation_id, "access_token": META_TOKEN}).json()

            if "id" in pub_res:
                print(f"✅ SUCCESSFULLY POSTED! Post ID: {pub_res['id']}")
                # Update status in Database so it disappears from Pending Gallery
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
    return render_template('dashboard.html')

@app.route('/manual')
def manual():
    if not session.get('logged_in'): return redirect('/')
    return "<h1 style='color:white; background:black; padding:20px;'>📤 Manual Upload Jald Aa Raha Hai!</h1><br><a href='/dashboard' style='color:yellow;'>Back</a>"

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

# 👇 Naya VIP Route: Yahan se Reels Blast hoti hain
@app.route('/post_batch', methods=['POST'])
def post_batch():
    if not session.get('logged_in'): return redirect('/')
    
    # Threading start kar rahe hain taaki screen load na leti rahe
    thread = threading.Thread(target=blast_reels_to_instagram)
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

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

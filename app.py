from flask import Flask, render_template, request, redirect, session, jsonify
import os
import json
import uuid
import requests
import time
import threading
from datetime import timedelta
from supabase import create_client

app = Flask(__name__)
app.secret_key = "gojex_ultimate_secret_v3"
app.config['SESSION_COOKIE_NAME'] = 'gojex_vip_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

ADMIN_USER = "zenitsu"
ADMIN_PASS = "godcreation"

# ☁️ Supabase Cloud Config
SUPABASE_URL = "https://pinfpgaybbrxtknnvbnf.supabase.co"
SUPABASE_KEY = "sb_publishable_2_dv36ZkyQlgIirREoHPyA_albdgTSB"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 📦 Dropbox Config (Lifetime Auto-Refresh)
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY", "cocv4248l0ky3mg")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET", "xjf4c4zasj9fiuo")
DROPBOX_REDIRECT_URI = "https://babu-pro.onrender.com/dropbox_callback"

DROPBOX_STATE = {
    "refresh_token": os.environ.get("DROPBOX_REFRESH_TOKEN", ""),
    "access_token": os.environ.get(
        "DROPBOX_TOKEN",
        "sl.u.AG78dCErKcK17RZ6mArHteh3e2sjwMoYSYLArTrI0yn6snIhJexaQRrMWVkQoK6QrJhA5AgQ8JOSS-fQDyQ6jdLjWgenYS1VvMC7aw8Zt7D9c_juksWHj-eMTvW6ghhIT-LTR4MGCRwOgT3zp2Wb3_PSno81-RZDTzTN9p_g43Qi034kWsYXaMFHrPkoksn0o7ejL5Jb-_vit8muM2xDlKDHnhrmraPYizTyb0G3PPElGUOJMndCNza2SQq4-xYdUX_xsAibR5q5cGqGQz0L8kVsN-To8MNxyCjmTYsGZ0r39JD0cjqUXfYqiTBUP8k1ZkCITS_BVar9_AGDE9B1Q6HKyL4ZRiKhCoKrJcDspGRfLlTVIdlHF70dVN1gJjQ7T8QDeu7y4LBFU5LtrSR-NLBjtp0OEnVm9TV3x3WtDAV8uXwn81upR5MzreV32GDHbYojyNb7eYqLg9g0Xw0dQY6sQ1zOVjekepQMawp_ezkE8zoNMT3WSiFJr4v8ZFCIzbq3OXYTROK4c1F0RlozHu1ji7BDZzNkMuO2vKQZpKOnhsERffNd2vh2Pd7DR9HaimGvuJGK3_Ub9MoXBTD8ccHsjD7CAnERC2k_S0xaOUZtuZYpNbxapw2QZz5fc9gtM6TPxft0cztw-2p5V6CuwEkIKxWMqds9cWbpTwhNCq2RuPicw3W3HSDz_qlwI2j1l32aNmLfjPBR3tYiWU5dYXlXzWo4nKQc3eU5-09_ILFKfaNYuyid3UcDG15nBiB1F3i7XsaYy5eHoW_fhWwf1IGYkwRi9NfhoAayOjc1fPbj0wo4v6xB8Zo_dHLEtSHss40IQx5zSyPS_9wJL8dAZIEJbA3o8kYf1UOTMfrzYsGgfB4xVSQykO0_nuEZYYjggZd7OQVUqMMcAAnRyvSXHFLJdUdVDkk2iFbjsxEGPZeO8r0CTDebjrbD6kyb65z5UC7lTnusejnsgj--Qp4-HFq3MNCZpXoZFLjf2NWfIfS3bkAmhrjdRedFycuw2Rj0yPvNM_2Ej53ilZFI-3nNxPIila5xLe9rgsJwrrYDb1YGpf9WQmsV9n4wooUWGfNVCXT5BI6235u2jSzvyH82RYawgsCYYtGn7KFDs6QAPczUBkNB3HoaO1__H725OHnILHDElnyaTuDdlEdkVyNGb4u6yVPOr5QhcqimI47ZN5GcwjI5Og41LoaYLzPqeO-2I_jlr0ZiO93_AJEvJY_ohdqM2SXD66HEqVum2UL30aYosh2Fc26uHFaf1mXU8G6svSRQ8QOyJrjY9A8Q5RXeudhQp1jBw7yzyPNSrSXY8qifOTtUW7p7rWERXMSb9sK4LgkgvI9uJoSNeKCqYP366sfNZrr1mnJP49E__nSUDm4ai3Bn32mOPn2sd5IlleqFmTm2snBP2nzpgfFr4CQK84xmN1vL0X8NZtFDgmzj2vAWXw"
    ),
    "expires_at": 0
}

META_APP_ID = "1412413731007169"
META_APP_SECRET = "46dd9dd47263567e27916e85eb086e0b"
REDIRECT_URI = "https://babu-pro.onrender.com/meta_callback"

BLAST_STATUS = {
    'is_running': False,
    'total_tasks': 0,
    'completed_tasks': 0,
    'logs': []
}

MANUAL_JOBS = {}


def get_valid_dropbox_token():
    # Agar refresh_token set hai toh khud naya fresh access_token le aayega
    if DROPBOX_STATE["refresh_token"]:
        if time.time() < DROPBOX_STATE["expires_at"] and DROPBOX_STATE["access_token"]:
            return DROPBOX_STATE["access_token"]

        res = requests.post(
            "https://api.dropboxapi.com/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": DROPBOX_STATE["refresh_token"],
                "client_id": DROPBOX_APP_KEY,
                "client_secret": DROPBOX_APP_SECRET,
            },
            timeout=20
        )
        if res.status_code != 200:
            raise Exception(f"Dropbox Refresh Failed: {res.text}")

        token_data = res.json()
        DROPBOX_STATE["access_token"] = token_data["access_token"]
        DROPBOX_STATE["expires_at"] = time.time() + int(token_data.get("expires_in", 14400)) - 300
        return DROPBOX_STATE["access_token"]

    return DROPBOX_STATE["access_token"]


def dropbox_upload_and_get_raw_link(file_bytes, dropbox_path):
    token = get_valid_dropbox_token()

    # 1. Upload file to Dropbox
    upload_res = requests.post(
        "https://content.dropboxapi.com/2/files/upload",
        headers={
            "Authorization": f"Bearer {token}",
            "Dropbox-API-Arg": json.dumps({
                "path": dropbox_path,
                "mode": "overwrite",
                "autorename": True,
                "mute": False
            }),
            "Content-Type": "application/octet-stream"
        },
        data=file_bytes,
        timeout=120
    )
    if upload_res.status_code != 200:
        raise Exception(f"Dropbox Upload Failed ({upload_res.status_code}): {upload_res.text}")

    # 2. Create Shared Link
    link_res = requests.post(
        "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"path": dropbox_path},
        timeout=30
    )

    raw_url = None
    if link_res.status_code == 200:
        raw_url = link_res.json().get("url")
    else:
        list_res = requests.post(
            "https://api.dropboxapi.com/2/sharing/list_shared_links",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"path": dropbox_path, "direct_only": True},
            timeout=30
        )
        if list_res.status_code == 200 and list_res.json().get("links"):
            raw_url = list_res.json()["links"][0].get("url")
        else:
            raise Exception(f"Dropbox Share Link Failed: {link_res.text}")

    if not raw_url:
        raise Exception("Dropbox link generate nahi ho paya.")

    return raw_url.replace("?dl=0", "?raw=1").replace("&dl=0", "&raw=1")


def process_single_post(reel, acc, cover_url, caption_text):
    global BLAST_STATUS
    ig_id = acc['id']
    access_token = acc['token']
    username = acc.get('username', 'Unknown')

    BLAST_STATUS['logs'].insert(0, f"🚀 Started parallel upload for @{username}...")

    try:
        create_url = f"https://graph.instagram.com/v21.0/{ig_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": reel['video_url'],
            "caption": caption_text,
            "access_token": access_token
        }

        if cover_url:
            payload['cover_url'] = cover_url

        create_res = requests.post(create_url, data=payload).json()
        creation_id = create_res.get("id")

        if not creation_id:
            error_msg = create_res.get('error', {}).get('message', str(create_res))
            BLAST_STATUS['logs'].insert(0, f"❌ CONTAINER ERROR on @{username}: {error_msg}")
            BLAST_STATUS['completed_tasks'] += 1
            return

        BLAST_STATUS['logs'].insert(0, f"⌛ @{username} is scanning the video. Waiting for Meta to process...")

        is_ready = False
        for step in range(30):
            time.sleep(10)
            status_url = f"https://graph.instagram.com/v21.0/{creation_id}?fields=status_code,status&access_token={access_token}"
            status_res = requests.get(status_url).json()

            status_code = status_res.get('status_code')
            if status_code == 'FINISHED':
                is_ready = True
                break
            elif status_code == 'ERROR':
                err_msg = status_res.get('status', 'Meta rejected the video/cover')
                BLAST_STATUS['logs'].insert(0, f"❌ META REJECTION on @{username}: {err_msg}")
                break

        if not is_ready:
            BLAST_STATUS['logs'].insert(0, f"❌ PUBLISH ABORTED for @{username}: Processing timeout after 5 minutes.")
            BLAST_STATUS['completed_tasks'] += 1
            return

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


def blast_reels_to_instagram(selected_accounts_ids, selected_reel_ids, cover_url, caption_text):
    global BLAST_STATUS
    BLAST_STATUS['is_running'] = True
    BLAST_STATUS['logs'].insert(0, "🔥 MULTI-THREAD ENGINE STARTED! All accounts posting simultaneously...")

    all_reels = supabase.table("reels_bank").select("*").execute().data
    all_accs = supabase.table("connected_accounts").select("*").execute().data

    reels_to_post = [r for r in all_reels if str(r['id']) in selected_reel_ids]
    accounts_to_post = [a for a in all_accs if str(a['id']) in selected_accounts_ids]

    threads = []

    for reel in reels_to_post:
        for acc in accounts_to_post:
            t = threading.Thread(target=process_single_post, args=(reel, acc, cover_url, caption_text))
            threads.append(t)
            t.start()

    for t in threads:
        t.join()

    BLAST_STATUS['is_running'] = False
    BLAST_STATUS['logs'].insert(0, "🏁 BLAST MODE COMPLETED FULLY!")


# ========================
# MANUAL PUBLISHER WORKER
# ========================
def run_manual_blast_worker(job_id, video_urls, caption, cover_url, selected_accounts):
    MANUAL_JOBS[job_id]["logs"].append(
        f"🚀 Blast started: {len(video_urls)} reel(s) x {len(selected_accounts)} account(s)"
    )

    for acc in selected_accounts:
        ig_id = acc['id']
        access_token = acc['token']
        username = acc.get('username', 'Unknown')

        for idx, video_url in enumerate(video_urls, start=1):
            MANUAL_JOBS[job_id]["logs"].append(f"⏳ @{username} | Reel {idx}/{len(video_urls)}: Uploading to Meta...")
            try:
                payload = {
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption,
                    "access_token": access_token
                }
                if cover_url:
                    payload["cover_url"] = cover_url

                create_res = requests.post(
                    f"https://graph.instagram.com/v21.0/{ig_id}/media",
                    data=payload,
                    timeout=30
                ).json()

                creation_id = create_res.get("id")
                if not creation_id:
                    err_msg = create_res.get('error', {}).get('message', str(create_res))
                    MANUAL_JOBS[job_id]["logs"].append(f"❌ @{username} | Reel {idx} Container Error: {err_msg}")
                    continue

                is_ready = False
                for _ in range(30):
                    time.sleep(10)
                    status_res = requests.get(
                        f"https://graph.instagram.com/v21.0/{creation_id}",
                        params={"fields": "status_code,status", "access_token": access_token},
                        timeout=20
                    ).json()
                    status_code = status_res.get("status_code")
                    if status_code == "FINISHED":
                        is_ready = True
                        break
                    elif status_code == "ERROR":
                        err_msg = status_res.get("status", "Meta rejected video/cover")
                        MANUAL_JOBS[job_id]["logs"].append(f"❌ @{username} | Reel {idx} Meta Rejection: {err_msg}")
                        break

                if not is_ready:
                    MANUAL_JOBS[job_id]["logs"].append(f"❌ @{username} | Reel {idx} Timeout after 5 minutes.")
                    continue

                pub_res = requests.post(
                    f"https://graph.instagram.com/v21.0/{ig_id}/media_publish",
                    data={"creation_id": creation_id, "access_token": access_token},
                    timeout=30
                ).json()

                if "id" in pub_res:
                    MANUAL_JOBS[job_id]["logs"].append(
                        f"✅ @{username} | Reel {idx}/{len(video_urls)} LIVE! (ID: {pub_res['id']})"
                    )
                else:
                    err_msg = pub_res.get('error', {}).get('message', str(pub_res))
                    MANUAL_JOBS[job_id]["logs"].append(f"❌ @{username} | Reel {idx} Publish Error: {err_msg}")

            except Exception as e:
                MANUAL_JOBS[job_id]["logs"].append(f"❌ @{username} | Reel {idx} System Error: {str(e)}")

    MANUAL_JOBS[job_id]["done"] = True
    MANUAL_JOBS[job_id]["logs"].append("🏁 ALL DONE! Manual Blast Completed!")


# ========================
# DROPBOX 1-CLICK LIFETIME AUTH
# ========================
@app.route('/dropbox_login')
def dropbox_login():
    if not session.get('logged_in'):
        return redirect('/')
    auth_url = (
        f"https://www.dropbox.com/oauth2/authorize"
        f"?client_id={DROPBOX_APP_KEY}"
        f"&token_access_type=offline"
        f"&response_type=code"
        f"&redirect_uri={DROPBOX_REDIRECT_URI}"
    )
    return redirect(auth_url)


@app.route('/dropbox_callback')
def dropbox_callback():
    code = request.args.get('code')
    if not code:
        return "❌ Dropbox Login Cancelled.<br><a href='/dashboard'>Back</a>"

    res = requests.post(
        "https://api.dropboxapi.com/oauth2/token",
        data={
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": DROPBOX_REDIRECT_URI,
            "client_id": DROPBOX_APP_KEY,
            "client_secret": DROPBOX_APP_SECRET,
        },
        timeout=30
    ).json()

    refresh_token = res.get("refresh_token")
    access_token = res.get("access_token")

    if not refresh_token:
        return f"<h3>❌ Refresh Token nahi mila:</h3><pre>{res}</pre><a href='/dashboard'>Back</a>"

    # Abhi turant live kar do
    DROPBOX_STATE["refresh_token"] = refresh_token
    DROPBOX_STATE["access_token"] = access_token
    DROPBOX_STATE["expires_at"] = time.time() + int(res.get("expires_in", 14400)) - 300

    return f"""
    <div style='background:#0f172a;color:#fff;font-family:sans-serif;padding:30px;min-height:100vh;'>
      <h2 style='color:#22c55e;'>✅ Dropbox Lifetime Token Ready!</h2>
      <p>Abhi turant ke liye activate ho gaya hai. Hamesha ke liye save karne ke liye ye token copy karke Render ke <b>Environment Variables</b> me <code>DROPBOX_REFRESH_TOKEN</code> naam se daal de:</p>
      <textarea style='width:100%;height:90px;padding:10px;border-radius:8px;background:#1e293b;color:#facc15;font-size:14px;' readonly>{refresh_token}</textarea>
      <br><br>
      <a href='/manual' style='background:#eab308;color:#000;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;'>🚀 Open Manual Publisher</a>
    </div>
    """


# ========================
# CORE ROUTES
# ========================
@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect('/dashboard')
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session.permanent = True
            session['logged_in'] = True
            return redirect('/dashboard')
        return "❌ Wrong Details!", 401
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    try:
        accounts = supabase.table("connected_accounts").select("*").execute().data
    except:
        accounts = []
    return render_template('dashboard.html', accounts=accounts)


@app.route('/meta_login')
def meta_login():
    if not session.get('logged_in'):
        return redirect('/')
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
        username = f"Insta_{str(user_id)[-4:]}"
        try:
            user_info = requests.get(f"https://graph.instagram.com/me?fields=username&access_token={access_token}").json()
            if 'username' in user_info:
                username = user_info['username']
        except:
            pass

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


@app.route('/disconnect/<account_id>')
def disconnect_account(account_id):
    if not session.get('logged_in'):
        return redirect('/')
    try:
        supabase.table("connected_accounts").delete().eq("id", account_id).execute()
    except:
        pass
    return redirect('/dashboard')


@app.route('/disconnect_all')
def disconnect_all():
    if not session.get('logged_in'):
        return redirect('/')
    try:
        supabase.table("connected_accounts").delete().neq("id", "0").execute()
    except:
        pass
    return redirect('/dashboard')


@app.route('/clear_reels')
def clear_reels():
    if not session.get('logged_in'):
        return redirect('/')
    try:
        supabase.table("reels_bank").delete().neq("id", 0).execute()
    except:
        pass
    return redirect('/templates')


@app.route('/clear_covers')
def clear_covers():
    if not session.get('logged_in'):
        return redirect('/')
    try:
        supabase.table("covers_bank").delete().neq("id", 0).execute()
    except:
        pass
    return redirect('/templates')


@app.route('/clear_captions')
def clear_captions():
    if not session.get('logged_in'):
        return redirect('/')
    try:
        supabase.table("captions_bank").delete().neq("id", 0).execute()
    except:
        pass
    return redirect('/templates')


@app.route('/templates', methods=['GET', 'POST'])
def templates():
    if not session.get('logged_in'):
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_link':
            video_url = request.form.get('video_url')
            if video_url:
                try:
                    supabase.table("reels_bank").insert({"video_url": video_url, "caption": "", "status": "active"}).execute()
                except Exception as e:
                    return f"<h2 style='color:red;'>❌ Save Error: {str(e)}</h2><br><a href='/templates'>Back</a>"

        elif action == 'add_cover':
            cover = request.files.get('cover_image')
            cover_name = request.form.get('cover_name', 'My Cover')
            if cover and cover.filename:
                unique_id = str(int(time.time()))
                filename = f"cover_{unique_id}_{cover.filename.replace(' ', '_')}"
                try:
                    supabase.storage.from_("reels").upload(
                        file=cover.read(),
                        path=filename,
                        file_options={"content-type": cover.content_type}
                    )
                    cover_url = supabase.storage.from_("reels").get_public_url(filename)
                    supabase.table("covers_bank").insert({"cover_url": cover_url, "cover_name": cover_name}).execute()
                except Exception as e:
                    return f"<h2 style='color:red;'>❌ Cover Upload Error: {str(e)}</h2><br><a href='/templates'>Back</a>"

        elif action == 'add_caption':
            caption_name = request.form.get('caption_name', 'My Caption')
            caption_text = request.form.get('caption_text', '')
            if caption_text:
                try:
                    supabase.table("captions_bank").insert({"caption_name": caption_name, "caption_text": caption_text}).execute()
                except Exception as e:
                    return f"<h2 style='color:red;'>❌ Caption Save Error: {str(e)}</h2><br><a href='/templates'>Back</a>"

        return redirect('/templates')

    try:
        reels_data = supabase.table("reels_bank").select("*").order("created_at", desc=True).execute().data
        accounts = supabase.table("connected_accounts").select("*").execute().data
        covers = supabase.table("covers_bank").select("*").execute().data
        captions = supabase.table("captions_bank").select("*").execute().data
    except:
        reels_data, accounts, covers, captions = [], [], [], []

    return render_template('templates_vault.html', reels=reels_data, accounts=accounts, covers=covers, captions=captions)


@app.route('/post_batch', methods=['POST'])
def post_batch():
    if not session.get('logged_in'):
        return redirect('/')

    selected_reels = request.form.getlist('selected_reels')
    selected_accounts = request.form.getlist('selected_accounts')
    selected_cover_url = request.form.get('selected_cover_url')
    selected_caption_text = request.form.get('selected_caption_text', '')

    if not selected_reels or not selected_accounts:
        return "<h2 style='color:red;'>❌ Kam se kam 1 Reel aur 1 Account select karo!</h2><br><a href='/templates'>Back</a>"

    global BLAST_STATUS
    BLAST_STATUS['total_tasks'] = len(selected_reels) * len(selected_accounts)
    BLAST_STATUS['completed_tasks'] = 0
    BLAST_STATUS['logs'] = []

    thread = threading.Thread(
        target=blast_reels_to_instagram,
        args=(selected_accounts, selected_reels, selected_cover_url, selected_caption_text)
    )
    thread.start()

    return redirect('/live_monitor')


# ========================
# MANUAL PUBLISHER ROUTES
# ========================
@app.route('/manual')
def manual_publisher():
    if not session.get('logged_in'):
        return redirect('/')
    try:
        accounts = supabase.table("connected_accounts").select("*").execute().data
        packs = supabase.table("reel_packs").select("*").order("created_at", desc=True).execute().data
    except:
        accounts, packs = [], []
    return render_template('manual.html', accounts=accounts, packs=packs)


@app.route('/api/upload-video-dropbox', methods=['POST'])
def upload_video_dropbox():
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        if "video" not in request.files:
            return jsonify({"success": False, "error": "No video file received"}), 400

        video_file = request.files["video"]
        file_bytes = video_file.read()
        dropbox_path = f"/gojex_reels/{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4"

        vip_url = dropbox_upload_and_get_raw_link(file_bytes, dropbox_path)
        return jsonify({"success": True, "url": vip_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/save-reel-pack', methods=['POST'])
def save_reel_pack():
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        data = request.json
        name = data.get("name", "").strip()
        mode = data.get("mode", "single")
        video_urls = data.get("video_urls", [])

        if not name or not video_urls:
            return jsonify({"success": False, "error": "Name aur kam se kam 1 video chahiye!"}), 400

        res = supabase.table("reel_packs").insert({
            "name": name,
            "mode": mode,
            "video_urls": video_urls
        }).execute()

        return jsonify({"success": True, "pack": res.data[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/delete-reel-pack/<int:pack_id>', methods=['DELETE'])
def delete_reel_pack(pack_id):
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        supabase.table("reel_packs").delete().eq("id", pack_id).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/upload-cover', methods=['POST'])
def upload_cover():
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        if "cover" not in request.files:
            return jsonify({"success": False, "error": "No cover image"}), 400

        cover_file = request.files["cover"]
        ext = cover_file.filename.rsplit(".", 1)[-1].lower() if "." in cover_file.filename else "jpg"
        filename = f"cover_{int(time.time())}_{uuid.uuid4().hex[:6]}.{ext}"

        supabase.storage.from_("reels").upload(
            file=cover_file.read(),
            path=filename,
            file_options={"content-type": cover_file.content_type or "image/jpeg"}
        )
        public_url = supabase.storage.from_("reels").get_public_url(filename)
        return jsonify({"success": True, "url": public_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/manual-blast', methods=['POST'])
def manual_blast():
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        data = request.json
        pack_id = data.get("pack_id")
        caption = data.get("caption", "")
        cover_url = data.get("cover_url", "").strip()
        account_ids = [str(aid) for aid in data.get("account_ids", [])]

        if not pack_id or not account_ids:
            return jsonify({"success": False, "error": "Reel/Pack aur kam se kam 1 Account select karo!"}), 400

        pack_res = supabase.table("reel_packs").select("*").eq("id", pack_id).single().execute()
        video_urls = pack_res.data["video_urls"]

        all_accs = supabase.table("connected_accounts").select("*").execute().data
        selected_accounts = [a for a in all_accs if str(a['id']) in account_ids]

        job_id = uuid.uuid4().hex[:10]
        MANUAL_JOBS[job_id] = {"done": False, "logs": []}

        threading.Thread(
            target=run_manual_blast_worker,
            args=(job_id, video_urls, caption, cover_url, selected_accounts),
            daemon=True
        ).start()

        return jsonify({"success": True, "job_id": job_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/blast-status/<job_id>')
def blast_status(job_id):
    job = MANUAL_JOBS.get(job_id)
    if not job:
        return jsonify({"done": True, "logs": ["❌ Job not found"]})
    return jsonify(job)


# ========================
# MONITOR & SYSTEM ROUTES
# ========================
@app.route('/api/status')
def api_status():
    global BLAST_STATUS
    return jsonify(BLAST_STATUS)


@app.route('/live_monitor')
def live_monitor():
    if not session.get('logged_in'):
        return redirect('/')
    return render_template('monitor.html')


@app.route('/ping')
def ping():
    return "PONG! Gojex PRO is awake! 🚀", 200


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

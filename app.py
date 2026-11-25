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

# 📦 Dropbox Config (Direct HTTP API - No pkg_resources crash!)
DROPBOX_TOKEN = os.environ.get(
    "DROPBOX_TOKEN",
    "sl.u.AG4l7JIjqUOijSa0OJVMD5dAD4PvDgXZZFgvphc1l5SGXLW8XiqFSVBnHfqSt4MXvRlyekOf1Pf_fANPQB5Ie1beqk6lIaMkt8Za7supjTsGiFABY5mMBFJ3Ukrh0HUPF-9pjry6dKWEfo5vQ5iICfY9AOvvagYdi-OVP5PvxQztKFeuxnq5DQ6G0ETK_tXor9hVw7PZxfE42yazFCo4AXhOmi57CcsOUyodJR6WnythA2SUOBaZQEuKc3vVAPjbiMK-ijfFlTBrMClTnabAMwUyzn3fhQvw39vefQfLtN1yy0PjU8H5GI6w41mitvHLule8C2eCVRjUtEnnDEIAsvvS6s73BfHOY5ZMzCu3RP9wMtdrlcE5TPP6RSLMi4SIFJCcdAWMp81rvE27sXgSaorL-Cbl8Tse2ul9P5z26IM9Um_dYv9UWY2HGhLK1yaEk4GAhmrweEczsDtboWa7ap3m1xCMvCai43z7sWbcBPVG8ES5jK5w8eH6MKDzcD3hjrMLQekAePhB2G_H4lVtzxDFqrzS82Q5nK8imAs20r_tgXENMr8MC3nL9Sg_kWnlAkF31oAMPnJhKKIoUpRLkSeucxUzYw2z_Spo_lBJwHTTg8CH1mUv92x0hN85Pi6Z3blM19HlJBcYJWV2Ic4RyF9ealh6GwcpdqJs_pvsar7uUHRbPNCe2EspCtdt6NeGkkeaI5mkxWx0BEYtgJjgyBRrftAFiPMzexVkOfT4c_zdAESr_Ja-OIlxURZ123sMQfNtQEn-0ajBwmBrWLu0bDGurnliGATmOl7TcvjCYCrzaDoyQxNRco1vDOc8YaQTl6RLgtSkkMb0Vqp2Bcku3HS_EW0mnAM5juZvR5hsg1l7rL3BVPAJGuo84mQ5DWNVBhupr3N0-lmFLVLvT3Z7FcGV6KQ7PAIHkIdfdpawAY1Y9Ndu4YfjpIr6VWL2fTX8-IPBBC9OnTymn5wuMkLFt30Us7nQ_nmQqDqT2iYk70Ox9uet73bbCWWdyAks86a8kQMkiAwPVT0-WqksoUsnA-P4bec0gMviKj-cnAQ4Ks3IKUsupYAUuiSQutTyXnA8h8WlrVBdKR2xHyJ3dKLmJCntKR1wRX8Gh8bmGXMv6B0MokDpWJ0R9-Y8eMYlouk29nG0alOcvGRjHQttaVGSVggCa4pzL6W-iaKEQZYKL0SBB1ktWjh4PoZFz5RxpTOcZbxhK3I4-zPY_OVyhw0Yw619fXloeNEKb4w8wKRSDyODIn5hXrzkI-QaqYUb10aj-0XsqkCTSKjHhSvzFET6__QTxV4ODL6_EIdiXFJlIh_fKH9XsB6Gq2eRMInKGpgjYYNFqxwW_0kK2bJsWOs8FuSfdNSxoS-uotYhetbt3G6kMPrWnpzkzzO1hjAAQ442qdaMsl3pmHqScD_q5aPS4GbudBvaBp3n8j9wAKx9Cfqor8PnTdLkZbty82PjC6JRllA5GgxG8v5hTPPEGF_ZHN-w"
)

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


def dropbox_upload_and_get_raw_link(file_bytes, dropbox_path):
    # 1. Upload file to Dropbox
    upload_res = requests.post(
        "https://content.dropboxapi.com/2/files/upload",
        headers={
            "Authorization": f"Bearer {DROPBOX_TOKEN}",
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
            "Authorization": f"Bearer {DROPBOX_TOKEN}",
            "Content-Type": "application/json"
        },
        json={"path": dropbox_path},
        timeout=30
    )

    raw_url = None
    if link_res.status_code == 200:
        raw_url = link_res.json().get("url")
    else:
        # Agar link already exist karta hai toh list_shared_links se nikal lo
        list_res = requests.post(
            "https://api.dropboxapi.com/2/sharing/list_shared_links",
            headers={
                "Authorization": f"Bearer {DROPBOX_TOKEN}",
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

        # 30 steps * 10 seconds = 5 Minutes total wait time
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

                # 5-Minute Polling Loop (30 steps x 10 sec)
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

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Gojex PRO | Link Vault</title>
    <style>
        body { background: #0f172a; color: white; font-family: Arial; padding: 30px; text-align: center; }
        .vault-container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; border: 1px solid #334155; }
        input[type="text"], input[type="url"], textarea { width: 100%; padding: 10px; margin: 10px 0; border-radius: 6px; border: none; background: #334155; color: white; box-sizing: border-box; font-size: 16px; }
        .btn { background: #eab308; color: black; padding: 12px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%; font-size: 16px; }
        .btn:hover { background: #ca8a04; }
        .btn-blast { background: #22c55e; color: white; padding: 15px; width: 100%; font-size: 18px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 20px; }
        .btn-blast:hover { background: #16a34a; }
        
        .reel-card { background: #0f172a; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #334155; text-align: left; display: flex; align-items: flex-start; gap: 15px; }
        .reel-card input[type="checkbox"] { width: 25px; height: 25px; cursor: pointer; margin-top: 10px; }
        .reel-info { flex: 1; overflow: hidden; }
        .acc-card { background: #334155; padding: 10px 15px; border-radius: 6px; margin: 10px 0; display: flex; align-items: center; gap: 10px; text-align: left;}
        .acc-card input[type="checkbox"] { width: 20px; height: 20px; cursor: pointer; }
        
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 100; }
        .modal-content { background: #1e293b; max-width: 400px; margin: 10% auto; padding: 30px; border-radius: 12px; border: 1px solid #334155; position: relative; max-height: 80vh; overflow-y: auto;}
        .close-btn { position: absolute; top: 10px; right: 15px; color: white; font-size: 24px; cursor: pointer; }
        .select-all-btn { background: #3b82f6; color: white; padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold; margin-bottom: 10px; }
    </style>
</head>
<body>

    <h1 style="color: #eab308;">🔗 Link Templates Vault</h1>
    <p style="color: #94a3b8;">Save your video URLs and Blast them anytime.</p>

    <a href="/dashboard" style="color: #3b82f6; text-decoration: none; display: block; margin-bottom: 20px;">🔙 Back to Dashboard</a>

    <div class="vault-container">
        <h2 style="border-bottom: 1px solid #334155; padding-bottom: 10px;">📥 Save New Reel Link</h2>
        
        <!-- Add Link Form (No file upload) -->
        <form action="/templates" method="POST">
            <label style="display: block; text-align: left; font-weight: bold; color: #cbd5e1;">Video URL (Catbox/Mp4 Link):</label>
            <input type="url" name="video_url" required placeholder="https://files.catbox.moe/example.mp4">
            
            <label style="display: block; text-align: left; font-weight: bold; margin-top: 10px; color: #cbd5e1;">Caption:</label>
            <textarea name="caption" rows="3" placeholder="Write your VIP caption here..."></textarea>
            
            <button type="submit" class="btn">💾 Save to Vault</button>
        </form>

        <hr style="border: 0; border-top: 1px solid #334155; margin: 40px 0;">

        <!-- BATCH POSTING FORM -->
        <form action="/post_batch" method="POST">
            
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2>🗄️ Saved Reels ({{ reels|length }})</h2>
                <button type="button" class="select-all-btn" onclick="selectAllReels()">☑️ Select All Reels</button>
            </div>
            
            {% if reels %}
                {% for reel in reels %}
                    <div class="reel-card">
                        <input type="checkbox" name="selected_reels" class="reel-checkbox" value="{{ reel.id }}">
                        <div class="reel-info">
                            <p style="margin: 0; color: #3b82f6; font-size: 12px; word-break: break-all;">🔗 {{ reel.video_url }}</p>
                            <p style="margin-top: 8px; color: #e2e8f0; font-size: 14px;"><strong>Caption:</strong> {{ reel.caption }}</p>
                        </div>
                    </div>
                {% endfor %}
                
                <button type="button" class="btn-blast" onclick="openModal()">
                    🚀 CONTINUE TO SELECT ACCOUNTS
                </button>
            {% else %}
                <p style="color: #94a3b8;">No reels saved yet. Add a link above!</p>
            {% endif %}

            <!-- VIP Account Selection Modal -->
            <div id="postModal" class="modal">
                <div class="modal-content">
                    <span class="close-btn" onclick="closeModal()">×</span>
                    <h2 style="color: #22c55e;">🎯 Select Target Accounts</h2>
                    
                    <button type="button" class="select-all-btn" onclick="selectAllAccounts()">☑️ Select All Accounts</button>

                    <div style="margin-top: 15px;">
                        {% for acc in accounts %}
                            <div class="acc-card">
                                <input type="checkbox" name="selected_accounts" class="acc-checkbox" value="{{ acc.id }}">
                                <span style="font-weight: bold;">@{{ acc.username }}</span>
                            </div>
                        {% endfor %}
                    </div>
                    
                    <button type="submit" class="btn-blast" style="margin-top: 25px;">⚡ POST TO SELECTED ACCOUNTS</button>
                </div>
            </div>

        </form>
    </div>

    <script>
        function selectAllReels() {
            let boxes = document.querySelectorAll('.reel-checkbox');
            let allChecked = Array.from(boxes).every(box => box.checked);
            boxes.forEach(box => box.checked = !allChecked);
        }

        function selectAllAccounts() {
            let boxes = document.querySelectorAll('.acc-checkbox');
            let allChecked = Array.from(boxes).every(box => box.checked);
            boxes.forEach(box => box.checked = !allChecked);
        }

        function openModal() {
            document.getElementById('postModal').style.display='block';
        }

        function closeModal() {
            document.getElementById('postModal').style.display='none';
        }
    </script>

</body>
</html>

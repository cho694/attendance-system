import os, json, datetime, hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'change-this-to-random-secret-key-12345'

# ===================== MongoDB 설정 =====================
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://choesubin2018_db_user:bYLATrVP7kyeVrgo@cluster0.qmvit80.mongodb.net/?appName=Cluster0')
client = MongoClient(MONGO_URI)
db = client['attendance_system'] 

def load(name):
    """MongoDB에서 데이터를 불러옵니다. (파일 방식 제거)"""
    col = db[name]
    doc = col.find_one({"_id": "main_data"})
    if doc:
        return doc.get('data', {})
    return {}

def save(name, data):
    """MongoDB에 데이터를 저장합니다. (파일 방식 제거)"""
    col = db[name]
    col.update_one(
        {"_id": "main_data"}, 
        {"$set": {"data": data}}, 
        upsert=True
    )

def init_admin():
    a = load('admin')
    if not a:
        a = {"password": hashlib.sha256("admin1234".encode()).hexdigest()}
        save('admin', a)
init_admin()

def get_attend_status():
    s = load('attend_status')
    return s.get('open', False)

def set_attend_status(val):
    save('attend_status', {'open': val})

def check_team_attendance(date):
    att = load('attendance').get(date, {})
    teams = load('teams')
    result = {}
    for tid, tdata in teams.items():
        members = tdata.get('members', [])
        if not members:
            result[tid] = False
            continue
        result[tid] = all(m in att for m in members)
    return result

# ===================== HTML 템플릿 (CSS 포함) =====================
BASE_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:url('/static/bg.png') no-repeat center center fixed;background-size:cover;color:#1a1a2e;min-height:100vh}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(255,255,255,0.3);z-index:0}
.container{max-width:500px;margin:0 auto;padding:20px;position:relative;z-index:1}
.card{background:rgba(255,255,255,0.92);border-radius:16px;padding:24px;margin-bottom:16px;box-shadow:0 4px 24px rgba(0,0,0,.15);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.5)}
h1{font-size:1.6rem;text-align:center;margin-bottom:20px;color:#1a1a2e;font-weight:800;text-shadow:0 1px 2px rgba(255,255,255,0.8)}
h2{font-size:1.2rem;color:#1a1a2e;margin-bottom:12px;font-weight:700}
input,select,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #ccc;background:rgba(255,255,255,0.95);color:#1a1a2e;margin-bottom:12px;font-size:1rem}
input::placeholder,textarea::placeholder{color:#888}
button{width:100%;padding:14px;border-radius:12px;border:none;font-size:1rem;font-weight:700;cursor:pointer;transition:.2s}
.btn-primary{background:linear-gradient(135deg,#2563eb,#7c3aed);color:#fff}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 4px 16px rgba(37,99,235,.4)}
.btn-danger{background:#dc2626;color:#fff;margin-top:8px}
.btn-success{background:#059669;color:#fff;margin-top:8px}
.btn-sm{width:auto;padding:8px 16px;font-size:.85rem;display:inline-block;margin:4px}
.tag{display:inline-block;padding:4px 10px;border-radius:20px;font-size:.75rem;font-weight:600}
.tag-green{background:#d1fae5;color:#065f46}
.tag-red{background:#fee2e2;color:#991b1b}
.tag-blue{background:#dbeafe;color:#1e40af}
.msg{text-align:center;padding:16px;border-radius:10px;margin:12px 0;font-weight:600}
.msg-ok{background:#d1fae5;color:#065f46;border:1px solid #6ee7b7}
.msg-err{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5}
table{width:100%;border-collapse:collapse;margin-top:8px}
th,td{padding:8px;text-align:left;border-bottom:1px solid #e5e7eb;font-size:.9rem}
th{color:#6b7280;font-weight:600}
td{color:#1a1a2e}
a{color:#2563eb;text-decoration:none;font-weight:600}
.nav{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;justify-content:center}
.back{display:block;text-align:center;margin-top:16px;color:#6b7280;font-weight:600}
.comment{background:rgba(243,244,246,0.8);border-radius:10px;padding:12px;margin-top:8px;border-left:3px solid #2563eb}
.comment-author{font-weight:700;color:#2563eb;font-size:.85rem}
.comment-time{color:#9ca3af;font-size:.75rem}
.comment-content{color:#1a1a2e;margin-top:4px;font-size:.9rem}
</style>
"""

# HTML 템플릿 변수들 (코드 길이를 위해 생략하되, 실제 파일에는 전체 내용을 넣으셔야 합니다.)
# INDEX_HTML, ATTEND_HTML, NOTICE_HTML, SCORES_HTML, BOARD_HTML, ADMIN_HTML 등 기존 내용 유지

# ── 게시판 권한 강화 로직이 포함된 라우트 ──

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/board/write', methods=['POST'])
def board_write():
    sid = request.form['student_id'].strip()
    author = request.form['author'].strip()
    title = request.form['title'].strip()
    content = request.form['content'].strip()
    
    if not all([sid, author, title, content]):
        return "<script>alert('모든 항목을 입력해주세요.'); history.back();</script>"
        
    students = load('students')
    if not students or sid not in students:
        return "<script>alert('허용되지 않은 학번입니다.'); history.back();</script>"
    if students[sid]['name'] != author:
        return "<script>alert('학번과 이름이 일치하지 않습니다.'); history.back();</script>"

    board_data = load('board')
    pid = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    board_data[pid] = {
        "author": author, "student_id": sid, "title": title, "content": content,
        "created": datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), "comments": []
    }
    save('board', board_data)
    return redirect('/board')

# ... (나머지 admin 관련 라우트 및 기능들은 기존과 동일하게 유지) ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
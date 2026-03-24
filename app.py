import os, json, datetime, hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'subin-super-secret-key-12345'

# ===================== MongoDB 설정 (수정 금지) =====================
MONGO_URI = "mongodb+srv://choesubin2018_db_user:bYLATrVP7kyeVrgo@cluster0.qmvit80.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['attendance_system']

def load(name):
    col = db[name]
    doc = col.find_one({"_id": "main_data"})
    return doc.get('data', {}) if doc else {}

def save(name, data):
    col = db[name]
    col.update_one({"_id": "main_data"}, {"$set": {"data": data}}, upsert=True)

def init_admin():
    if not load('admin'):
        save('admin', {"password": hashlib.sha256("admin1234".encode()).hexdigest()})
init_admin()

# ===================== 공통 기능 =====================
def get_attend_status():
    return load('attend_status').get('open', False)

def check_team_attendance(date):
    att = load('attendance').get(date, {})
    teams = load('teams')
    result = {}
    for tid, tdata in teams.items():
        members = tdata.get('members', [])
        if not members: result[tid] = False; continue
        result[tid] = all(m in att for m in members)
    return result

# ===================== HTML 템플릿 (디자인 복구) =====================
BASE_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#f0f2f5;color:#1a1a2e;min-height:100vh}
.container{max-width:500px;margin:0 auto;padding:20px}
.card{background:white;border-radius:16px;padding:24px;margin-bottom:16px;box-shadow:0 4px 15px rgba(0,0,0,0.08)}
h1{font-size:1.6rem;text-align:center;margin-bottom:20px;font-weight:800}
button{width:100%;padding:14px;border-radius:12px;border:none;font-size:1rem;font-weight:700;cursor:pointer;margin-bottom:10px;transition:.2s}
.btn-primary{background:linear-gradient(135deg,#2563eb,#7c3aed);color:#fff}
.btn-success{background:#059669;color:#fff}
.btn-danger{background:#dc2626;color:#fff}
.tag{display:inline-block;padding:4px 10px;border-radius:20px;font-size:.75rem;font-weight:600}
.tag-blue{background:#dbeafe;color:#1e40af}
input,textarea,select{width:100%;padding:12px;border-radius:10px;border:1px solid #ccc;margin-bottom:12px}
table{width:100%;border-collapse:collapse}
th,td{padding:10px;border-bottom:1px solid #eee;text-align:left;font-size:0.9rem}
</style>
"""

# (아래 라우트 함수들에 디자인을 입혀서 다시 구성합니다)
@app.route('/')
def index():
    return render_template_string(BASE_CSS + """
    <div class="container">
        <h1>정진:政進</h1>
        <div class="card" style="text-align:center">
            <a href="/attend"><button class="btn-primary">📋 출석체크</button></a>
            <a href="/notices"><button class="btn-success">📢 공지 & 미션</button></a>
            <a href="/scores"><button style="background:#d97706;color:white">🏆 팀 점수</button></a>
            <a href="/board"><button style="background:#8b5cf6;color:white">💬 자유게시판</button></a>
            <hr style="margin:15px 0; border:0; border-top:1px solid #eee">
            <a href="/admin/login"><button style="background:#e5e7eb;color:#6b7280;font-size:12px">🔐 관리자</button></a>
        </div>
    </div>
    """)

# --- [출석 기능] ---
@app.route('/attend')
def attend_page():
    return render_template_string(BASE_CSS + """
    <div class="container">
        <h1>📋 출석 체크</h1>
        <div class="card">
            <input id="sid" placeholder="학번"><input id="sname" placeholder="이름"><input id="steam" placeholder="팀 번호" type="number">
            <button class="btn-primary" onclick="attend()">✅ 출석하기</button>
            <div id="result"></div>
        </div>
        <a style="display:block;text-align:center;color:#666" href="/">← 뒤로가기</a>
    </div>
    <script>
    async function attend(){
        const sid=document.getElementById('sid').value;
        const sname=document.getElementById('sname').value;
        const steam=document.getElementById('steam').value;
        const r=await fetch('/api/attend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_id:sid,name:sname,team:steam})});
        const d=await r.json();
        document.getElementById('result').innerHTML='<p style="text-align:center;margin-top:10px;color:'+(d.ok?'green':'red')+'">'+d.msg+'</p>';
    }
    </script>
    """)

@app.route('/api/attend', methods=['POST'])
def api_attend():
    d = request.json
    if not get_attend_status(): return jsonify(ok=False, msg='⛔ 출석이 마감되었습니다.')
    sid, name, team = d.get('student_id',''), d.get('name',''), d.get('team','')
    students = load('students')
    if students and (sid not in students or students[sid]['name'] != name):
        return jsonify(ok=False, msg='❌ 등록된 학생 정보와 일치하지 않습니다.')
    
    today = datetime.date.today().isoformat()
    att = load('attendance')
    if today not in att: att[today] = {}
    if sid in att[today]: return jsonify(ok=False, msg='이미 출석하셨습니다.')
    
    att[today][sid] = {"name": name, "team": team, "time": datetime.datetime.now().strftime("%H:%M")}
    save('attendance', att)
    return jsonify(ok=True, msg=f'✅ {name}님 출석 완료!')

# --- [공지/미션 기능] ---
@app.route('/notices')
def notices():
    missions = load('missions')
    return render_template_string(BASE_CSS + """
    <div class="container">
        <h1>📢 공지 & 미션</h1>
        {% for mid, m in missions.items()|sort(reverse=True) %}
        <div class="card">
            <span class="tag tag-blue">{{m.type}}</span>
            <h2 style="margin-top:8px">{{m.title}}</h2>
            <p style="margin-top:8px; white-space:pre-wrap">{{m.desc}}</p>
            <p style="font-size:0.8rem; color:#999; margin-top:10px">{{m.created}}</p>
        </div>
        {% endfor %}
        <a style="display:block;text-align:center;color:#666" href="/">← 뒤로가기</a>
    </div>
    """, missions=missions)

# --- [팀 점수] ---
@app.route('/scores')
def scores():
    teams = load('teams')
    sorted_teams = sorted(teams.items(), key=lambda x: x[1].get('score',0), reverse=True)
    return render_template_string(BASE_CSS + """
    <div class="container">
        <h1>🏆 팀 점수 순위</h1>
        <div class="card">
            <table><tr><th>순위</th><th>팀</th><th>점수</th></tr>
            {% for tid, tdata in sorted_teams %}
            <tr><td>{{loop.index}}</td><td>{{tid}}팀</td><td><b>{{tdata.score}}점</b></td></tr>
            {% endfor %}
            </table>
        </div>
        <a style="display:block;text-align:center;color:#666" href="/">← 뒤로가기</a>
    </div>
    """, sorted_teams=sorted_teams)

# --- [자유게시판 (보안 강화)] ---
@app.route('/board')
def board():
    posts = sorted(load('board').items(), key=lambda x: x[0], reverse=True)
    return render_template_string(BASE_CSS + """
    <div class="container">
        <h1>💬 자유게시판</h1>
        <div class="card">
            <form method="POST" action="/board/write">
                <input name="student_id" placeholder="학번" required>
                <input name="author" placeholder="이름" required>
                <input name="title" placeholder="제목" required>
                <textarea name="content" placeholder="내용" rows="3" required></textarea>
                <button type="submit" class="btn-primary">✏️ 글쓰기</button>
            </form>
        </div>
        {% for pid, p in posts %}
        <div class="card">
            <h3>{{p.title}}</h3>
            <p style="font-size:0.8rem; color:#666">{{p.author}} | {{p.created}}</p>
            <p style="margin-top:10px; white-space:pre-wrap">{{p.content}}</p>
        </div>
        {% endfor %}
        <a style="display:block;text-align:center;color:#666" href="/">← 뒤로가기</a>
    </div>
    """, posts=posts)

@app.route('/board/write', methods=['POST'])
def board_write():
    sid, author = request.form['student_id'].strip(), request.form['author'].strip()
    title, content = request.form['title'].strip(), request.form['content'].strip()
    students = load('students')
    if not students or sid not in students or students[sid]['name'] != author:
        return "<script>alert('등록된 학번과 이름이 일치하지 않습니다.'); history.back();</script>"
    board_data = load('board')
    pid = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    board_data[pid] = {"author":author, "title":title, "content":content, "created":datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
    save('board', board_data)
    return redirect('/board')

# --- [관리자 기능] ---
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        if hashlib.sha256(request.form['pw'].encode()).hexdigest() == load('admin')['password']:
            session['admin'] = True; return redirect('/admin')
    return render_template_string(BASE_CSS + '<div class="container"><h1>🔐 관리자 로그인</h1><div class="card"><form method="POST"><input name="pw" type="password" placeholder="비밀번호"><button class="btn-primary">로그인</button></form></div></div>')

@app.route('/admin')
def admin_dash():
    if not session.get('admin'): return redirect('/admin/login')
    today = datetime.date.today().isoformat()
    att_count = len(load('attendance').get(today, {}))
    return render_template_string(BASE_CSS + """
    <div class="container">
        <h1>⚙️ 관리자 대시보드</h1>
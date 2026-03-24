import os, json, datetime, hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'subin-secret-1234'

# ===================== MongoDB 설정 =====================
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

# ===================== HTML 및 라우트 통합 =====================
@app.route('/')
def index():
    return render_template_string("""
    <style>body{font-family:sans-serif;text-align:center;padding:50px;background:#f0f2f5} .card{background:white;padding:30px;border-radius:15px;box-shadow:0 4px 10px rgba(0,0,0,0.1)} button{width:200px;padding:15px;margin:10px;cursor:pointer;border:none;border-radius:10px;background:#2563eb;color:white;font-weight:bold}</style>
    <div class="card"><h1>정진:政進 멘토멘티</h1>
    <a href="/attend"><button>📋 출석체크</button></a><br>
    <a href="/board"><button style="background:#8b5cf6">💬 자유게시판</button></a><br>
    <a href="/admin/login"><button style="background:#6b7280;width:100px;font-size:12px">관리자</button></a></div>
    """)

@app.route('/board')
def board():
    board_data = load('board')
    posts = sorted(board_data.items(), key=lambda x: x[0], reverse=True)
    return render_template_string("""
    <style>body{font-family:sans-serif;max-width:500px;margin:auto;padding:20px} .post{background:white;padding:15px;margin-bottom:15px;border-radius:10px;border:1px solid #ddd} input,textarea{width:100%;margin-bottom:10px;padding:10px}</style>
    <h1>💬 자유게시판</h1>
    <div class="post"><h3>새 글 쓰기</h3>
    <form method="POST" action="/board/write">
    <input name="student_id" placeholder="학번" required><input name="author" placeholder="이름" required>
    <input name="title" placeholder="제목" required><textarea name="content" placeholder="내용" required></textarea>
    <button type="submit">작성하기</button></form></div>
    {% for pid, p in posts %}<div class="post"><b>{{p.title}}</b><br><small>{{p.author}} | {{p.created}}</small><p>{{p.content}}</p></div>{% endfor %}
    <a href="/">← 메인으로</a>
    """, posts=posts)

@app.route('/board/write', methods=['POST'])
def board_write():
    sid, author = request.form['student_id'].strip(), request.form['author'].strip()
    title, content = request.form['title'].strip(), request.form['content'].strip()
    students = load('students')
    if not students or sid not in students or students[sid]['name'] != author:
        return "<script>alert('등록된 학번/이름이 아닙니다.'); history.back();</script>"
    board_data = load('board')
    pid = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    board_data[pid] = {"author": author, "title": title, "content": content, "created": datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
    save('board', board_data)
    return redirect('/board')

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        if hashlib.sha256(request.form['pw'].encode()).hexdigest() == load('admin')['password']:
            session['admin'] = True; return redirect('/admin')
    return '<h1>관리자 로그인</h1><form method="POST"><input name="pw" type="password"><button>로그인</button></form>'

@app.route('/admin')
def admin():
    if not session.get('admin'): return redirect('/admin/login')
    return '<h1>관리자 페이지</h1><a href="/admin/students">학생 관리</a><br><a href="/admin/logout">로그아웃</a>'

@app.route('/admin/students', methods=['GET','POST'])
def admin_students():
    if not session.get('admin'): return redirect('/admin/login')
    if request.method == 'POST':
        sid, name = request.form['sid'], request.form['name']
        s = load('students'); s[sid] = {"name": name}; save('students', s)
    return '<h1>학생 등록</h1><form method="POST"><input name="sid" placeholder="학번"><input name="name" placeholder="이름"><button>등록</button></form><br><a href="/admin">뒤로</a>'

@app.route('/admin/logout')
def logout(): session.pop('admin', None); return redirect('/')

@app.route('/keep-alive')
def keep_alive(): return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
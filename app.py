import os, json, datetime, hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'subin-secret-key-777'

MONGO_URI = "mongodb+srv://choesubin2018_db_user:bYLATrVP7kyeVrgo@cluster0.qmvit80.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['attendance_system']

def load(name):
    col = db[name]; doc = col.find_one({"_id": "main_data"})
    return doc.get('data', {}) if doc else {}

def save(name, data):
    col = db[name]; col.update_one({"_id": "main_data"}, {"$set": {"data": data}}, upsert=True)

if not load('admin'): save('admin', {"password": hashlib.sha256("admin1234".encode()).hexdigest()})

def get_status(): return load('attend_status').get('open', False)
CSS = "<style>*{box-sizing:border-box}body{font-family:sans-serif;background:#f0f2f5;padding:20px}.container{max-width:500px;margin:auto}.card{background:white;padding:20px;border-radius:15px;box-shadow:0 2px 10px rgba(0,0,0,0.1);margin-bottom:15px}button{width:100%;padding:12px;border:none;border-radius:10px;color:white;font-weight:bold;cursor:pointer;margin-bottom:8px}input,textarea{width:100%;padding:10px;margin-bottom:10px;border:1px solid #ddd;border-radius:8px}</style>"

@app.route('/')
def index():
    return render_template_string(CSS + '<div class="container"><h1>정진:政進</h1><div class="card"><a href="/attend"><button style="background:#2563eb">📋 출석체크</button></a><a href="/notices"><button style="background:#059669">📢 공지&미션</button></a><a href="/scores"><button style="background:#d97706">🏆 팀 점수</button></a><a href="/board"><button style="background:#8b5cf6">💬 자유게시판</button></a><hr><a href="/admin/login"><button style="background:#6b7280;font-size:12px">🔐 관리자</button></a></div></div>')

@app.route('/board')
def board():
    ps = sorted(load('board').items(), key=lambda x:x[0], reverse=True)
    return render_template_string(CSS + '<div class="container"><h1>💬 자유게시판</h1><div class="card"><form method="POST" action="/board/write"><input name="sid" placeholder="학번" required><input name="author" placeholder="이름" required><input name="title" placeholder="제목" required><textarea name="content" placeholder="내용" required></textarea><button style="background:#8b5cf6">✏️ 글쓰기</button></form></div>{% for id,p in ps %}<div class="card"><h3>{{p.title}}</h3><p style="font-size:0.8rem;color:#666">{{p.author}} | {{p.created}}</p><p>{{p.content}}</p></div>{% endfor %}<a href="/">← 뒤로</a></div>', ps=ps)

@app.route('/board/write', methods=['POST'])
def board_write():
    sid, name, title, cont = request.form['sid'], request.form['author'], request.form['title'], request.form['content']
    ss = load('students')
    if not ss or sid not in ss or ss[sid]['name'] != name: return "<script>alert('학번/이름 불일치');history.back();</script>"
    b = load('board'); pid = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    b[pid] = {"author":name, "title":title, "content":cont, "created":datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
    save('board', b); return redirect('/board')
@app.route('/attend')
def att_p():
    return render_template_string(CSS + '<div class="container"><h1>📋 출석체크</h1><div class="card"><input id="sid" placeholder="학번"><input id="nm" placeholder="이름"><input id="tm" placeholder="팀번호"><button style="background:#2563eb" onclick="at()">출석하기</button><div id="re"></div></div></div><script>async function at(){const r=await fetch("/api/at",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sid:document.getElementById("sid").value,nm:document.getElementById("nm").value,tm:document.getElementById("tm").value})});const d=await r.json();alert(d.msg)}</script>')

@app.route('/api/at', methods=['POST'])
def api_at():
    if not get_status(): return jsonify(msg="마감됨")
    d=request.json; sid,nm,tm=d['sid'],d['nm'],d['tm']
    ss=load('students')
    if not ss or sid not in ss or ss[sid]['name'] != nm: return jsonify(msg="정보불일치")
    a=load('attendance'); day=datetime.date.today().isoformat()
    if day not in a: a[day]={}
    if sid in a[day]: return jsonify(msg="이미 출석함")
    a[day][sid]={"name":nm,"team":tm,"time":datetime.datetime.now().strftime("%H:%M")}; save('attendance',a)
    return jsonify(msg="출석완료!")

@app.route('/notices')
def notices():
    ms = load('missions')
    return render_template_string(CSS + '<div class="container"><h1>📢 공지&미션</h1>{% for id,m in ms.items()|sort(reverse=True) %}<div class="card"><b>[{{m.type}}] {{m.title}}</b><p>{{m.desc}}</p></div>{% endfor %}<a href="/">← 뒤로</a></div>', ms=ms)

@app.route('/admin/login', methods=['GET','POST'])
def alog():
    if request.method=='POST':
        if hashlib.sha256(request.form['pw'].encode()).hexdigest()==load('admin')['password']: session['admin']=True; return redirect('/admin')
    return render_template_string(CSS+'<div class="container"><h1>🔐 관리자</h1><div class="card"><form method="POST"><input name="pw" type="password"><button style="background:#2563eb">로그인</button></form></div></div>')

@app.route('/admin')
def adm():
    if not session.get('admin'): return redirect('/admin/login')
    return render_template_string(CSS+'<div class="container"><h1>⚙️ 관리</h1><div class="card"><form method="POST" action="/admin/tg"><button style="background:#2563eb">출석 열기/닫기</button></form><a href="/admin/st"><button style="background:#059669">학생 등록</button></a><a href="/admin/logout"><button style="background:#dc2626">로그아웃</button></a></div></div>')

@app.route('/admin/tg', methods=['POST'])
def atg(): save('attend_status', {'open':not get_status()}); return redirect('/admin')

@app.route('/admin/st', methods=['GET','POST'])
def ast():
    if request.method=='POST':
        s=load('students'); s[request.form['sid']]={"name":request.form['nm']}; save('students',s)
    return render_template_string(CSS+'<div class="container"><h1>🧑‍🎓 학생등록</h1><div class="card"><form method="POST"><input name="sid" placeholder="학번"><input name="nm" placeholder="이름"><button style="background:#2563eb">등록</button></form></div><a href="/admin">뒤로</a></div>')

@app.route('/admin/logout')
def lout(): session.pop('admin',None); return redirect('/')

@app.route('/keep-alive')
def keep(): return "OK",200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
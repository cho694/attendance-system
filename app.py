import os, json, datetime, hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'subin-jeongjin-final-2026'

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

# ===================== 초기 설정 및 헬퍼 함수 =====================
def init_admin():
    a = load('admin')
    if not a:
        save('admin', {"password": hashlib.sha256("admin1234".encode()).hexdigest()})
init_admin()

def get_attend_status():
    return load('attend_status').get('open', False)

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

def check_auth():
    return 'student_id' in session or session.get('admin') is True

# ===================== HTML 템플릿 =====================
BASE_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:url('/static/bg.png') no-repeat center center fixed;background-size:cover;color:#1a1a2e;min-height:100vh}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(255,255,255,0.3);z-index:0}
.container{max-width:500px;margin:0 auto;padding:20px;position:relative;z-index:1}
.card{background:rgba(255,255,255,0.92);border-radius:16px;padding:24px;margin-bottom:16px;box-shadow:0 4px 24px rgba(0,0,0,.15);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.5)}
h1{font-size:1.6rem;text-align:center;margin-bottom:20px;color:#1a1a2e;font-weight:800;text-shadow:0 1px 2px rgba(255,255,255,0.8)}
h2{font-size:1.2rem;color:#1a1a2e;margin-bottom:12px;font-weight:700}
h3{font-size:1rem;color:#4b5563;margin-top:10px;margin-bottom:6px;font-weight:600}
input,select,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #ccc;background:rgba(255,255,255,0.95);color:#1a1a2e;margin-bottom:12px;font-size:1rem}
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
.history-row{font-size:0.85rem; color:#4b5563; background:#f3f4f6; border-radius:6px; padding:8px; margin-top:6px; border-left:3px solid #d97706;}
</style>
"""

STUDENT_LOGIN_HTML = BASE_CSS + """
<div class="container">
<h1>🎓 학생 로그인</h1>
<div class="card">
 <form method="POST" action="/login">
  <input name="student_id" placeholder="학번 입력" required />
  <input name="pw" type="password" placeholder="비밀번호 입력 (초기비번: 1234)" required />
  <button class="btn-primary" type="submit">로그인</button>
 </form>
 {% if error %}<div class="msg msg-err">{{error}}</div>{% endif %}
</div>
<a class="back" href="/">← 메인으로</a>
</div>
"""

INDEX_HTML = BASE_CSS + """
<div class="container">
<h1>정진:政進</h1>
<div class="card" style="text-align:center">
 {% if student_id or is_admin %}
    {% if student_id %}
      <div style="background:rgba(255,255,255,0.6); padding:12px; border-radius:12px; margin-bottom:15px; border:1px solid #e5e7eb;">
       <p style="font-weight:bold; color:#1a1a2e; margin-bottom:10px; font-size:1.1rem;">👤 {{student_name}}님 환영합니다!</p>
       <p style="font-size:1rem; color:#d97706; font-weight:bold; margin-bottom:10px;">🏆 내 개인 점수: {{my_score}}점</p>
       <form method="POST" action="/change_pw" style="display:flex; gap:6px; justify-content:center; margin-bottom:8px;">
        <input type="password" name="new_pw" placeholder="새 비밀번호 설정" style="width:60%; margin:0; padding:10px;" required>
        <button class="btn-sm btn-danger" style="margin:0;">비번변경</button>
       </form>
       <a href="/logout" style="display:inline-block; font-size:0.9rem; color:#dc2626; font-weight:bold;">[로그아웃]</a>
      </div>
    {% else %}
      <div style="background:rgba(255,255,255,0.6); padding:12px; border-radius:12px; margin-bottom:15px; border:1px solid #e5e7eb;">
       <p style="font-weight:bold; color:#1a1a2e; margin-bottom:10px; font-size:1.1rem;">👑 관리자 모드로 접속 중입니다.</p>
       <a href="/admin" style="display:inline-block; font-size:0.9rem; color:#2563eb; font-weight:bold;">[관리자 대시보드 가기]</a>
      </div>
    {% endif %}

    <a href="/attend"><button class="btn-primary" style="margin-bottom:10px">📋 출석하기</button></a>
    <a href="/notices"><button class="btn-primary" style="margin-bottom:10px;background:linear-gradient(135deg,#059669,#2563eb)">📢 공지 & 미션 확인</button></a>
    <a href="/scores"><button class="btn-primary" style="margin-bottom:10px;background:linear-gradient(135deg,#d97706,#dc2626)">🏆 점수 랭킹 및 내역</button></a>
    <a href="/board"><button class="btn-primary" style="margin-bottom:10px;background:linear-gradient(135deg,#8b5cf6,#ec4899)">💬 자유게시판</button></a>
 {% else %}
    <div style="padding:20px 0;">
       <p style="color:#4b5563; margin-bottom:20px; font-weight:bold; font-size:1.1rem;">서비스를 이용하려면 로그인이 필요합니다.</p>
       <a href="/login"><button class="btn-primary" style="margin-bottom:10px; background:linear-gradient(135deg,#3b82f6,#2563eb); font-size:1.1rem; padding:16px;">👤 학생 로그인</button></a>
    </div>
 {% endif %}
 <hr style="border-color:#e5e7eb;margin:16px 0">
 <a href="/admin/login"><button class="btn-sm" style="background:#e5e7eb;color:#6b7280">🔐 관리자 접속</button></a>
</div>
</div>
"""

ATTEND_HTML = BASE_CSS + """
<div class="container">
<h1>📋 출석 체크</h1>
<div class="card">
 <div id="status" style="margin-bottom:12px"></div>
 <input id="sid" placeholder="학번 입력" value="{{student_id}}" {% if student_id %}readonly style="background:#f3f4f6; color:#9ca3af;"{% endif %} />
 <input id="sname" placeholder="이름 입력" value="{{student_name}}" {% if student_name %}readonly style="background:#f3f4f6; color:#9ca3af;"{% endif %} />
 <input id="steam" placeholder="팀 번호 입력" type="number" min="1" value="{{student_team}}" {% if student_team %}readonly style="background:#f3f4f6; color:#9ca3af;"{% endif %} />
 <button class="btn-primary" onclick="attend()">✅ 출석하기</button>
 <div id="result"></div>
</div>
<a class="back" href="/">← 메인으로</a>
</div>
<script>
async function checkStatus(){
 const r=await fetch('/api/attend_status');
 const d=await r.json();
 if(!d.open) document.getElementById('status').innerHTML='<div class="msg msg-err">⛔ 현재 출석이 마감되었습니다</div>';
 else document.getElementById('status').innerHTML='<div class="msg msg-ok">✅ 출석이 열려있습니다</div>';
}
checkStatus();
async function attend(){
 const sid=document.getElementById('sid').value.trim();
 const sname=document.getElementById('sname').value.trim();
 const steam=document.getElementById('steam').value.trim();
 if(!sid||!sname||!steam){alert('모든 항목을 입력하세요');return}
 const r=await fetch('/api/attend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_id:sid,name:sname,team:steam})});
 const d=await r.json();
 document.getElementById('result').innerHTML=d.ok?'<div class="msg msg-ok">'+d.msg+'</div>':'<div class="msg msg-err">'+d.msg+'</div>';
}
</script>
"""

NOTICE_HTML = BASE_CSS + """
<div class="container">
<h1>📢 공지 & 미션</h1>
{% for mid, m in missions.items()|sort(attribute='1.created', reverse=True) %}
<div class="card">
 <span class="tag {% if m.type=='weekly' %}tag-blue{% elif m.type=='sudden' %}tag-red{% else %}tag-green{% endif %}">{{ '주간미션' if m.type=='weekly' else '돌발미션' if m.type=='sudden' else '공지' }}</span>
 {% if m.week %}<span class="tag tag-green">{{m.week}}주차</span>{% endif %}
 <h2 style="margin-top:8px">{{m.title}}</h2>
 <p style="color:#4b5563;margin-top:8px;white-space:pre-wrap">{{m.desc}}</p>
 <p style="color:#9ca3af;font-size:.8rem;margin-top:8px">{{m.created}}</p>
</div>
{% endfor %}
{% if not missions %}<div class="card"><p style="text-align:center;color:#9ca3af">등록된 공지가 없습니다.</p></div>{% endif %}
<a class="back" href="/">← 메인으로</a>
</div>
"""

SCORES_HTML = BASE_CSS + """
<div class="container">
<h1>🏆 랭킹 & 점수 내역</h1>

{% if student_id %}
<div class="card" style="border:2px solid #d97706;">
 <h2>📜 나의 점수 획득 내역</h2>
 <p style="font-weight:bold; color:#d97706; font-size:1.1rem; margin-bottom:8px;">현재 누적 점수: {{my_score}}점</p>
 {% if my_history %}
  {% for h in my_history|reverse %}
   <div class="history-row">
    <strong style="color:#1a1a2e;">[{{ '+' if h.point > 0 else '' }}{{h.point}}점]</strong> {{h.reason}} 
    <span style="color:#9ca3af; float:right; font-size:0.75rem; margin-top:2px;">{{h.date}}</span>
   </div>
  {% endfor %}
 {% else %}
  <p style="color:#9ca3af; font-size:0.9rem;">아직 획득한 개인 점수가 없습니다.</p>
 {% endif %}
</div>
{% endif %}

<div class="card">
 <h2>👥 팀 전체 랭킹 (팀 단위 점수)</h2>
 <table><tr><th>순위</th><th>팀</th><th>점수</th></tr>
 {% for tid, tdata in teams_sorted %}
  <tr>
   <td>{{loop.index}}</td>
   <td style="font-weight:bold;">{{tid}}팀</td>
   <td style="font-weight:700;color:#d97706">{{tdata.score|default(0)}}점</td>
  </tr>
 {% endfor %}
 </table>
</div>

<div class="card">
 <h2>👤 개인 점수 랭킹 (Top 10)</h2>
 <table><tr><th>순위</th><th>이름</th><th>소속팀</th><th>점수</th></tr>
 {% for sdata in students_sorted %}
  <tr>
   <td>{{loop.index}}</td>
   <td>{{sdata.name}}</td>
   <td style="color:#6b7280; font-size:0.8rem;">{{sdata.team}}팀</td>
   <td style="font-weight:700;color:#2563eb">{{sdata.score|default(0)}}점</td>
  </tr>
 {% endfor %}
 </table>
</div>
<a class="back" href="/">← 메인으로</a>
</div>
"""

BOARD_HTML = BASE_CSS + """
<div class="container">
<h1>💬 자유게시판</h1>
<div class="card">
<h2>새 글 작성</h2>
<form method="POST" action="/board/write">
 <input name="title" placeholder="제목" required />
 <textarea name="content" placeholder="내용" rows="4" required></textarea>
 {% if is_admin and not student_id %}
  <button class="btn-primary" type="submit" style="background:#dc2626">✏️ 관리자 권한으로 작성</button>
 {% else %}
  <button class="btn-primary" type="submit">✏️ 작성하기</button>
 {% endif %}
</form>
</div>
{% for pid, p in posts %}
<div class="card">
 <h2 style="margin-bottom:4px">{{p.title}}</h2>
 <p style="color:#6b7280;font-size:.8rem">{{p.author}} ({{p.student_id}}) · {{p.created}}</p>
 <p style="color:#1a1a2e;margin-top:8px;white-space:pre-wrap">{{p.content}}</p>
 {% if p.comments %}
 <div style="margin-top:12px">
  {% for c in p.comments %}
  <div class="comment">
   <span class="comment-author">{{c.author}} ({{c.student_id}})</span>
   <span class="comment-time"> · {{c.created}}</span>
   <p class="comment-content">{{c.content}}</p>
  </div>
  {% endfor %}
 </div>
 {% endif %}
 <form method="POST" action="/board/comment" style="margin-top:12px">
  <input type="hidden" name="post_id" value="{{pid}}"/>
  <div style="display:flex;gap:6px;flex-wrap:wrap">
   <input name="content" placeholder="댓글 입력" style="flex:1;min-width:120px" required />
   <button class="btn-sm btn-success" type="submit" style="margin:0">💬</button>
  </div>
 </form>
 {% if is_admin %}
 <form method="POST" action="/board/delete" style="margin-top:8px">
  <input type="hidden" name="post_id" value="{{pid}}"/>
  <button class="btn-sm btn-danger" type="submit">삭제</button>
 </form>
 {% endif %}
</div>
{% endfor %}
{% if not posts %}<div class="card"><p style="text-align:center;color:#9ca3af">아직 게시글이 없습니다.</p></div>{% endif %}
<a class="back" href="/">← 메인으로</a>
</div>
"""

ADMIN_LOGIN_HTML = BASE_CSS + """<div class="container"><h1>🔐 관리자 로그인</h1><div class="card"><form method="POST"><input name="pw" type="password" placeholder="관리자 비밀번호" /><button class="btn-primary" type="submit">로그인</button></form>{% if error %}<div class="msg msg-err">{{error}}</div>{% endif %}</div><a class="back" href="/">← 메인으로</a></div>"""
ADMIN_DASH_HTML = BASE_CSS + """<div class="container"><h1>⚙️ 관리자 대시보드</h1><div class="nav"><a href="/admin/attendance"><button class="btn-sm btn-primary">출석현황</button></a><a href="/admin/teams"><button class="btn-sm btn-success">팀관리</button></a><a href="/admin/students"><button class="btn-sm" style="background:#d97706;color:#fff">학생관리</button></a><a href="/admin/scores_manage"><button class="btn-sm" style="background:#8b5cf6;color:#fff">💯 점수관리</button></a><a href="/admin/missions"><button class="btn-sm" style="background:#7c3aed;color:#fff">공지/미션</button></a><a href="/board"><button class="btn-sm" style="background:#ec4899;color:#fff">게시판</button></a><a href="/admin/logout"><button class="btn-sm btn-danger">로그아웃</button></a></div><div class="card" style="text-align:center"><h2>🔒 출석 관리</h2><p style="margin-bottom:12px">현재 상태: {% if attend_open %}<span class="tag tag-green" style="font-size:1.1rem">✅ 출석 열림</span>{% else %}<span class="tag tag-red" style="font-size:1.1rem">⛔ 출석 닫힘</span>{% endif %}</p><form method="POST" action="/admin/attend_toggle">{% if attend_open %}<button class="btn-danger" style="width:60%">🔒 출석 마감하기</button>{% else %}<button class="btn-success" style="width:60%">🔓 출석 열기</button>{% endif %}</form></div><div class="card"><h2>📊 오늘의 요약 ({{today}})</h2><p>개인 출석: <b>{{att_count}}명</b></p><p>팀 출석 완료: <b>{{team_ok}}/{{team_total}}팀</b></p><p>등록된 학생: <b>{{student_count}}명</b></p></div><a class="back" href="/">← 메인으로</a></div>"""
ADMIN_SCORES_HTML = BASE_CSS + """
<div class="container">
<h1>💯 점수 관리 (개인/팀 분리)</h1>
{% if msg %}<div class="msg msg-ok">{{msg}}</div>{% endif %}
<div class="card">
 <h2>👥 팀 점수 부여 (팀 전체)</h2>
 <form method="POST" action="/admin/scores_manage/team">
  <input name="team_id" placeholder="팀 번호 (예: 1)" required />
  <input name="point" type="number" placeholder="부여할 점수 (감점은 - 기호)" required />
  <input name="reason" placeholder="사유 (예: 단체미션 우승)" required />
  <button class="btn-success" type="submit">팀 점수 적용</button>
 </form>
</div>
<div class="card" style="border:1px solid #2563eb;">
 <h2>👤 개인 점수 부여 (특정 학생)</h2>
 <form method="POST" action="/admin/scores_manage/personal">
  <input name="student_id" placeholder="학생 학번" required />
  <input name="point" type="number" placeholder="부여할 점수 (감점은 - 기호)" required />
  <input name="reason" placeholder="사유 (예: 발표 우수)" required />
  <button class="btn-primary" type="submit">개인 점수 적용</button>
 </form>
</div>
<a class="back" href="/admin">← 대시보드</a>
</div>
"""
ADMIN_ATT_HTML = BASE_CSS + """<div class="container"><h1>📋 출석 현황</h1><div class="card"><label style="color:#6b7280">날짜 선택</label><input type="date" id="datesel" value="{{today}}" onchange="location.href='/admin/attendance?date='+this.value" /></div><div class="card"><h2>{{sel_date}} 출석 ({{att_list|length}}명)</h2><table><tr><th>학번</th><th>이름</th><th>팀</th><th>시간</th><th>삭제</th></tr>{% for sid, info in att_list.items() %}<tr><td>{{sid}}</td><td>{{info.name}}</td><td>{{info.team}}팀</td><td>{{info.time}}</td><td><form method="POST" action="/admin/attendance/delete" style="margin:0"><input type="hidden" name="date" value="{{sel_date}}"/><input type="hidden" name="student_id" value="{{sid}}"/><button class="btn-sm btn-danger" type="submit" style="margin:0;padding:4px 8px">X</button></form></td></tr>{% endfor %}</table>{% if att_list %}<form method="POST" action="/admin/attendance/clear" style="margin-top:12px"><input type="hidden" name="date" value="{{sel_date}}"/><button class="btn-danger" type="submit" onclick="return confirm('{{sel_date}} 출석 기록을 전체 삭제하시겠습니까?')">🗑️ {{sel_date}} 전체 삭제</button></form>{% endif %}</div><div class="card"><h2>팀 출석 현황</h2><table><tr><th>팀</th><th>상태</th></tr>{% for tid, ok in team_att.items()|sort %}<tr><td>{{tid}}팀</td><td>{% if ok %}<span class="tag tag-green">전원출석</span>{% else %}<span class="tag tag-red">미완료</span>{% endif %}</td></tr>{% endfor %}</table></div><a class="back" href="/admin">← 대시보드</a></div>"""
ADMIN_TEAMS_HTML = BASE_CSS + """<div class="container"><h1>👥 팀 관리</h1><div class="card"><h2>팀 추가/수정</h2><form method="POST" action="/admin/teams/save"><input name="team_id" placeholder="팀 번호" type="number" min="1" /><input name="members" placeholder="팀원 학번 (쉼표 구분: 20210001,20210002)" /><button class="btn-primary" type="submit">저장</button></form></div>{% for tid, tdata in teams.items()|sort(attribute='0') %}<div class="card"><h2>{{tid}}팀 <span style="color:#d97706">{{tdata.score|default(0)}}점</span></h2><p style="color:#6b7280">팀원: {{tdata.members|join(', ')}}</p><form method="POST" action="/admin/teams/delete" style="margin-top:8px"><input type="hidden" name="team_id" value="{{tid}}"/><button class="btn-sm btn-danger" type="submit">삭제</button></form></div>{% endfor %}<a class="back" href="/admin">← 대시보드</a></div>"""
ADMIN_STUDENTS_HTML = BASE_CSS + """<div class="container"><h1>🧑‍🎓 학생 명단 관리</h1><div class="card"><h2>학생 개별 추가</h2><form method="POST" action="/admin/students/add"><input name="student_id" placeholder="학번" /><input name="name" placeholder="이름" /><input name="team" placeholder="팀 번호" type="number" min="1" /><button class="btn-primary" type="submit">추가</button></form></div><div class="card"><h2>학생 일괄 추가</h2><p style="color:#6b7280;font-size:.85rem;margin-bottom:8px">한 줄에 하나씩: 학번,이름,팀번호</p><form method="POST" action="/admin/students/bulk"><textarea name="bulk" rows="6" placeholder="20210001,홍길동,1&#10;20210002,김철수,1&#10;20210003,이영희,2"></textarea><button class="btn-success" type="submit">일괄 추가</button></form></div>{% if msg %}<div class="msg {% if msg_ok %}msg-ok{% else %}msg-err{% endif %}">{{msg}}</div>{% endif %}<div class="card"><h2>등록된 학생 ({{students|length}}명)</h2><table><tr><th>학번</th><th>이름</th><th>팀</th><th>관리</th></tr>{% for sid, info in students.items()|sort(attribute='0') %}<tr><td>{{sid}}</td><td>{{info.name}}</td><td>{{info.team}}팀</td><td><form method="POST" action="/admin/students/reset_pw" style="margin:0; display:inline-block;"><input type="hidden" name="student_id" value="{{sid}}"/><button class="btn-sm" type="submit" style="margin:0;padding:4px 6px; background:#f59e0b; color:white; border:none; border-radius:4px; cursor:pointer;" onclick="return confirm('{{info.name}} 학생의 비밀번호를 1234로 초기화할까요?');">비번초기화</button></form><form method="POST" action="/admin/students/delete" style="margin:0; display:inline-block;"><input type="hidden" name="student_id" value="{{sid}}"/><button class="btn-sm btn-danger" type="submit" style="margin:0;padding:4px 8px" onclick="return confirm('정말 삭제하시겠습니까?');">X</button></form></td></tr>{% endfor %}</table></div><div class="card"><h2>⚠️ 전체 삭제</h2><form method="POST" action="/admin/students/clear"><button class="btn-danger" type="submit" onclick="return confirm('정말 전체 삭제하시겠습니까?')">🗑️ 학생 명단 전체 삭제</button></form></div><a class="back" href="/admin">← 대시보드</a></div>"""
ADMIN_MISSIONS_HTML = BASE_CSS + """<div class="container"><h1>📢 공지사항 관리</h1><div class="card"><h2>새 공지 등록</h2><form method="POST" action="/admin/missions/add"><select name="type"><option value="notice">일반 공지</option><option value="weekly">주간 미션</option><option value="sudden">돌발 미션</option></select><input name="week" placeholder="주차 (선택, 예: 1)" /><input name="title" placeholder="제목" /><textarea name="desc" placeholder="내용" rows="4"></textarea><button class="btn-primary" type="submit">등록</button></form></div>{% for mid, m in missions.items()|sort(attribute='1.created', reverse=True) %}<div class="card"><span class="tag {% if m.type=='weekly' %}tag-blue{% elif m.type=='sudden' %}tag-red{% else %}tag-green{% endif %}">{{ '주간미션' if m.type=='weekly' else '돌발미션' if m.type=='sudden' else '공지' }}</span><h2 style="margin-top:8px">{{m.title}}</h2><p style="color:#4b5563;white-space:pre-wrap">{{m.desc}}</p><form method="POST" action="/admin/missions/delete" style="margin-top:8px"><input type="hidden" name="mission_id" value="{{mid}}"/><button class="btn-sm btn-danger" type="submit">삭제</button></form></div>{% endfor %}<a class="back" href="/admin">← 대시보드</a></div>"""

# ===================== 학생 라우트 =====================
@app.route('/')
def index():
    my_score = 0
    if session.get('student_id'):
        students = load('students')
        my_score = students.get(session['student_id'], {}).get('score', 0)
        
    return render_template_string(INDEX_HTML, 
                                  student_id=session.get('student_id'), 
                                  student_name=session.get('student_name'),
                                  is_admin=session.get('admin'),
                                  my_score=my_score)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        sid = request.form['student_id'].strip()
        pw = request.form['pw'].strip()
        students = load('students')
        
        if sid in students and students[sid].get('pw') == hashlib.sha256(pw.encode()).hexdigest():
            session['student_id'] = sid
            session['student_name'] = students[sid]['name']
            session['student_team'] = str(students[sid]['team'])
            return redirect('/')
        error = '학번 또는 비밀번호가 틀립니다.'
    return render_template_string(STUDENT_LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/change_pw', methods=['POST'])
def change_pw():
    if not check_auth(): return redirect('/login')
    sid = session['student_id']
    new_pw = request.form['new_pw'].strip()
    students = load('students')
    if sid in students:
        students[sid]['pw'] = hashlib.sha256(new_pw.encode()).hexdigest()
        save('students', students)
    return "<script>alert('비밀번호가 변경되었습니다. 다시 로그인해주세요.'); location.href='/logout';</script>"

@app.route('/attend')
def attend_page():
    if not check_auth(): return redirect('/login')
    return render_template_string(ATTEND_HTML, student_id=session.get('student_id', ''), student_name=session.get('student_name', ''), student_team=session.get('student_team', ''))

@app.route('/api/attend_status')
def api_attend_status():
    return jsonify(open=get_attend_status())

@app.route('/api/attend', methods=['POST'])
def api_attend():
    if not check_auth(): return jsonify(ok=False, msg='로그인이 필요합니다.')
    d = request.json
    if not get_attend_status(): return jsonify(ok=False, msg='⛔ 현재 출석이 마감되었습니다.')
    
    sid, name, team = d.get('student_id',''), d.get('name',''), d.get('team','')
    if not all([sid, name, team]): return jsonify(ok=False, msg='모든 항목을 입력하세요')
    
    students = load('students')
    if students:
        if sid not in students: return jsonify(ok=False, msg='❌ 등록되지 않은 학번입니다.')
        s = students[sid]
        if s['name'] != name: return jsonify(ok=False, msg='❌ 학번과 이름이 일치하지 않습니다.')
        if str(s['team']) != str(team): return jsonify(ok=False, msg='❌ 팀 번호가 일치하지 않습니다.')
        
    today = datetime.date.today().isoformat()
    att = load('attendance')
    if today not in att: att[today] = {}
    if sid in att[today]: return jsonify(ok=False, msg=f'{name}님은 이미 출석했습니다 ({att[today][sid]["time"]})')
    
    att[today][sid] = {"name": name, "team": str(team), "time": datetime.datetime.now().strftime("%H:%M:%S")}
    save('attendance', att)
    
    teams = load('teams')
    team_msg = ""
    if str(team) in teams:
        members = teams[str(team)].get('members', [])
        present = [m for m in members if m in att[today]]
        if len(present) == len(members) and members:
            team_msg = f"\n🎉 {team}팀 전원 출석 완료!"
        else:
            team_msg = f"\n👥 {team}팀: {len(present)}/{len(members)}명 출석"
            
    return jsonify(ok=True, msg=f'✅ {name}님 출석 완료!{team_msg}')

@app.route('/notices')
def notices():
    if not check_auth(): return redirect('/login')
    return render_template_string(NOTICE_HTML, missions=load('missions'))

@app.route('/scores')
def scores():
    if not check_auth(): return redirect('/login')
    
    sid = session.get('student_id')
    students = load('students')
    teams = load('teams')
    
    my_score = 0
    my_history = []
    if sid and sid in students:
        my_score = students[sid].get('score', 0)
        my_history = students[sid].get('history', [])
        
    # 개인 Top 10 추출
    students_list = [{'id': k, 'name': v['name'], 'team': v['team'], 'score': v.get('score',0)} for k, v in students.items()]
    students_sorted = sorted(students_list, key=lambda x: x['score'], reverse=True)[:10]
    
    # 팀 랭킹
    teams_sorted = sorted(teams.items(), key=lambda x: x[1].get('score',0), reverse=True)
    
    return render_template_string(SCORES_HTML, student_id=sid, my_score=my_score, my_history=my_history, teams_sorted=teams_sorted, students_sorted=students_sorted)

@app.route('/board')
def board():
    if not check_auth(): return redirect('/login')
    board_data = load('board')
    posts = sorted(board_data.items(), key=lambda x: x[1].get('created',''), reverse=True)
    return render_template_string(BOARD_HTML, posts=posts, is_admin=session.get('admin'), student_id=session.get('student_id'))

@app.route('/board/write', methods=['POST'])
def board_write():
    if not check_auth(): return redirect('/login')
    sid = session.get('student_id', 'admin')
    author = session.get('student_name', '관리자')
    title, content = request.form['title'].strip(), request.form['content'].strip()
    if not all([title, content]): return redirect('/board')
    board_data = load('board')
    pid = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    board_data[pid] = {"author": author, "student_id": sid, "title": title, "content": content, "created": datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), "comments": []}
    save('board', board_data)
    return redirect('/board')

@app.route('/board/comment', methods=['POST'])
def board_comment():
    if not check_auth(): return redirect('/login')
    pid = request.form['post_id']
    sid = session.get('student_id', 'admin')
    author = session.get('student_name', '관리자')
    content = request.form['content'].strip()
    if not content: return redirect('/board')
    board_data = load('board')
    if pid in board_data:
        board_data[pid]['comments'].append({"author": author, "student_id": sid, "content": content, "created": datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})
        save('board', board_data)
    return redirect('/board')

@app.route('/board/delete', methods=['POST'])
def board_delete():
    if not session.get('admin'): return redirect('/board')
    board_data = load('board')
    board_data.pop(request.form['post_id'], None)
    save('board', board_data)
    return redirect('/board')

# ===================== 관리자 라우트 =====================
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        if load('admin')['password'] == hashlib.sha256(request.form['pw'].encode()).hexdigest():
            session['admin'] = True
            return redirect('/admin')
        return render_template_string(ADMIN_LOGIN_HTML, error='비밀번호가 틀렸습니다')
    return render_template_string(ADMIN_LOGIN_HTML, error=None)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/')

def require_admin():
    return session.get('admin') is True

@app.route('/admin')
def admin_dash():
    if not require_admin(): return redirect('/admin/login')
    today = datetime.date.today().isoformat()
    att, ta, students = load('attendance').get(today, {}), check_team_attendance(today), load('students')
    return render_template_string(ADMIN_DASH_HTML, today=today, att_count=len(att), team_ok=sum(ta.values()), team_total=len(ta), attend_open=get_attend_status(), student_count=len(students))

@app.route('/admin/attend_toggle', methods=['POST'])
def admin_attend_toggle():
    if not require_admin(): return redirect('/admin/login')
    set_attend_status(not get_attend_status())
    return redirect('/admin')

@app.route('/admin/attendance')
def admin_att():
    if not require_admin(): return redirect('/admin/login')
    sel = request.args.get('date', datetime.date.today().isoformat())
    return render_template_string(ADMIN_ATT_HTML, today=datetime.date.today().isoformat(), sel_date=sel, att_list=load('attendance').get(sel, {}), team_att=check_team_attendance(sel))

@app.route('/admin/attendance/delete', methods=['POST'])
def admin_att_delete():
    if not require_admin(): return redirect('/admin/login')
    date, sid = request.form['date'], request.form['student_id']
    att = load('attendance')
    if date in att and sid in att[date]: del att[date][sid]; save('attendance', att)
    return redirect(f'/admin/attendance?date={date}')

@app.route('/admin/attendance/clear', methods=['POST'])
def admin_att_clear():
    if not require_admin(): return redirect('/admin/login')
    date = request.form['date']
    att = load('attendance')
    if date in att: del att[date]; save('attendance', att)
    return redirect(f'/admin/attendance?date={date}')

@app.route('/admin/teams')
def admin_teams():
    if not require_admin(): return redirect('/admin/login')
    return render_template_string(ADMIN_TEAMS_HTML, teams=load('teams'))

@app.route('/admin/teams/save', methods=['POST'])
def admin_teams_save():
    if not require_admin(): return redirect('/admin/login')
    tid, members = str(request.form['team_id']), [m.strip() for m in request.form['members'].split(',') if m.strip()]
    teams = load('teams')
    if tid in teams: teams[tid]['members'] = members
    else: teams[tid] = {"members": members, "score": 0, "history": []}
    save('teams', teams)
    return redirect('/admin/teams')

@app.route('/admin/teams/delete', methods=['POST'])
def admin_teams_delete():
    if not require_admin(): return redirect('/admin/login')
    teams = load('teams')
    teams.pop(str(request.form['team_id']), None)
    save('teams', teams)
    return redirect('/admin/teams')

@app.route('/admin/students')
def admin_students():
    if not require_admin(): return redirect('/admin/login')
    return render_template_string(ADMIN_STUDENTS_HTML, students=load('students'), msg=request.args.get('msg', ''), msg_ok=request.args.get('ok', '0') == '1')

@app.route('/admin/students/add', methods=['POST'])
def admin_students_add():
    if not require_admin(): return redirect('/admin/login')
    sid, name, team = request.form['student_id'].strip(), request.form['name'].strip(), request.form['team'].strip()
    if not all([sid, name, team]): return redirect('/admin/students?msg=입력오류&ok=0')
    students = load('students')
    students[sid] = {"name": name, "team": str(team), "pw": hashlib.sha256("1234".encode()).hexdigest(), "score": 0, "history": []}
    save('students', students)
    return redirect(f'/admin/students?msg={name} 추가됨&ok=1')

@app.route('/admin/students/bulk', methods=['POST'])
def admin_students_bulk():
    if not require_admin(): return redirect('/admin/login')
    bulk, students, count = request.form['bulk'].strip(), load('students'), 0
    if not bulk: return redirect('/admin/students?msg=내용없음&ok=0')
    for line in bulk.split('\n'):
        parts = [p.strip() for p in line.split(',')]
        if len(parts) == 3:
            students[parts[0]] = {"name": parts[1], "team": str(parts[2]), "pw": hashlib.sha256("1234".encode()).hexdigest(), "score": 0, "history": []}
            count += 1
    save('students', students)
    return redirect(f'/admin/students?msg={count}명 일괄 추가 완료&ok=1')

@app.route('/admin/students/reset_pw', methods=['POST'])
def admin_students_reset_pw():
    if not require_admin(): return redirect('/admin/login')
    sid, students = request.form['student_id'], load('students')
    if sid in students: students[sid]['pw'] = hashlib.sha256("1234".encode()).hexdigest(); save('students', students)
    return redirect(f'/admin/students?msg=비밀번호 초기화됨&ok=1')

@app.route('/admin/students/delete', methods=['POST'])
def admin_students_delete():
    if not require_admin(): return redirect('/admin/login')
    students = load('students')
    students.pop(request.form['student_id'], None)
    save('students', students)
    return redirect('/admin/students')

@app.route('/admin/students/clear', methods=['POST'])
def admin_students_clear():
    if not require_admin(): return redirect('/admin/login')
    save('students', {})
    return redirect('/admin/students?msg=전체 삭제 완료&ok=1')

@app.route('/admin/missions')
def admin_missions():
    if not require_admin(): return redirect('/admin/login')
    return render_template_string(ADMIN_MISSIONS_HTML, missions=load('missions'))

@app.route('/admin/missions/add', methods=['POST'])
def admin_missions_add():
    if not require_admin(): return redirect('/admin/login')
    missions, mid = load('missions'), datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    missions[mid] = {"title": request.form['title'], "desc": request.form['desc'], "type": request.form['type'], "week": request.form.get('week',''), "created": datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
    save('missions', missions)
    return redirect('/admin/missions')

@app.route('/admin/missions/delete', methods=['POST'])
def admin_missions_delete():
    if not require_admin(): return redirect('/admin/login')
    missions = load('missions')
    missions.pop(request.form['mission_id'], None)
    save('missions', missions)
    return redirect('/admin/missions')

# ===================== 관리자 점수 관리 =====================
@app.route('/admin/scores_manage')
def admin_scores_manage():
    if not require_admin(): return redirect('/admin/login')
    return render_template_string(ADMIN_SCORES_HTML, msg=request.args.get('msg', ''))

@app.route('/admin/scores_manage/team', methods=['POST'])
def admin_scores_team():
    if not require_admin(): return redirect('/admin/login')
    tid, point, reason = str(request.form['team_id']).strip(), int(request.form['point']), request.form['reason'].strip()
    teams = load('teams')
    if tid in teams:
        teams[tid]['score'] = teams[tid].get('score', 0) + point
        if 'history' not in teams[tid]: teams[tid]['history'] = []
        teams[tid]['history'].append({'point': point, 'reason': reason, 'date': datetime.date.today().isoformat()})
        save('teams', teams)
        return redirect(f'/admin/scores_manage?msg={tid}팀에 {point}점이 적용되었습니다.')
    return redirect('/admin/scores_manage?msg=존재하지 않는 팀 번호입니다.')

@app.route('/admin/scores_manage/personal', methods=['POST'])
def admin_scores_personal():
    if not require_admin(): return redirect('/admin/login')
    sid, point, reason = request.form['student_id'].strip(), int(request.form['point']), request.form['reason'].strip()
    students = load('students')
    if sid in students:
        students[sid]['score'] = students[sid].get('score', 0) + point
        if 'history' not in students[sid]: students[sid]['history'] = []
        students[sid]['history'].append({'point': point, 'reason': reason, 'date': datetime.date.today().isoformat()})
        save('students', students)
        return redirect(f'/admin/scores_manage?msg={students[sid]["name"]} 학생에게 {point}점이 적용되었습니다.')
    return redirect('/admin/scores_manage?msg=등록되지 않은 학생(학번)입니다.')

# ===================== 서버 잠들기 방지용 =====================
@app.route('/keep-alive')
def keep_alive():
    return "I am awake!", 200

# ===================== 실행 =====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
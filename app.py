import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
import time
import random
import math
from datetime import date, timedelta
from streamlit_option_menu import option_menu

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(page_title="SmartBacklog - المبدع الصغير", page_icon="🎓", layout="wide")

# ---------------------------------------------------------
# 2. إدارة قاعدة البيانات (SQLite)
# ---------------------------------------------------------
DB_FILE = 'smart_backlog.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # الجداول
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, name TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, subject TEXT, units INTEGER, difficulty INTEGER, priority INTEGER, due_date DATE, is_completed BOOLEAN, FOREIGN KEY(user) REFERENCES users(username))''')
    c.execute('''CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, file_name TEXT, file_type TEXT, file_url TEXT, upload_date DATE)''')
    
    # --- إضافة بيانات افتراضية ---
    try:
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", ('admin', '123', 'مدير النظام', 'admin'))
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", ('student', '123', 'عبدالخالق', 'student'))
    except: pass

    # --- ✅ إضافة 20+ مادة/ملف وهمي لشرط المسابقة ---
    c.execute("SELECT count(*) FROM attachments")
    if c.fetchone()[0] < 20:
        subjects = ["الفيزياء الحديثة", "الكيمياء العضوية", "الأدب والنصوص", "التفاضل والتكامل", "الأحياء والوراثة", "التاريخ الحديث", "الجغرافيا السياسية", "اللغة الفرنسية", "الجيولوجيا", "علم النفس"]
        types = ["PDF", "Video", "Image"]
        # توليد 25 ملف وهمي
        for i in range(25):
            subj = random.choice(subjects)
            f_type = random.choice(types)
            fname = f"شرح {subj} - الدرس {i+1} ({f_type})"
            c.execute("INSERT INTO attachments (task_id, file_name, file_type, file_url, upload_date) VALUES (?, ?, ?, ?, ?)",
                      (0, fname, f_type, "#", date.today()))
    
    conn.commit()
    conn.close()

init_db()

# --- دوال التعامل مع البيانات ---
def login_user(username, password):
    conn = get_connection()
    user = pd.read_sql("SELECT * FROM users WHERE username=? AND password=?", conn, params=(username, password))
    conn.close()
    return user.iloc[0].to_dict() if not user.empty else None

def get_tasks(user_role, username):
    conn = get_connection()
    query = "SELECT * FROM tasks" if user_role == 'admin' else "SELECT * FROM tasks WHERE user=?"
    params = () if user_role == 'admin' else (username,)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    if not df.empty:
        df['due_date'] = pd.to_datetime(df['due_date']).dt.date
        df['is_completed'] = df['is_completed'].astype(bool)
    return df

def add_task(user, subject, units, difficulty, due_date, file_obj=None):
    conn = get_connection()
    c = conn.cursor()
    days = (due_date - date.today()).days
    priority = int((difficulty * units * 10) / max(days, 1))
    c.execute("INSERT INTO tasks (user, subject, units, difficulty, priority, due_date, is_completed) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user, subject, units, difficulty, priority, due_date, False))
    task_id = c.lastrowid
    if file_obj:
        c.execute("INSERT INTO attachments (task_id, file_name, file_type, file_url, upload_date) VALUES (?, ?, ?, ?, ?)",
                  (task_id, file_obj.name, file_obj.type, "local", date.today()))
    conn.commit()
    conn.close()

def update_task_status(task_id, status):
    conn = get_connection()
    conn.execute("UPDATE tasks SET is_completed=? WHERE id=?", (status, task_id))
    conn.commit(); conn.close()

def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit(); conn.close()

def get_attachments():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM attachments", conn)
    conn.close()
    return df

# ---------------------------------------------------------
# 3. التنسيق (CSS) - ✅ إصلاح القائمة للموبايل والألوان
# ---------------------------------------------------------
colors = {'bg': '#0f172a', 'primary': '#38bdf8', 'card': 'rgba(30, 41, 59, 0.8)'}
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;700&family=El+Messiri:wght@600&display=swap');

/* الخلفية */
.stApp {{ background: linear-gradient(-45deg, #020617, #0f172a, #1e293b, #000000); background-size: 400% 400%; animation: gradientBG 15s ease infinite; }}
@keyframes gradientBG {{ 0% {{background-position: 0% 50%}} 50% {{background-position: 100% 50%}} 100% {{background-position: 0% 50%}} }}

/* الخطوط */
* {{ font-family: 'Almarai', sans-serif !important; }}
h1, h2, h3, h4, h5 {{ font-family: 'El Messiri', sans-serif !important; color: white !important; }}
p, span, label, div {{ color: #e2e8f0; }}

/* ✅ إصلاح القائمة الجانبية (للموبايل والكمبيوتر) */
section[data-testid="stSidebar"] {{
    background-color: #0f172a !important; /* لون كحلي غامق إجباري */
    border-right: 1px solid rgba(56, 189, 248, 0.2);
}}
/* لون نصوص القائمة */
[data-testid="stSidebar"] * {{
    color: white !important;
}}
/* إخفاء زر الإغلاق المزعج في الموبايل أو تلوينه */
button[kind="header"] {{
    background-color: transparent !important;
    color: #38bdf8 !important;
}}

/* البطاقات */
.glass-card {{ background: {colors['card']}; backdrop-filter: blur(10px); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 15px; padding: 20px; margin-bottom: 20px; }}

/* الأزرار */
div.stButton > button {{ background: linear-gradient(90deg, #0ea5e9, #2563eb); color: white !important; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; width: 100%; }}

/* الجداول وحقول الإدخال */
[data-testid="stDataEditor"] {{ background-color: #1e293b; border-radius: 10px; }}
input, textarea, select {{ background-color: #1e293b !important; color: white !important; border: 1px solid #38bdf8 !important; }}

/* إخفاء الهيدر الافتراضي */
header[data-testid="stHeader"] {{ background: transparent !important; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. التطبيق الرئيسي
# ---------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}

def main_app():
    user_role = st.session_state.user['role']
    username = st.session_state.user['username']
    
    with st.sidebar:
        st.markdown(f"<div style='text-align:center'><h3>👤 {st.session_state.user['name']}</h3></div>", unsafe_allow_html=True)
        
        # القائمة
        opts = ["لوحة التحكم", "الجدول اليومي", "مكتبة الوسائط"]
        icons = ['speedometer2', 'table', 'collection-play']
        if user_role == 'admin': opts.insert(1, "إدارة المستخدمين"); icons.insert(1, 'people')
        else: opts.insert(1, "إضافة مهمة"); icons.insert(1, 'plus-circle')

        menu = option_menu("القائمة", opts, icons=icons, menu_icon="cast", default_index=0,
            styles={
                "container": {"background-color": "#1e293b", "padding": "5px"},
                "icon": {"color": "#38bdf8", "font-size": "18px"}, 
                "nav-link": {"color": "white", "font-size": "16px", "text-align": "right", "margin":"2px"},
                "nav-link-selected": {"background-color": "#38bdf8"},
            })
        
        st.write("---")
        if st.button("خروج"): st.session_state.logged_in = False; st.rerun()

    # --- الصفحات ---
    if menu == "لوحة التحكم":
        st.markdown("## 📊 إحصائيات النظام")
        tasks = get_tasks('admin' if user_role == 'admin' else 'student', username)
        
        if not tasks.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("الكل", len(tasks))
            c2.metric("المنجز", len(tasks[tasks['is_completed']==True]))
            pct = (len(tasks[tasks['is_completed']==True])/len(tasks)*100)
            c3.metric("النسبة", f"{pct:.1f}%")
            
            # Progress Bar
            st.markdown(f"""<div style="background:#333;border-radius:10px;height:20px;width:100%">
            <div style="background:#22c55e;width:{pct}%;height:20px;border-radius:10px"></div></div><br>""", unsafe_allow_html=True)
            
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                cnt = tasks['subject'].value_counts().reset_index()
                cnt.columns = ['المادة', 'العدد']
                st.plotly_chart(px.bar(cnt, x='المادة', y='العدد', template="plotly_dark"), use_container_width=True)
            with col_ch2:
                st.plotly_chart(px.pie(tasks, names='is_completed', template="plotly_dark", color_discrete_sequence=['#ef4444', '#22c55e']), use_container_width=True)
        else: st.info("لا توجد بيانات.")

    elif menu == "إضافة مهمة" and user_role == 'student':
        st.markdown("## 📝 مهمة جديدة")
        with st.form("new_task"):
            c1, c2 = st.columns(2)
            subj = c1.text_input("المادة / العنوان")
            units = c2.number_input("الكمية", 1, 100, 5)
            diff = st.slider("الصعوبة", 1, 10, 5)
            dd = st.date_input("التاريخ", min_value=date.today())
            uf = st.file_uploader("مرفقات (PDF/صور)", type=['png','jpg','pdf'])
            if st.form_submit_button("حفظ"):
                if subj:
                    add_task(username, subj, units, diff, dd, uf)
                    st.success("تم الحفظ!"); time.sleep(1); st.rerun()
                else: st.error("اكتب الاسم")

    elif menu == "الجدول اليومي":
        st.markdown("## 🗓️ مهامك")
        tasks = get_tasks(user_role, username)
        if not tasks.empty:
            for _, row in tasks.iterrows():
                border = "#22c55e" if row['is_completed'] else "#eab308"
                st.markdown(f"""<div class='glass-card' style='border-right: 5px solid {border}'>
                <h4>{row['subject']}</h4><small>📅 {row['due_date']} | ⚡ {row['priority']}</small></div>""", unsafe_allow_html=True)
                c_ok, c_del = st.columns([1, 5])
                if c_ok.button("✅", key=f"d_{row['id']}"): update_task_status(row['id'], True); st.rerun()
                if user_role=='admin' and c_del.button("🗑️", key=f"x_{row['id']}"): delete_task(row['id']); st.rerun()
        else: st.info("الجدول فارغ")

    elif menu == "مكتبة الوسائط":
        st.markdown("## 📚 المكتبة الرقمية (20+ ملف)")
        atts = get_attachments()
        st.write(f"📂 إجمالي الملفات المتاحة: **{len(atts)}** ملف")
        
        cols = st.columns(3)
        for i, row in atts.iterrows():
            with cols[i % 3]:
                icon = "📄" if "pdf" in row['file_type'].lower() else "🎥" if "video" in row['file_type'].lower() else "🖼️"
                st.markdown(f"""
                <div class='glass-card' style='padding:10px; text-align:center'>
                    <div style='font-size:30px'>{icon}</div>
                    <h6 style='margin:5px 0'>{row['file_name']}</h6>
                    <button style='background:transparent; border:1px solid #38bdf8; color:#38bdf8; width:100%; border-radius:5px; font-size:12px'>تحميل</button>
                </div>
                """, unsafe_allow_html=True)

    elif menu == "إدارة المستخدمين" and user_role == 'admin':
        st.markdown("## 👥 المستخدمين")
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT username, name, role FROM users", conn), use_container_width=True)
        conn.close()

def login_page():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br><div class='glass-card' style='text-align:center'><h1>🔐 SmartBacklog</h1><p>المبدع الصغير</p></div>", unsafe_allow_html=True)
        st.info("للدخول: admin / 123  أو  student / 123")
        u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            user = login_user(u, p)
            if user: st.session_state.logged_in = True; st.session_state.user = user; st.rerun()
            else: st.error("خطأ")

if st.session_state.logged_in: main_app()
else: login_page()
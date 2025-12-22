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
# 2. قاعدة البيانات (مع حقن البيانات الكثيفة)
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
    
    # --- المستخدمين ---
    try:
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", ('admin', '123', 'مدير النظام', 'admin'))
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", ('student', '123', 'عبدالخالق', 'student'))
    except: pass

    # --- ✅ حقن 50 مهمة لتجميل الرسوم البيانية ---
    c.execute("SELECT count(*) FROM tasks")
    if c.fetchone()[0] < 10: # لو المهام قليلة، ضيف مهام وهمية كتير
        subjects = ["الفيزياء الكهربية", "الكيمياء العضوية", "النحو والصرف", "Calculus", "الأحياء", "التاريخ", "JGeography", "French", "Geology", "English Skills"]
        statuses = [True, False, False, True, False] # تنويع بين المنجز وغير المنجز
        
        for i in range(50):
            subj = random.choice(subjects)
            is_done = random.choice(statuses)
            prio = random.randint(40, 100)
            diff = random.randint(3, 10)
            # تواريخ متنوعة (ماضي ومستقبل)
            d_date = date.today() + timedelta(days=random.randint(-5, 20))
            
            c.execute("INSERT INTO tasks (user, subject, units, difficulty, priority, due_date, is_completed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ('student', subj, random.randint(1, 10), diff, prio, d_date, is_done))
            
            # اضافة بعض لـ admin للمقارنة
            if i % 5 == 0:
                c.execute("INSERT INTO tasks (user, subject, units, difficulty, priority, due_date, is_completed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ('admin', subj, random.randint(1, 10), diff, prio, d_date, is_done))

    # --- حقن ملفات الوسائط ---
    c.execute("SELECT count(*) FROM attachments")
    if c.fetchone()[0] < 20:
        file_types = ["PDF", "Video", "Image"]
        for i in range(25):
            fname = f"ملخص {random.choice(['فيزياء', 'كيمياء', 'عربي'])} - {i+1}"
            ftype = random.choice(file_types)
            c.execute("INSERT INTO attachments (task_id, file_name, file_type, file_url, upload_date) VALUES (?, ?, ?, ?, ?)",
                      (0, fname, ftype, "#", date.today()))
    
    conn.commit()
    conn.close()

init_db()

# --- دوال البيانات ---
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
    if file_obj:
        task_id = c.lastrowid
        c.execute("INSERT INTO attachments (task_id, file_name, file_type, file_url, upload_date) VALUES (?, ?, ?, ?, ?)",
                  (task_id, file_obj.name, file_obj.type, "local", date.today()))
    conn.commit(); conn.close()

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
# 3. التنسيق (CSS) - Dark Cyberpunk Mode
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

/* القائمة الجانبية */
section[data-testid="stSidebar"] {{ background-color: #0f172a !important; border-right: 1px solid rgba(56, 189, 248, 0.2); }}
[data-testid="stSidebar"] * {{ color: white !important; }}

/* البطاقات والمدخلات */
.glass-card {{ background: {colors['card']}; backdrop-filter: blur(10px); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 15px; padding: 20px; margin-bottom: 20px; }}
[data-testid="stDataEditor"] {{ background-color: #1e293b; border-radius: 10px; }}
input, textarea, select {{ background-color: #1e293b !important; color: white !important; border: 1px solid #38bdf8 !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
div.stButton > button {{ background: linear-gradient(90deg, #0ea5e9, #2563eb); color: white !important; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; width: 100%; }}
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

    # --- لوحة التحكم (الدشملة الجديدة) ---
    if menu == "لوحة التحكم":
        st.markdown("## 📊 مركز القيادة")
        tasks = get_tasks('admin' if user_role == 'admin' else 'student', username)
        
        if not tasks.empty:
            # 1. كروت الأرقام (Metrics)
            c1, c2, c3, c4 = st.columns(4)
            total = len(tasks)
            done = len(tasks[tasks['is_completed']==True])
            pending = total - done
            high_prio = len(tasks[tasks['priority'] > 80])
            
            c1.metric("إجمالي المهام", total, "📚")
            c2.metric("تم الإنجاز", done, "✅")
            c3.metric("قيد الانتظار", pending, "⏳")
            c4.metric("أولوية قصوى", high_prio, "🔥")
            
            st.markdown("<br>", unsafe_allow_html=True)

            # 2. الرسوم البيانية المتطورة (Modern Charts)
            col_ch1, col_ch2 = st.columns([3, 2])
            
            with col_ch1:
                st.markdown("#### 📉 توزيع المواد الدراسية")
                # تجميع البيانات
                subj_counts = tasks['subject'].value_counts().reset_index().head(10)
                subj_counts.columns = ['المادة', 'العدد']
                # رسم بار شارت ملون
                fig_bar = px.bar(
                    subj_counts, x='المادة', y='العدد', 
                    color='العدد', 
                    template="plotly_dark",
                    color_continuous_scale='Bluyl' # تدرج أزرق نيون
                )
                fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_ch2:
                st.markdown("#### 🎯 نسبة الإنجاز")
                status_counts = tasks['is_completed'].map({True:'مكتمل', False:'جاري العمل'}).value_counts().reset_index()
                status_counts.columns = ['الحالة', 'العدد']
                # رسم دونت شارت (Donut Chart) بدل الفطيرة العادية
                fig_pie = px.pie(
                    status_counts, values='العدد', names='الحالة', 
                    hole=0.6, # تحويلها لدونت
                    template="plotly_dark", 
                    color_discrete_sequence=['#22c55e', '#ef4444'] # أخضر وأحمر
                )
                fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True)

        else: st.info("جاري تحميل البيانات الذكية...")

    elif menu == "إضافة مهمة" and user_role == 'student':
        st.markdown("## 📝 مهمة جديدة")
        with st.form("new_task"):
            c1, c2 = st.columns(2)
            subj = c1.text_input("المادة")
            units = c2.number_input("الكمية", 1, 100, 5)
            diff = st.slider("الصعوبة", 1, 10, 5)
            dd = st.date_input("التاريخ", min_value=date.today())
            uf = st.file_uploader("مرفق", type=['png','jpg','pdf'])
            if st.form_submit_button("حفظ"):
                if subj: add_task(username, subj, units, diff, dd, uf); st.success("تم!"); time.sleep(1); st.rerun()
                else: st.error("اكتب الاسم")

    elif menu == "الجدول اليومي":
        st.markdown("## 🗓️ جدول المهام")
        tasks = get_tasks(user_role, username)
        if not tasks.empty:
            # ترتيب المهام
            tasks = tasks.sort_values(by=['is_completed', 'due_date'], ascending=[True, True])
            
            # --- إصلاح الخطأ السابق Reset Index ---
            tasks = tasks.reset_index(drop=True)
            
            # عرض الجدول التفاعلي
            edited_df = st.data_editor(
                tasks,
                column_config={
                    "is_completed": st.column_config.CheckboxColumn("حالة", width="small"),
                    "subject": st.column_config.TextColumn("المهمة", width="medium"),
                    "priority": st.column_config.ProgressColumn("الأهمية", min_value=0, max_value=100),
                    "due_date": st.column_config.DateColumn("التاريخ"),
                    "id": None, "user": None, "units": None, "difficulty": None # إخفاء أعمدة النظام
                },
                column_order=["is_completed", "subject", "due_date", "priority"],
                disabled=["subject", "priority", "due_date"], # السماح بتعديل الـ Checkbox فقط
                hide_index=True,
                use_container_width=True,
                key="tasks_editor"
            )
            
            # زر الحفظ المجمع
            if st.button("💾 حفظ التعديلات"):
                conn = get_connection()
                # تحديث الحالات المتغيرة فقط
                for i, row in edited_df.iterrows():
                    # مقارنة الحالة الجديدة بالقديمة (يمكن تحسينها ولكن هذا بسيط وفعال)
                    original_status = tasks.iloc[i]['is_completed']
                    if row['is_completed'] != original_status:
                        conn.execute("UPDATE tasks SET is_completed=? WHERE id=?", (row['is_completed'], tasks.iloc[i]['id']))
                conn.commit()
                conn.close()
                st.toast("تم تحديث الجدول بنجاح!", icon="✅")
                time.sleep(1)
                st.rerun()
                
        else: st.info("الجدول فارغ")

    elif menu == "مكتبة الوسائط":
        st.markdown("## 📚 المكتبة (20+ ملف)")
        atts = get_attachments()
        cols = st.columns(4)
        for i, row in atts.iterrows():
            with cols[i % 4]:
                icon = "📄" if "pdf" in row['file_type'].lower() else "🎥"
                st.markdown(f"<div class='glass-card' style='text-align:center; padding:10px'><h2 style='margin:0'>{icon}</h2><small>{row['file_name']}</small></div>", unsafe_allow_html=True)

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
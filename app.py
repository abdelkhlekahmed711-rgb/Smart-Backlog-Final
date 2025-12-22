import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
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
# 2. قاعدة البيانات (SQLite) - تخزين دائم
# ---------------------------------------------------------
DB_FILE = 'smart_backlog.db'

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # إنشاء الجداول
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, name TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, subject TEXT, units INTEGER, difficulty INTEGER, priority INTEGER, due_date DATE, is_completed BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, file_name TEXT, file_type TEXT, upload_date DATE)''')
    
    # --- إضافة بيانات افتراضية (Seeding) ---
    try:
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", ('admin', '123', 'مدير النظام', 'admin'))
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", ('student', '123', 'عبدالخالق', 'student'))
    except: pass

    # --- حقن بيانات المسابقة (20+ ملف ومهمة) ---
    c.execute("SELECT count(*) FROM attachments")
    if c.fetchone()[0] < 20:
        subjects = ["الفيزياء", "الكيمياء", "العربي", "الإنجليزي", "الجيولوجيا"]
        for i in range(25):
            subj = random.choice(subjects)
            # إضافة مهام
            c.execute("INSERT INTO tasks (user, subject, units, difficulty, priority, due_date, is_completed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ('student', f"مذاكرة {subj} - الدرس {i+1}", 5, 5, random.randint(40, 100), date.today()+timedelta(days=i), random.choice([0, 1])))
            # إضافة مرفقات
            c.execute("INSERT INTO attachments (task_id, file_name, file_type, upload_date) VALUES (?, ?, ?, ?)",
                      (0, f"ملف شرح {subj} {i+1}.pdf", "PDF", date.today()))
    
    conn.commit()
    conn.close()

init_db()

# --- دوال التعامل مع البيانات ---
def login_user(u, p):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM users WHERE username=? AND password=?", conn, params=(u, p))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else None

def get_tasks(role, user):
    conn = get_connection()
    q = "SELECT * FROM tasks" if role == 'admin' else "SELECT * FROM tasks WHERE user=?"
    p = () if role == 'admin' else (user,)
    df = pd.read_sql(q, conn, params=p)
    conn.close()
    if not df.empty:
        df['due_date'] = pd.to_datetime(df['due_date']).dt.date
        df['is_completed'] = df['is_completed'].astype(bool)
    return df

def add_task_db(user, subj, units, diff, date):
    conn = get_connection()
    prio = int((diff * units * 10) / max((date - date.today()).days, 1))
    conn.execute("INSERT INTO tasks (user, subject, units, difficulty, priority, due_date, is_completed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (user, subj, units, diff, prio, date, False))
    conn.commit(); conn.close()

def update_status(id, status):
    conn = get_connection()
    conn.execute("UPDATE tasks SET is_completed=? WHERE id=?", (status, id))
    conn.commit(); conn.close()

def get_files():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM attachments", conn)
    conn.close()
    return df

# ---------------------------------------------------------
# 3. التنسيق والوظائف المساعدة
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;700&display=swap');
* { font-family: 'Almarai', sans-serif !important; }
.stApp { background-color: #0f172a; color: white; }
.glass-card { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 15px; padding: 20px; margin-bottom: 20px; }
h1, h2, h3 { color: white !important; }
/* القائمة الجانبية */
section[data-testid="stSidebar"] { background-color: #020617 !important; }
section[data-testid="stSidebar"] span { color: white !important; }
/* الجداول */
[data-testid="stDataEditor"] { background-color: #1e293b; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# دالة شريط الدوبامين (رجعتها عشانك)
def render_progress(pct):
    color, emoji = ("#ef4444", "😟") if pct < 30 else ("#eab308", "😐") if pct < 70 else ("#22c55e", "🤩")
    st.markdown(f"""
    <div style="margin-bottom:15px">
        <div style="display:flex;justify-content:space-between;color:white;font-weight:bold">
            <span>نسبة الإنجاز {emoji}</span><span>{pct:.1f}%</span>
        </div>
        <div style="background:rgba(255,255,255,0.1);border-radius:10px;height:12px">
            <div style="background:{color};width:{pct}%;height:12px;border-radius:10px;transition:width 0.5s"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. التطبيق
# ---------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}

def main():
    user = st.session_state.user
    
    with st.sidebar:
        st.header(f"👤 {user['name']}")
        menu = option_menu("القائمة", ["لوحة التحكم", "الجدول اليومي", "غرفة الإنقاذ", "المكتبة"], 
            icons=['speedometer2', 'table', 'life-preserver', 'collection'], 
            menu_icon="cast", default_index=0,
            styles={"container": {"background-color": "#1e293b"}, "nav-link": {"color": "white"}})
        
        st.write("---")
        if st.button("خروج"): st.session_state.logged_in = False; st.rerun()

    # --- 1. لوحة التحكم (العملية) ---
    if menu == "لوحة التحكم":
        st.title("📊 مركز القيادة")
        tasks = get_tasks(user['role'], user['username'])
        
        if not tasks.empty:
            done = len(tasks[tasks['is_completed']==True])
            total = len(tasks)
            pct = (done/total*100) if total > 0 else 0
            
            # 1. شريط الدوبامين (أول حاجة في الوش)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_progress(pct)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 2. الأرقام
            c1, c2, c3 = st.columns(3)
            c1.metric("المهام", total)
            c2.metric("المنجز", done)
            c3.metric("المتبقي", total - done)
            
            # 3. الرسوم البيانية (شيك وبسيط)
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("توزيع المواد")
                cnt = tasks['subject'].apply(lambda x: x.split('-')[0]).value_counts().reset_index() # تجميع حسب المادة
                cnt.columns = ['المادة', 'العدد']
                st.plotly_chart(px.bar(cnt, x='المادة', y='العدد', template="plotly_dark", color='العدد'), use_container_width=True)
            with g2:
                st.subheader("الحالة")
                st.plotly_chart(px.pie(tasks, names='is_completed', template="plotly_dark", hole=0.5, color_discrete_sequence=['#ef4444', '#22c55e']), use_container_width=True)

    # --- 2. الجدول اليومي (فيه Priority Bar) ---
    elif menu == "الجدول اليومي":
        st.title("🗓️ مهامك اليومية")
        tasks = get_tasks(user['role'], user['username'])
        
        if not tasks.empty:
            # ترتيب حسب الحالة ثم الأولوية
            tasks = tasks.sort_values(by=['is_completed', 'priority'], ascending=[True, False]).reset_index(drop=True)
            
            edited = st.data_editor(
                tasks,
                column_config={
                    "is_completed": st.column_config.CheckboxColumn("تم", width="small"),
                    "subject": st.column_config.TextColumn("المهمة", width="large"),
                    "priority": st.column_config.ProgressColumn("الأهمية 🔥", min_value=0, max_value=100, format="%f"),
                    "due_date": st.column_config.DateColumn("التاريخ"),
                    "id": None, "user": None, "units": None, "difficulty": None
                },
                column_order=["is_completed", "subject", "priority", "due_date"],
                disabled=["subject", "priority", "due_date"],
                hide_index=True,
                use_container_width=True
            )
            
            if st.button("حفظ التغييرات 💾"):
                conn = get_connection()
                for i, row in edited.iterrows():
                    conn.execute("UPDATE tasks SET is_completed=? WHERE id=?", (row['is_completed'], row['id']))
                conn.commit(); conn.close()
                st.success("تم الحفظ!"); time.sleep(0.5); st.rerun()
        else: st.info("مفيش مهام، روح لغرفة الإنقاذ!")

    # --- 3. غرفة الإنقاذ ---
    elif menu == "غرفة الإنقاذ":
        st.title("🚑 إضافة وتفتيت المهام")
        with st.form("rescue"):
            c1, c2 = st.columns(2)
            subj = c1.text_input("اسم المادة")
            num = c2.number_input("العدد", 1, 50, 5)
            diff = st.slider("الأهمية/الصعوبة", 1, 10, 5)
            date_end = st.date_input("موعد الانتهاء")
            if st.form_submit_button("توزيع المهام"):
                days = (date_end - date.today()).days
                quota = math.ceil(num / max(days, 1))
                for i in range(min(days, num)): # توزيع بسيط
                    add_task_db(user['username'], f"{subj} - جزء {i+1}", 1, diff, date.today()+timedelta(days=i))
                st.success(f"تم إضافة {num} مهام للجدول!"); time.sleep(1); st.rerun()

    # --- 4. المكتبة (شرط الـ 20 ملف) ---
    elif menu == "المكتبة":
        st.title("📚 مكتبة الوسائط")
        files = get_files()
        st.write(f"عدد الملفات المتاحة: **{len(files)}** ملف")
        
        cols = st.columns(3)
        for i, row in files.iterrows():
            with cols[i%3]:
                st.markdown(f"""
                <div class='glass-card' style='text-align:center; padding:10px'>
                    <h3>📄</h3>
                    <small>{row['file_name']}</small><br>
                    <button style='background:transparent;border:1px solid #38bdf8;color:#38bdf8;border-radius:5px;width:100%'>تحميل</button>
                </div>
                """, unsafe_allow_html=True)

# صفحة الدخول
def login():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><div class='glass-card' style='text-align:center'><h1>🔐 SmartBacklog</h1></div>", unsafe_allow_html=True)
        u = st.text_input("المستخدم"); p = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            user = login_user(u, p)
            if user: st.session_state.logged_in = True; st.session_state.user = user; st.rerun()
            else: st.error("خطأ")

if st.session_state.logged_in: main()
else: login()
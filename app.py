import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import time
import random
import math
import requests
from datetime import date, timedelta
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(page_title="SmartBacklog - المبدع الصغير", page_icon="🎓", layout="wide")

# ---------------------------------------------------------
# 2. قاعدة البيانات (SQLite) - (نفس المنطق الثابت)
# ---------------------------------------------------------
DB_FILE = 'smart_backlog_v4.db'

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, name TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, subject TEXT, units INTEGER, difficulty INTEGER, priority INTEGER, due_date DATE, is_completed BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT, file_type TEXT, file_content BLOB, is_real BOOLEAN, upload_date DATE)''')
    
    try:
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", ('admin', '123', 'مدير النظام', 'admin'))
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", ('student', '123', 'عبدالخالق', 'student'))
    except: pass

    # حقن بيانات وهمية للمسابقة (للمنظر)
    c.execute("SELECT count(*) FROM attachments")
    if c.fetchone()[0] < 20:
        subjects = ["الفيزياء", "الكيمياء", "العربي", "الإنجليزي"]
        types = ["PDF", "Image"]
        for i in range(25):
            subj = random.choice(subjects)
            c.execute("INSERT INTO attachments (file_name, file_type, file_content, is_real, upload_date) VALUES (?, ?, ?, ?, ?)",
                      (f"ملف {subj} {i+1}", random.choice(types), None, False, date.today()))
    conn.commit(); conn.close()

init_db()

# --- دوال البيانات ---
def register_user(username, password, name):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, password, name, 'student'))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def login_user(username, password):
    conn = get_connection()
    user = pd.read_sql("SELECT * FROM users WHERE username=? AND password=?", conn, params=(username, password))
    conn.close()
    return user.iloc[0].to_dict() if not user.empty else None

def get_tasks(user_role, username):
    conn = get_connection()
    q = "SELECT * FROM tasks" if user_role == 'admin' else "SELECT * FROM tasks WHERE user=?"
    p = () if user_role == 'admin' else (username,)
    df = pd.read_sql(q, conn, params=p)
    conn.close()
    if not df.empty:
        df['due_date'] = pd.to_datetime(df['due_date']).dt.date
        df['is_completed'] = df['is_completed'].astype(bool)
    return df

def add_task_db(user, subj, units, diff, d_date):
    conn = get_connection()
    prio = int((diff * units * 10) / max((d_date - date.today()).days, 1))
    conn.execute("INSERT INTO tasks (user, subject, units, difficulty, priority, due_date, is_completed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (user, subj, units, diff, prio, d_date, False))
    conn.commit(); conn.close()

def upload_file_db(name, type, content):
    conn = get_connection()
    conn.execute("INSERT INTO attachments (file_name, file_type, file_content, is_real, upload_date) VALUES (?, ?, ?, ?, ?)",
                 (name, type, content, True, date.today()))
    conn.commit(); conn.close()

def get_files():
    conn = get_connection()
    df = pd.read_sql("SELECT id, file_name, file_type, is_real, upload_date FROM attachments", conn)
    conn.close()
    return df

def get_real_file_content(file_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT file_content, file_name FROM attachments WHERE id=?", (file_id,))
    data = c.fetchone()
    conn.close()
    return data

def delete_user_db(username):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE username=?", (username,))
    conn.execute("DELETE FROM tasks WHERE user=?", (username,))
    conn.commit(); conn.close()

@st.cache_data
def load_lottie(url):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# ---------------------------------------------------------
# 3. التنسيق (CSS) - (نفس التصميم الإبداعي المحافظ عليه)
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;700&family=El+Messiri:wght@600&display=swap');

.stApp {
    background: linear-gradient(-45deg, #020617, #0f172a, #1e293b, #000000);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}
@keyframes gradientBG {
    0% {background-position: 0% 50%}
    50% {background-position: 100% 50%}
    100% {background-position: 0% 50%}
}

* { font-family: 'Almarai', sans-serif !important; }
h1, h2, h3 { font-family: 'El Messiri', sans-serif !important; color: white !important; }

header[data-testid="stHeader"] { background: transparent !important; backdrop-filter: blur(5px); z-index: 100; }
[data-testid="stDecoration"] { display: none; }

section[data-testid="stSidebar"] { background-color: #020617 !important; border-right: 1px solid rgba(56, 189, 248, 0.1); }
section[data-testid="stSidebar"] * { color: white !important; }
button[kind="header"] { background: transparent !important; color: #38bdf8 !important; }

/* تحسين الأزرار */
div.stButton > button {
    background: linear-gradient(90deg, #0ea5e9, #2563eb);
    color: white !important; border: none;
    padding: 12px 24px; border-radius: 12px;
    font-weight: bold; width: 100%;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
    transition: transform 0.2s, box-shadow 0.2s;
}
div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(14, 165, 233, 0.6); }

/* البطاقات */
.glass-card {
    background: rgba(30, 41, 59, 0.75);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}
.metric-card {
    text-align: center; border-right: 1px solid rgba(255,255,255,0.1);
}

/* المدخلات */
input, .stTextInput > div > div > input, .stDateInput > div > div > input {
    background-color: rgba(15, 23, 42, 0.8) !important;
    color: white !important;
    border: 1px solid #38bdf8 !important;
    border-radius: 10px !important;
}
.stSelectbox > div > div > div {
    background-color: rgba(15, 23, 42, 0.8) !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. التطبيق الرئيسي
# ---------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}

def render_progress(pct):
    color, emoji = ("#ef4444", "😟") if pct < 30 else ("#eab308", "😐") if pct < 70 else ("#22c55e", "🤩")
    st.markdown(f"""<div style="margin-bottom:15px"><div style="display:flex;justify-content:space-between;color:white;font-weight:bold"><span>إنجازك {emoji}</span><span>{pct:.1f}%</span></div><div style="background:rgba(255,255,255,0.1);border-radius:10px;height:12px"><div style="background:{color};width:{pct}%;height:12px;border-radius:10px;transition:width 0.5s"></div></div></div>""", unsafe_allow_html=True)

def main_app():
    user = st.session_state.user
    role = user['role']
    
    with st.sidebar:
        st.markdown(f"<div style='text-align:center; margin-bottom:20px'><h3>👤 {user['name']}</h3><span style='color:#38bdf8; font-weight:bold'>{role.upper()}</span></div>", unsafe_allow_html=True)
        opts = ["لوحة التحكم", "الجدول اليومي", "غرفة الإنقاذ", "المكتبة"]
        icons = ['speedometer2', 'table', 'life-preserver', 'collection']
        if role == 'admin': opts.insert(1, "إدارة المستخدمين"); icons.insert(1, "people")
        
        menu = option_menu("القائمة", opts, icons=icons, menu_icon="cast", default_index=0, 
            styles={
                "container": {"background-color": "#020617"}, 
                "nav-link": {"color": "white", "font-size": "16px"},
                "nav-link-selected": {"background-color": "#38bdf8", "color": "white"},
            })
        
        st.write("---"); 
        if st.button("تسجيل خروج"): st.session_state.logged_in = False; st.rerun()

    if menu == "لوحة التحكم":
        st.title("📊 مركز القيادة")
        tasks = get_tasks(role, user['username'])
        if not tasks.empty:
            done = len(tasks[tasks['is_completed']==True]); total = len(tasks); pct = (done/total*100) if total > 0 else 0
            st.markdown('<div class="glass-card">', unsafe_allow_html=True); render_progress(pct)
            c1, c2, c3 = st.columns(3); c1.metric("الكل", total); c2.metric("تم", done); c3.metric("باقي", total - done); st.markdown('</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1: st.subheader("توزيع المواد"); cnt = tasks['subject'].apply(lambda x: x.split('-')[0]).value_counts().reset_index(); cnt.columns = ['المادة', 'العدد']; st.plotly_chart(px.bar(cnt, x='المادة', y='العدد', template="plotly_dark", color='العدد'), use_container_width=True)
            with col2: st.subheader("حالة المهام"); st.plotly_chart(px.pie(tasks, names='is_completed', template="plotly_dark", hole=0.5, color_discrete_sequence=['#ef4444', '#22c55e']), use_container_width=True)
        else: st.info("ابدأ بإضافة مهام.")

    elif menu == "الجدول اليومي":
        st.title("🗓️ إدارة المهام الذكية")
        tasks = get_tasks(role, user['username'])
        
        if not tasks.empty:
            # --- ميزة 1: إحصائية سريعة لليوم ---
            today_tasks = tasks[tasks['due_date'] == date.today()]
            today_count = len(today_tasks)
            today_done = len(today_tasks[today_tasks['is_completed']==True])
            
            st.markdown(f"""
            <div class='glass-card' style='display:flex; justify-content:space-around; align-items:center; padding:15px'>
                <div>📅 <b>مهام اليوم:</b> {today_count}</div>
                <div>✅ <b>منجز اليوم:</b> {today_done}</div>
                <div>🔥 <b>التركيز:</b> عالي</div>
            </div>
            """, unsafe_allow_html=True)

            # --- ميزة 2: الفلاتر (جعل الأزرار حقيقية ومفيدة) ---
            col_filter, col_space = st.columns([2, 4])
            with col_filter:
                filter_option = st.selectbox("🌪️ تصفية المهام:", ["عرض الكل", "المهام المعلقة (Pending)", "المهام المنجزة (Done)"])

            # تطبيق الفلتر
            if filter_option == "المهام المعلقة (Pending)":
                tasks = tasks[tasks['is_completed'] == False]
            elif filter_option == "المهام المنجزة (Done)":
                tasks = tasks[tasks['is_completed'] == True]

            # ترتيب وعرض الجدول
            tasks = tasks.sort_values(by=['is_completed', 'priority'], ascending=[True, False]).reset_index(drop=True)
            
            edited = st.data_editor(
                tasks,
                column_config={
                    "is_completed": st.column_config.CheckboxColumn("إنجاز", width="small"),
                    "subject": st.column_config.TextColumn("تفاصيل المهمة", width="large"),
                    "priority": st.column_config.ProgressColumn("الأهمية 🔥", min_value=0, max_value=100, format="%f"),
                    "due_date": st.column_config.DateColumn("تاريخ التنفيذ"),
                    "id": None, "user": None, "units": None, "difficulty": None
                },
                column_order=["is_completed", "subject", "priority", "due_date"],
                disabled=["subject", "priority", "due_date"],
                hide_index=True,
                use_container_width=True,
                key="tasks_editor"
            )
            
            # زر حفظ حقيقي
            if st.button("💾 حفظ التحديثات الآن"):
                conn = get_connection()
                changes_count = 0
                for i, row in edited.iterrows():
                    # تحديث الحالة فقط
                    conn.execute("UPDATE tasks SET is_completed=? WHERE id=?", (row['is_completed'], row['id']))
                    changes_count += 1
                conn.commit(); conn.close()
                if changes_count > 0:
                    st.toast("تم حفظ تقدمك بنجاح! عاش يا بطل 💪", icon="✅")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("جدولك نظيف! اذهب لغرفة الإنقاذ لإضافة خطة جديدة.")

    elif menu == "غرفة الإنقاذ":
        st.title("🚑 غرفة عمليات الإنقاذ (AI Planner)")
        
        st.markdown("""
        <div class='glass-card'>
            <p>💡 هذا النظام يستخدم خوارزمية ذكية لتقسيم المواد المتراكمة بناءً على الوقت المتاح وصعوبة المادة.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("rescue_form"):
            c1, c2 = st.columns(2)
            with c1:
                subj = st.text_input("📚 اسم المادة المتراكمة", placeholder="مثال: الفيزياء الكهربية")
                num = st.number_input("🔢 عدد الدروس/الوحدات", 1, 100, 5)
            with c2:
                diff = st.slider("😰 مستوى الصعوبة/القلق (1-10)", 1, 10, 7)
                d_date = st.date_input("🗓️ أريد الانتهاء قبل تاريخ:", min_value=date.today() + timedelta(days=1))
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("🚀 تفعيل خطة الإنقاذ")

            if submit:
                if subj:
                    # محاكاة التفكير (Visual Effect)
                    progress_text = "جاري تحليل الوقت المتاح..."
                    my_bar = st.progress(0, text=progress_text)
                    for percent_complete in range(100):
                        time.sleep(0.01)
                        my_bar.progress(percent_complete + 1, text="جاري توزيع المهام بذكاء...")
                    my_bar.empty()

                    # المنطق الحقيقي
                    days = (d_date - date.today()).days
                    quota = math.ceil(num / max(days, 1))
                    
                    # عرض بطاقة ملخص قبل الحفظ
                    st.success(f"تمت الموافقة على الخطة! سيتم إضافة {num} مهام لجدولك.")
                    st.markdown(f"""
                    <div class='glass-card' style='border-color: #22c55e'>
                        <h4>✅ ملخص الخطة:</h4>
                        <ul>
                            <li><b>المادة:</b> {subj}</li>
                            <li><b>المعدل اليومي:</b> {quota} درس/يوم</li>
                            <li><b>المدة:</b> {days} أيام</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

                    # التنفيذ في الداتابيز
                    for i in range(min(days, num)):
                        add_task_db(user['username'], f"مذاكرة {subj} - جزء {i+1} (إنقاذ)", 1, diff, date.today()+timedelta(days=i))
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("من فضلك أدخل اسم المادة.")

    elif menu == "المكتبة":
        st.title("📚 مكتبة الوسائط")
        with st.expander("📤 اضغط هنا لرفع ملف جديد", expanded=False):
            up_file = st.file_uploader("اختر ملف (PDF, صورة)", type=['pdf', 'png', 'jpg'])
            if up_file is not None:
                if st.button("تأكيد الرفع"):
                    bytes_data = up_file.getvalue()
                    upload_file_db(up_file.name, up_file.type, bytes_data)
                    st.success("تم الرفع!"); time.sleep(1); st.rerun()
        
        files = get_files()
        st.caption(f"عدد الملفات المتاحة: {len(files)}")
        cols = st.columns(3)
        for i, row in files.iterrows():
            with cols[i%3]:
                icon = "📄" if "pdf" in row['file_type'].lower() else "🖼️"
                is_real_badge = "✅ حقيقي" if row['is_real'] else "🔖 تجريبي"
                st.markdown(f"""
                <div class='glass-card' style='text-align:center; padding:15px'>
                    <h2>{icon}</h2>
                    <h5 style='margin:5px'>{row['file_name']}</h5>
                    <small style='color:#aaa'>{is_real_badge}</small>
                </div>
                """, unsafe_allow_html=True)
                if row['is_real']:
                    file_data = get_real_file_content(row['id'])
                    if file_data:
                        st.download_button(label="📥 تحميل", data=file_data[0], file_name=file_data[1], mime=row['file_type'], key=f"dl_{row['id']}")
                else:
                    st.button("📥 تحميل", key=f"fake_{row['id']}", disabled=True)

    elif menu == "إدارة المستخدمين" and role == 'admin':
        st.title("👮 لوحة تحكم المدير")
        conn = get_connection()
        users_df = pd.read_sql("SELECT username, name, role FROM users", conn)
        conn.close()
        st.dataframe(users_df, use_container_width=True)
        st.write("---")
        st.subheader("🗑️ حذف مستخدم")
        u_del = st.selectbox("اختر المستخدم", users_df['username'].unique())
        if st.button(f"حذف {u_del}"):
            if u_del == 'admin': st.error("لا يمكن حذف المدير!")
            else: delete_user_db(u_del); st.success(f"تم حذف {u_del}"); time.sleep(1); st.rerun()

# ---------------------------------------------------------
# 5. صفحة الدخول
# ---------------------------------------------------------
def login_page():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        lottie_anim = load_lottie("https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json")
        if lottie_anim: st_lottie(lottie_anim, height=200, key="anim")
        
        st.markdown("""<div class='glass-card' style='text-align:center; margin-top:-20px'><h1 style='color:#38bdf8; margin-bottom:0'>SmartBacklog</h1><p style='color:#aaa;'>إصدار المسابقة الرسمية 🏆</p></div>""", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔒 دخول", "✨ تسجيل"])
        with tab1:
            u = st.text_input("المستخدم", key="l_u"); p = st.text_input("كلمة السر", type="password", key="l_p")
            if st.button("دخول"):
                user = login_user(u, p)
                if user: st.session_state.logged_in = True; st.session_state.user = user; st.rerun()
                else: st.error("خطأ")
            st.caption("للتجربة: admin / 123")
            
        with tab2:
            nu = st.text_input("اسم مستخدم جديد", key="r_u"); nn = st.text_input("الاسم", key="r_n"); np = st.text_input("كلمة السر", type="password", key="r_p")
            if st.button("إنشاء حساب"):
                if register_user(nu, np, nn): st.success("تم! سجل دخول الآن.")
                else: st.error("المستخدم موجود مسبقاً")

if st.session_state.logged_in: main_app()
else: login_page()
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
# 2. التنسيق المستقر (Clean CSS)
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@500;700;900&display=swap');

/* إخفاء الهيدر الافتراضي المزعج */
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stDecoration"] { display: none; }

/* تنسيق زر القائمة الأصلي (هامبرغر) ليظهر بشكل جميل */
button[kind="header"] {
    color: #ffffff !important;
    background: rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    top: 15px !important; /* ضبط المكان */
    left: 15px !important;
    z-index: 99999 !important;
    transition: all 0.3s;
}
button[kind="header"]:hover {
    background: rgba(37, 99, 235, 0.5) !important; /* لون أزرق عند اللمس */
    transform: scale(1.05);
}

/* الخلفية العامة */
.stApp {
    background-color: #050505;
    background-image: 
        radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
        radial-gradient(at 50% 100%, hsla(225,39%,25%,1) 0, transparent 50%);
    color: #ffffff;
}
* { font-family: 'Cairo', sans-serif !important; }

/* شريط العنوان المخصص */
.custom-navbar {
    position: fixed; top: 0; left: 0; right: 0; height: 70px;
    background: rgba(20, 20, 30, 0.95);
    backdrop-filter: blur(15px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1); 
    z-index: 9999;
    display: flex; align-items: center; 
    justify-content: space-between; /* تباعد العناصر */
    padding: 0 20px; 
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}

/* البروفايل (يسار) - قمنا بإزاحته قليلاً لليمين عشان زر القائمة */
.navbar-user {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.1); padding: 5px 15px;
    border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);
    margin-left: 50px; /* مسافة لزر القائمة الأصلي */
}

/* اللوجو (يمين) */
.navbar-brand {
    font-size: 22px; font-weight: 900;
    background: -webkit-linear-gradient(45deg, #3b82f6, #d946ef);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

section[data-testid="stSidebar"] {
    background-color: #0a0a0f !important; border-right: 1px solid #1f2937; padding-top: 80px;
}

/* الكروت */
.glass-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8));
    backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px; padding: 25px; box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    transition: transform 0.2s; margin-bottom: 20px;
}

/* تحسينات الموبايل */
@media (max-width: 600px) {
    .custom-navbar { height: 60px; padding: 0 10px; }
    .navbar-brand { font-size: 18px; }
    .navbar-user { padding: 4px 10px; margin-left: 50px; }
    .navbar-user span { font-size: 1rem; } /* تصغير أيقونة المستخدم قليلاً */
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { color: white !important; }
}

div.stButton > button {
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    color: white; border: none; padding: 16px; border-radius: 16px;
    font-size: 18px !important; font-weight: 800 !important;
    width: 100%; margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. قاعدة البيانات
# ---------------------------------------------------------
DB_FILE = 'smart_backlog_v5.db'

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
    c.execute("SELECT count(*) FROM attachments")
    if c.fetchone()[0] < 5:
        subjects = ["الفيزياء", "الكيمياء", "العربي", "الإنجليزي"]
        types = ["PDF", "Image"]
        for i in range(10):
            subj = random.choice(subjects)
            c.execute("INSERT INTO attachments (file_name, file_type, file_content, is_real, upload_date) VALUES (?, ?, ?, ?, ?)",
                      (f"ملف مراجعة {subj} {i+1}", random.choice(types), None, False, date.today()))
    conn.commit(); conn.close()

def inject_starting_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM tasks WHERE user='student'")
    if c.fetchone()[0] == 0:
        today = date.today()
        starting_tasks = [
            ("الفيزياء الحديثة - الفصل الخامس", 3, 8, 4),
            ("الكيمياء العضوية - الهيدروكربونات", 5, 9, 7),
            ("التفاضل - معدلات زمنية مرتبطة", 2, 7, 3),
            ("اللغة العربية - مراجعة النحو", 1, 5, 2),
            ("الإنجليزي - Unit 5 Vocabulary", 2, 4, 5),
            ("الجيولوجيا - الباب الثالث (صخور)", 4, 6, 6),
            ("الفيزياء الكهربية - كيرشوف", 3, 9, 8),
            ("الإحصاء - الاحتمالات", 2, 3, 10),
            ("اللغة الفرنسية - مراجعة عامة", 1, 2, 12),
            ("الأحياء - البيولوجيا الجزيئية (DNA)", 4, 8, 5)
        ]
        for subj, units, diff, days_add in starting_tasks:
            d_date = today + timedelta(days=days_add)
            prio = int((diff * units * 10) / max((d_date - today).days, 1))
            c.execute("INSERT INTO tasks (user, subject, units, difficulty, priority, due_date, is_completed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ('student', subj, units, diff, prio, d_date, False))
        conn.commit()
    conn.close()

init_db()
inject_starting_data()

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
# 4. التطبيق الرئيسي
# ---------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}

def render_custom_header(user):
    # تم إزالة التعليقات والأكواد المعقدة لضمان الاستقرار
    st.markdown(f"""
    <div class="custom-navbar">
        <div class="navbar-user">
            <span style="font-size: 1.2rem;">👤</span>
            <div style="line-height: 1.2;">
                <div style="font-weight: bold; font-size: 0.9rem;">{user['name']}</div>
                <div style="font-size: 0.7rem; color: #aaa;">{user['role']}</div>
            </div>
        </div>
        <div class="navbar-brand">SmartBacklog 🚀</div>
    </div>
    <div style="margin-top: 60px;"></div> 
    """, unsafe_allow_html=True)

def render_progress(pct):
    color = "#ef4444" if pct < 30 else "#facc15" if pct < 70 else "#22c55e"
    st.markdown(f"""
    <div style="margin-bottom:15px; background:rgba(255,255,255,0.03); padding:15px; border-radius:15px;">
        <div style="display:flex;justify-content:space-between;color:white;font-weight:bold;margin-bottom:8px">
            <span>مستوى الإنجاز العام</span>
            <span style="color:{color}">{pct:.1f}%</span>
        </div>
        <div style="background:rgba(255,255,255,0.1);border-radius:10px;height:12px;overflow:hidden">
            <div style="background:{color};width:{pct}%;height:100%;border-radius:10px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main_app():
    user = st.session_state.user
    role = user['role']
    render_custom_header(user)
    
    with st.sidebar:
        opts = ["لوحة التحكم", "الجدول اليومي", "غرفة الإنقاذ", "المكتبة"]
        icons = ['speedometer2', 'calendar-check', 'life-preserver', 'collection']
        if role == 'admin': opts.insert(1, "إدارة المستخدمين"); icons.insert(1, "people")
        
        menu = option_menu("القائمة", opts, icons=icons, menu_icon="list", default_index=0, 
            styles={
                "container": {"background-color": "transparent"}, 
                "nav-link": {"color": "#ddd", "font-size": "16px", "margin": "5px 0"},
                "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight":"bold"},
            })
        st.write("---"); 
        if st.button("🚪 خروج"): st.session_state.logged_in = False; st.rerun()

    if menu == "لوحة التحكم":
        st.markdown("<h2 style='margin-bottom:20px'>📊 لوحة القيادة</h2>", unsafe_allow_html=True)
        tasks = get_tasks(role, user['username'])
        
        if not tasks.empty:
            done = len(tasks[tasks['is_completed']==True]); total = len(tasks); pct = (done/total*100) if total > 0 else 0
            
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_progress(pct)
            c1, c2, c3 = st.columns(3)
            c1.metric("📝 كل المهام", total)
            c2.metric("✅ المكتملة", done)
            c3.metric("🔥 المتبقية", total - done)
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                tasks['Subject_Main'] = tasks['subject'].apply(lambda x: x.split('-')[0].strip())
                cnt = tasks['Subject_Main'].value_counts().reset_index()
                cnt.columns = ['المادة', 'العدد']
                
                fig_bar = px.bar(cnt, x='المادة', y='العدد', 
                                 title="🎨 توزيع المواد",
                                 color='المادة', text='العدد', template='plotly_dark')
                
                fig_bar.update_layout(
                    paper_bgcolor="rgba(30, 41, 59, 0.6)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    showlegend=False,
                    title_font_size=20,
                    margin=dict(t=50, l=20, r=20, b=20)
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                pie_data = tasks['is_completed'].map({True: 'تم الإنجاز', False: 'معلق'}).value_counts().reset_index()
                pie_data.columns = ['الحالة', 'العدد']
                
                fig_pie = px.pie(pie_data, values='العدد', names='الحالة', 
                                 title="🎯 نسبة الإنجاز",
                                 hole=0.5, 
                                 color='الحالة',
                                 color_discrete_map={'تم الإنجاز': '#22c55e', 'معلق': '#ef4444'},
                                 template='plotly_dark')
                
                fig_pie.update_layout(
                    paper_bgcolor="rgba(30, 41, 59, 0.6)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    title_font_size=20,
                    margin=dict(t=50, l=20, r=20, b=20)
                )
                fig_pie.update_traces(textinfo='percent+label', textfont_size=14)
                st.plotly_chart(fig_pie, use_container_width=True)
                
        else: st.info("لا توجد بيانات.. ابدأ بإضافة مهام!")

    elif menu == "الجدول اليومي":
        st.markdown("<h2 style='margin-bottom:20px'>🗓️ جدول الأولويات</h2>", unsafe_allow_html=True)
        tasks = get_tasks(role, user['username'])
        if not tasks.empty:
            filter_option = st.selectbox("🌪️ تصفية العرض:", ["الكل", "المعلق (Pending)", "المنجز (Done)"])
            if filter_option == "المعلق (Pending)": tasks = tasks[tasks['is_completed'] == False]
            elif filter_option == "المنجز (Done)": tasks = tasks[tasks['is_completed'] == True]
            tasks = tasks.sort_values(by=['is_completed', 'priority'], ascending=[True, False]).reset_index(drop=True)
            
            edited = st.data_editor(
                tasks,
                column_config={
                    "is_completed": st.column_config.CheckboxColumn("إنجاز", width="small"),
                    "subject": st.column_config.TextColumn("تفاصيل المهمة", width="large"),
                    "priority": st.column_config.ProgressColumn("الأولوية 🔥", help="كلما زاد الرقم زادت الأهمية", format="%d", min_value=0, max_value=100),
                    "due_date": st.column_config.DateColumn("الموعد النهائي"),
                    "id": None, "user": None, "units": None, "difficulty": None, "Subject_Main": None
                },
                column_order=["is_completed", "priority", "subject", "due_date"],
                disabled=["subject", "priority", "due_date"],
                hide_index=True, use_container_width=True, key="tasks_editor"
            )
            if st.button("💾 حفظ التغييرات الآن"):
                conn = get_connection()
                changes = 0
                for i, row in edited.iterrows():
                    conn.execute("UPDATE tasks SET is_completed=? WHERE id=?", (row['is_completed'], row['id']))
                    changes += 1
                conn.commit(); conn.close()
                if changes > 0: st.toast("تم الحفظ بنجاح! استمر يا بطل 💪", icon="✅"); time.sleep(1); st.rerun()
        else: st.info("جدولك فارغ! اذهب لغرفة الإنقاذ.")

    elif menu == "غرفة الإنقاذ":
        st.markdown("<h2>🚑 غرفة الإنقاذ (AI Planner)</h2>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>💡 أدخل المادة المتراكمة وسيقوم الذكاء الاصطناعي بتقسيمها لك.</div>", unsafe_allow_html=True)
        with st.form("rescue_form"):
            c1, c2 = st.columns(2)
            with c1:
                subj = st.text_input("📚 اسم المادة", placeholder="مثال: الكيمياء")
                num = st.number_input("🔢 عدد الدروس", 1, 100, 5)
            with c2:
                diff = st.slider("😰 مستوى الصعوبة", 1, 10, 7)
                d_date = st.date_input("🗓️ تاريخ الانتهاء", min_value=date.today() + timedelta(days=1))
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("🚀 أنقذني الآن")
            if submit and subj:
                with st.spinner('جاري تحليل الجدول...'): time.sleep(1)
                days = (d_date - date.today()).days
                quota = math.ceil(num / max(days, 1))
                st.success(f"تم اعتماد الخطة: {quota} درس يومياً لمدة {days} أيام")
                for i in range(min(days, num)):
                    add_task_db(user['username'], f"مذاكرة {subj} - جزء {i+1} (إنقاذ)", 1, diff, date.today()+timedelta(days=i))
                time.sleep(1.5); st.rerun()

    elif menu == "المكتبة":
        st.markdown("<h2>📚 مكتبة الوسائط</h2>", unsafe_allow_html=True)
        with st.expander("📤 رفع ملف جديد", expanded=False):
            up_file = st.file_uploader("اختر ملف", type=['pdf', 'png', 'jpg'])
            if up_file is not None and st.button("تأكيد الرفع"):
                bytes_data = up_file.getvalue()
                upload_file_db(up_file.name, up_file.type, bytes_data)
                st.success("تم الرفع!"); time.sleep(1); st.rerun()
        files = get_files()
        cols = st.columns(2)
        for i, row in files.iterrows():
            with cols[i%2]:
                icon = "📄" if "pdf" in row['file_type'].lower() else "🖼️"
                st.markdown(f"""
                <div class='glass-card' style='text-align:center; padding:10px; margin-bottom:10px'>
                    <h2 style='margin:0'>{icon}</h2>
                    <h5 style='margin:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis'>{row['file_name']}</h5>
                </div>
                """, unsafe_allow_html=True)
                if row['is_real']:
                    file_data = get_real_file_content(row['id'])
                    if file_data:
                        st.download_button("📥 تحميل", data=file_data[0], file_name=file_data[1], mime=row['file_type'], key=f"dl_{row['id']}")
                else: st.button("📥 تحميل", key=f"fake_{row['id']}", disabled=True)

    elif menu == "إدارة المستخدمين" and role == 'admin':
        st.title("👮 لوحة المدير")
        conn = get_connection()
        users_df = pd.read_sql("SELECT username, name, role FROM users", conn)
        conn.close()
        st.dataframe(users_df, use_container_width=True)
        st.write("---")
        u_del = st.selectbox("حذف مستخدم:", users_df['username'].unique())
        if st.button("حذف") and u_del != 'admin':
            delete_user_db(u_del); st.success("تم الحذف"); time.sleep(1); st.rerun()

# ---------------------------------------------------------
# 5. صفحة الدخول
# ---------------------------------------------------------
def login_page():
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        lottie_anim = load_lottie("https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json")
        if lottie_anim: st_lottie(lottie_anim, height=220, key="anim")
        st.markdown("""
        <div class='glass-card' style='text-align:center; margin-bottom:20px'>
            <h1 style='background: linear-gradient(to right, #60a5fa, #c084fc); -webkit-background-clip: text; color: transparent;'>SmartBacklog</h1>
            <p style='color:#94a3b8;'>نظام إدارة المهام الذكي للطلاب 🚀</p>
        </div>
        """, unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔒 دخول", "✨ تسجيل"])
        with tab1:
            u = st.text_input("اسم المستخدم", key="l_u"); p = st.text_input("كلمة المرور", type="password", key="l_p")
            if st.button("تسجيل الدخول"):
                user = login_user(u, p)
                if user: st.session_state.logged_in = True; st.session_state.user = user; st.rerun()
                else: st.error("بيانات خاطئة!")
            st.caption("جرب: student / 123")
        with tab2:
            nu = st.text_input("اختر اسم مستخدم", key="r_u"); nn = st.text_input("اسمك الحقيقي", key="r_n"); np = st.text_input("كلمة مرور قوية", type="password", key="r_p")
            if st.button("إنشاء حساب جديد"):
                if register_user(nu, np, nn): st.success("تم الإنشاء! سجل دخولك الآن."); time.sleep(1); st.rerun()
                else: st.error("الاسم مستخدم مسبقاً")

if st.session_state.logged_in: main_app()
else: login_page()
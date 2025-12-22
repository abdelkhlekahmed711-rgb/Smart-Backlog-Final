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
st.set_page_config(page_title="SmartBacklog", page_icon="🚀", layout="wide")

# ---------------------------------------------------------
# 2. التنسيق (CSS) - إصلاحات الأندرويد الصارمة
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@500;700;900&display=swap');

/* 1. تعميم الخط العربي */
html, body, p, div, h1, h2, h3, h4, h5, h6, span, a, label, button, input, textarea, li {
    font-family: 'Cairo', sans-serif !important;
}

/* 2. استثناء الأيقونات من الخط */
.material-icons, .st-emotion-cache-1pbqwg9, [data-testid="stSidebarCollapsedControl"] {
    font-family: 'Material Icons', sans-serif !important;
}

/* 3. إصلاح القائمة الجانبية (Sidebar) - خاصة للأندرويد */
section[data-testid="stSidebar"] {
    background-color: #0a0a0f !important; /* خلفية داكنة جداً */
    border-right: 1px solid #1f2937;
}

/* إجبار جميع النصوص داخل السايد بار على اللون الأبيض */
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* تحسين القائمة المنسدلة (Option Menu) داخل السايد بار */
.nav-link {
    color: #e0e0e0 !important; /* لون النص غير المحدد */
    background-color: transparent !important;
}
.nav-link:hover {
    background-color: rgba(255,255,255,0.1) !important;
}
.nav-link-selected {
    background-color: #2563eb !important; /* لون الخلفية للمحدد */
    color: #ffffff !important;
    font-weight: bold !important;
}

/* 4. الهيدر وزر القائمة */
header[data-testid="stHeader"] { background-color: transparent !important; z-index: 1000 !important; }
[data-testid="stSidebarCollapsedControl"] {
    color: white !important; background-color: rgba(255,255,255,0.1) !important;
    border-radius: 8px; padding: 5px;
}
[data-testid="stDecoration"] { display: none; }

/* 5. الخلفية العامة */
.stApp {
    background-color: #050505;
    background-image: 
        radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
        radial-gradient(at 50% 100%, hsla(225,39%,25%,1) 0, transparent 50%);
    color: #ffffff;
}

/* 6. تحسينات عامة للموبايل */
@media (max-width: 600px) {
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: white !important; }
    /* تحسين ظهور الجداول في الموبايل */
    .stDataFrame { background: rgba(255,255,255,0.05) !important; border-radius: 10px; }
}

/* 7. الأزرار */
div.stButton > button {
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    color: white; border: none; padding: 12px; border-radius: 12px;
    font-weight: bold; width: 100%;
}

/* 8. الكروت الزجاجية */
.glass-card {
    background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px;
    padding: 20px; margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. قاعدة البيانات
# ---------------------------------------------------------
DB_FILE = 'smart_backlog_clean.db'

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

def delete_task_by_id(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
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

def render_progress(pct):
    color = "#ef4444" if pct < 30 else "#facc15" if pct < 70 else "#22c55e"
    st.markdown(f"""
    <div style="margin-bottom:15px; background:rgba(255,255,255,0.03); padding:15px; border-radius:15px; border:1px solid rgba(255,255,255,0.05);">
        <div style="display:flex;justify-content:space-between;color:white;font-weight:bold;margin-bottom:8px">
            <span>مستوى الإنجاز العام</span>
            <span style="color:{color}">{pct:.1f}%</span>
        </div>
        <div style="background:rgba(255,255,255,0.1);border-radius:10px;height:12px;overflow:hidden">
            <div style="background:{color};width:{pct}%;height:100%;border-radius:10px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def get_arabic_day_name(dt):
    days = {'Saturday': 'السبت', 'Sunday': 'الأحد', 'Monday': 'الاثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء', 'Thursday': 'الخميس', 'Friday': 'الجمعة'}
    return days.get(dt.strftime("%A"), dt.strftime("%A"))

def main_app():
    user = st.session_state.user
    role = user['role']
    
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 10px; margin-bottom: 20px;">
            <h3 style="margin:0; color:white;">👤 {user['name']}</h3>
            <span style="color: #3b82f6; font-size: 0.9em;">{user['role'].upper()}</span>
        </div>
        """, unsafe_allow_html=True)
        
        opts = ["لوحة التحكم", "الجدول اليومي", "غرفة الإنقاذ", "المكتبة"]
        icons = ['speedometer2', 'calendar-check', 'life-preserver', 'collection']
        if role == 'admin': opts.insert(1, "إدارة المستخدمين"); icons.insert(1, "people")
        
        menu = option_menu("القائمة", opts, icons=icons, menu_icon="list", default_index=0, 
            styles={
                "container": {"background-color": "transparent"}, 
                "nav-link": {"color": "white", "font-size": "16px", "margin": "5px 0"},
                "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight":"bold"},
                "icon": {"color": "#38bdf8", "font-size": "18px"},
            })
        st.write("---"); 
        if st.button("🚪 خروج"): st.session_state.logged_in = False; st.rerun()

    if menu == "لوحة التحكم":
        st.title("📊 لوحة القيادة")
        tasks = get_tasks(role, user['username'])
        
        if not tasks.empty:
            done = len(tasks[tasks['is_completed']==True]); total = len(tasks); pct = (done/total*100) if total > 0 else 0
            
            render_progress(pct)
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div style='background:rgba(255,255,255,0.05);padding:15px;border-radius:15px;text-align:center'><h3>📝 الكل</h3><h2>{total}</h2></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div style='background:rgba(255,255,255,0.05);padding:15px;border-radius:15px;text-align:center;color:#4ade80'><h3>✅ تم</h3><h2>{done}</h2></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div style='background:rgba(255,255,255,0.05);padding:15px;border-radius:15px;text-align:center;color:#f87171'><h3>🔥 باقي</h3><h2>{total-done}</h2></div>", unsafe_allow_html=True)
            
            st.markdown("---")

            col_sched, col_pie = st.columns([2, 1])
            
            with col_sched:
                st.subheader("📈 مستوى الضغط الدراسي (7 أيام)")
                today = date.today()
                week_data = []
                for i in range(7):
                    current_day = today + timedelta(days=i)
                    day_label = f"{get_arabic_day_name(current_day)} ({current_day.strftime('%d/%m')})"
                    day_tasks = tasks[tasks['due_date'] == current_day]
                    count = len(day_tasks)
                    top_focus = day_tasks.sort_values(by='priority', ascending=False).iloc[0]['subject'] if not day_tasks.empty else "لا يوجد"
                    week_data.append({"اليوم": day_label, "عدد المهام": count, "التركيز على": top_focus})
                
                df_week = pd.DataFrame(week_data)
                fig_line = px.line(df_week, x='اليوم', y='عدد المهام', markers=True, template='plotly_dark', hover_data=['التركيز على'])
                fig_line.update_traces(line_color='#38bdf8', line_width=3, marker_size=8)
                fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.05)", font_color="white", xaxis_title="", yaxis_title="عدد الدروس", margin=dict(t=20, l=10, r=10, b=10))
                fig_line.update_yaxes(dtick=1, rangemode="tozero")
                st.plotly_chart(fig_line, use_container_width=True)

            with col_pie:
                st.subheader("🎯 نسبة الإنجاز")
                pie_data = tasks['is_completed'].map({True: 'تم الإنجاز', False: 'معلق'}).value_counts().reset_index()
                pie_data.columns = ['الحالة', 'العدد']
                fig_pie = px.pie(pie_data, values='العدد', names='الحالة', hole=0.6, color='الحالة', color_discrete_map={'تم الإنجاز': '#22c55e', 'معلق': '#ef4444'}, template='plotly_dark')
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False, margin=dict(t=20, l=10, r=10, b=10))
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
                
        else: st.info("👋 أهلاً بك! البيانات فارغة حالياً. اذهب إلى 'غرفة الإنقاذ' لإضافة خطتك الأولى.")

    elif menu == "الجدول اليومي":
        st.title("🗓️ إدارة المهام اليومية")
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
        else: st.info("جدولك نظيف! اذهب لغرفة الإنقاذ لإضافة مهام.")

    elif menu == "غرفة الإنقاذ":
        st.title("🚑 غرفة عمليات الإنقاذ (AI Planner)")
        col_add, col_del = st.columns(2)

        with col_add:
            st.markdown("<div class='glass-card'><h4>➕ إضافة خطة دراسية</h4><p style='color:#aaa;'>أضف موادك وسيقوم النظام بتوزيعها.</p></div>", unsafe_allow_html=True)
            with st.form("rescue_form"):
                subj = st.text_input("📚 اسم المادة", placeholder="مثال: الكيمياء")
                num = st.number_input("🔢 عدد الدروس", 1, 100, 5)
                diff = st.slider("😰 مستوى الصعوبة", 1, 10, 7)
                d_date = st.date_input("🗓️ تاريخ الانتهاء", min_value=date.today() + timedelta(days=1))
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("🚀 إضافة الخطة")
                if submit and subj:
                    with st.spinner('جاري تحليل الجدول...'): time.sleep(1)
                    days = (d_date - date.today()).days
                    quota = math.ceil(num / max(days, 1))
                    st.success(f"تم اعتماد الخطة: {quota} درس يومياً لمدة {days} أيام")
                    for i in range(min(days, num)):
                        add_task_db(user['username'], f"مذاكرة {subj} - جزء {i+1} (إنقاذ)", 1, diff, date.today()+timedelta(days=i))
                    time.sleep(1.5); st.rerun()

        with col_del:
            st.markdown("<div class='glass-card' style='border-color:#f87171'><h4 style='color:#f87171'>🗑️ حذف المواد والمهام</h4><p style='color:#aaa;'>تخلص من المواد التي انتهيت منها.</p></div>", unsafe_allow_html=True)
            my_tasks = get_tasks(role, user['username'])
            if not my_tasks.empty:
                task_options = {f"{row['subject']} ({row['due_date']})": row['id'] for i, row in my_tasks.iterrows()}
                selected_task_label = st.selectbox("🔻 اختر المهمة لحذفها:", list(task_options.keys()))
                if st.button("❌ حذف المحدد نهائياً", type="primary"):
                    delete_task_by_id(task_options[selected_task_label])
                    st.toast("تم الحذف من قاعدة البيانات!", icon="🗑️"); time.sleep(1); st.rerun()
            else: st.info("لا توجد مهام لحذفها.")

    elif menu == "المكتبة":
        st.title("📚 مكتبة الوسائط")
        with st.expander("📤 رفع ملف جديد", expanded=False):
            up_file = st.file_uploader("اختر ملف", type=['pdf', 'png', 'jpg'])
            if up_file is not None and st.button("تأكيد الرفع"):
                bytes_data = up_file.getvalue()
                upload_file_db(up_file.name, up_file.type, bytes_data)
                st.success("تم الرفع!"); time.sleep(1); st.rerun()
        files = get_files()
        if not files.empty:
            cols = st.columns(2)
            for i, row in files.iterrows():
                with cols[i%2]:
                    icon = "📄" if "pdf" in row['file_type'].lower() else "🖼️"
                    st.markdown(f"<div style='background:rgba(255,255,255,0.05);padding:15px;border-radius:15px;text-align:center;margin-bottom:10px;border:1px solid rgba(255,255,255,0.1)'><h2 style='margin:0'>{icon}</h2><h5 style='margin:5px'>{row['file_name']}</h5></div>", unsafe_allow_html=True)
                    if row['is_real']:
                        file_data = get_real_file_content(row['id'])
                        if file_data: st.download_button("📥 تحميل", data=file_data[0], file_name=file_data[1], mime=row['file_type'], key=f"dl_{row['id']}")
                    else: st.button("📥 تحميل", key=f"fake_{row['id']}", disabled=True)
        else: st.info("المكتبة فارغة.")

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
# 5. صفحة الدخول (تحديث: عرض البيانات جنب بعض)
# ---------------------------------------------------------
def login_page():
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        lottie_anim = load_lottie("https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json")
        if lottie_anim: st_lottie(lottie_anim, height=220, key="anim")
        st.markdown("""
        <div style='text-align:center; margin-bottom:20px; background:rgba(255,255,255,0.05); padding:20px; border-radius:20px'>
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
            
            # --- التعديل هنا: وضع البيانات بجانب بعضها ---
            st.markdown("""
            <div style='background:rgba(0,0,0,0.3); padding:10px; border-radius:10px; margin-top:10px; display:flex; justify-content:space-around; align-items:center;'>
                <span style='color:#bbb; font-size:0.85em'>👤 الطالب: <b style='color:white'>student</b> / <b style='color:white'>123</b></span>
                <span style='color:#555'>|</span>
                <span style='color:#bbb; font-size:0.85em'>👮 المدير: <b style='color:white'>admin</b> / <b style='color:white'>123</b></span>
            </div>
            """, unsafe_allow_html=True)
            
        with tab2:
            nu = st.text_input("اختر اسم مستخدم", key="r_u"); nn = st.text_input("اسمك الحقيقي", key="r_n"); np = st.text_input("كلمة مرور قوية", type="password", key="r_p")
            if st.button("إنشاء حساب جديد"):
                if register_user(nu, np, nn): st.success("تم الإنشاء! سجل دخولك الآن."); time.sleep(1); st.rerun()
                else: st.error("الاسم مستخدم مسبقاً")

if st.session_state.logged_in: main_app()
else: login_page()
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
# 2. التنسيق الجديد (UI/UX 2.0) - الواجهة القوية
# ---------------------------------------------------------
st.markdown("""
<style>
/* استيراد خط 'Cairo' القوي والواضح */
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

/* الخلفية العامة - تدرج داكن عميق مناسب للعين وشاشات OLED */
.stApp {
    background-color: #000000;
    background-image: 
        radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
        radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
        radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
    background-size: 100% 100%;
    color: #ffffff;
}

/* توحيد الخطوط */
* { font-family: 'Cairo', sans-serif !important; }

/* العناوين بستايل نيون مضيء */
h1, h2, h3, h4, h5 {
    color: #ffffff !important;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    font-weight: 900 !important;
}

/* السايد بار (القائمة الجانبية) */
section[data-testid="stSidebar"] {
    background-color: rgba(10, 10, 20, 0.95) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

/* الكروت الزجاجية (Glassmorphism) - محدثة لتكون أوضح */
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 24px;
    padding: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    margin-bottom: 20px;
    transition: transform 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(56, 189, 248, 0.5);
    transform: translateY(-5px);
}

/* تحسين حقول الإدخال لتكون واضحة جداً */
input, .stTextInput > div > div > input, 
.stDateInput > div > div > input, 
.stNumberInput > div > div > input,
textarea {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 2px solid #334155 !important;
    border-radius: 12px !important;
    font-size: 16px !important;
    font-weight: bold !important;
    padding: 10px !important;
}
/* عند الضغط على الحقل */
input:focus, textarea:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
}

/* القوائم المنسدلة */
.stSelectbox > div > div > div {
    background-color: #1e293b !important;
    color: white !important;
    font-weight: bold;
}

/* الأزرار - تصميم قوي (Cyberpunk Style) */
div.stButton > button {
    background: linear-gradient(135deg, #2563eb 0%, #a855f7 100%);
    color: white !important;
    border: none;
    padding: 15px 30px;
    border-radius: 16px;
    font-size: 18px !important;
    font-weight: 900 !important;
    letter-spacing: 0.5px;
    box-shadow: 0 10px 20px -10px rgba(168, 85, 247, 0.6);
    width: 100%;
    transition: all 0.3s ease;
}
div.stButton > button:active {
    transform: scale(0.98);
}
div.stButton > button:hover {
    box-shadow: 0 0 20px rgba(37, 99, 235, 0.8);
    background: linear-gradient(135deg, #3b82f6 0%, #d946ef 100%);
}

/* تخصيص للأندرويد والموبايل (Responsive) */
@media only screen and (max-width: 600px) {
    .stApp { padding-top: 20px; }
    h1 { font-size: 28px !important; }
    div.stButton > button { padding: 12px 20px; font-size: 16px !important; }
    .glass-card { padding: 15px; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. منطق قاعدة البيانات (لم يتم المساس به إطلاقاً)
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

# --- دوال المساعدة ---
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
# 4. التطبيق الرئيسي (UI Structure)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}

def render_progress(pct):
    color, emoji = ("#ef4444", "😟") if pct < 30 else ("#facc15", "😐") if pct < 70 else ("#4ade80", "🤩")
    st.markdown(f"""
    <div style="margin-bottom:15px; padding:10px; background:rgba(0,0,0,0.2); border-radius:15px">
        <div style="display:flex;justify-content:space-between;color:white;font-weight:bold;margin-bottom:5px">
            <span style="font-size:18px">مستوى الإنجاز {emoji}</span>
            <span style="font-size:18px; color:{color}">{pct:.1f}%</span>
        </div>
        <div style="background:rgba(255,255,255,0.1);border-radius:10px;height:16px; overflow:hidden">
            <div style="background:{color};width:{pct}%;height:100%;border-radius:10px;box-shadow: 0 0 10px {color}; transition:width 0.8s ease-in-out"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main_app():
    user = st.session_state.user
    role = user['role']
    
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align:center; margin-bottom:20px; padding:20px; background:rgba(255,255,255,0.05); border-radius:20px'>
            <h2 style='margin:0'>👤 {user['name']}</h2>
            <div style='color:#38bdf8; font-weight:bold; letter-spacing:2px; margin-top:5px'>{role.upper()}</div>
        </div>
        """, unsafe_allow_html=True)
        
        opts = ["لوحة التحكم", "الجدول اليومي", "غرفة الإنقاذ", "المكتبة"]
        icons = ['speedometer2', 'table', 'life-preserver', 'collection']
        if role == 'admin': opts.insert(1, "إدارة المستخدمين"); icons.insert(1, "people")
        
        menu = option_menu("القائمة الرئيسية", opts, icons=icons, menu_icon="grid-fill", default_index=0, 
            styles={
                "container": {"background-color": "transparent"}, 
                "nav-link": {"color": "#e2e8f0", "font-size": "17px", "margin": "5px", "border-radius": "10px"},
                "nav-link-selected": {"background-color": "#3b82f6", "color": "white", "box-shadow": "0 0 15px rgba(59, 130, 246, 0.5)"},
            })
        
        st.write("---"); 
        if st.button("🚪 تسجيل خروج"): st.session_state.logged_in = False; st.rerun()

    if menu == "لوحة التحكم":
        st.title("🚀 مركز القيادة")
        tasks = get_tasks(role, user['username'])
        if not tasks.empty:
            done = len(tasks[tasks['is_completed']==True]); total = len(tasks); pct = (done/total*100) if total > 0 else 0
            
            # كارت الإنجاز الرئيسي
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_progress(pct)
            c1, c2, c3 = st.columns(3)
            # تنسيق الأرقام ليكون كبيراً وواضحاً
            c1.markdown(f"<div style='text-align:center'><h3>📚 الكل</h3><h1 style='color:#60a5fa'>{total}</h1></div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center'><h3>✅ تم</h3><h1 style='color:#4ade80'>{done}</h1></div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:center'><h3>⏳ باقي</h3><h1 style='color:#f87171'>{total - done}</h1></div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("#### 📊 توزيع المواد")
                tasks['Subject_Main'] = tasks['subject'].apply(lambda x: x.split('-')[0].strip())
                cnt = tasks['Subject_Main'].value_counts().reset_index()
                cnt.columns = ['المادة', 'العدد']
                fig_bar = px.bar(cnt, x='المادة', y='العدد', text='العدد', color='العدد', color_continuous_scale='Bluyl')
                fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("#### 🎯 نسبة الإنجاز")
                pie_data = tasks['is_completed'].map({True: 'منجز', False: 'معلق'}).value_counts().reset_index()
                pie_data.columns = ['الحالة', 'العدد']
                fig_pie = px.pie(pie_data, values='العدد', names='الحالة', hole=0.6, color='الحالة', color_discrete_map={'منجز': '#4ade80', 'معلق': '#f87171'})
                fig_pie.update_traces(textinfo='percent+label', textfont_size=15)
                fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else: st.info("جاري تحميل بياناتك الدراسية...")

    elif menu == "الجدول اليومي":
        st.title("🗓️ إدارة المهام الذكية")
        tasks = get_tasks(role, user['username'])
        
        if not tasks.empty:
            today_tasks = tasks[tasks['due_date'] == date.today()]
            st.markdown(f"""
            <div class='glass-card' style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;'>
                <div style='text-align:center; min-width:100px'>📅 مهام اليوم<br><b style='font-size:24px; color:#fbbf24'>{len(today_tasks)}</b></div>
                <div style='text-align:center; min-width:100px'>✅ المنجز<br><b style='font-size:24px; color:#4ade80'>{len(today_tasks[today_tasks['is_completed']==True])}</b></div>
                <div style='text-align:center; min-width:100px'>🔥 الحالة<br><b style='font-size:20px; color:#60a5fa'>تركيز عالي</b></div>
            </div>
            """, unsafe_allow_html=True)

            filter_option = st.selectbox("🌪️ فلترة العرض:", ["عرض الكل", "المهام المعلقة (Pending)", "المهام المنجزة (Done)"])

            if filter_option == "المهام المعلقة (Pending)": tasks = tasks[tasks['is_completed'] == False]
            elif filter_option == "المهام المنجزة (Done)": tasks = tasks[tasks['is_completed'] == True]

            tasks = tasks.sort_values(by=['is_completed', 'priority'], ascending=[True, False]).reset_index(drop=True)
            
            st.markdown("### 📝 قائمتك:")
            edited = st.data_editor(
                tasks,
                column_config={
                    "is_completed": st.column_config.CheckboxColumn("تم", width="small"),
                    "subject": st.column_config.TextColumn("المهمة", width="large"),
                    "priority": st.column_config.ProgressColumn("الأهمية", min_value=0, max_value=100, format="%f"),
                    "due_date": st.column_config.DateColumn("التاريخ"),
                    "id": None, "user": None, "units": None, "difficulty": None, "Subject_Main": None
                },
                column_order=["is_completed", "subject", "priority", "due_date"],
                disabled=["subject", "priority", "due_date"],
                hide_index=True,
                use_container_width=True,
                key="tasks_editor"
            )
            
            if st.button("💾 حفظ التغييرات"):
                conn = get_connection()
                changes = 0
                for i, row in edited.iterrows():
                    conn.execute("UPDATE tasks SET is_completed=? WHERE id=?", (row['is_completed'], row['id']))
                    changes += 1
                conn.commit(); conn.close()
                if changes > 0:
                    st.success("تم الحفظ بنجاح! 💪")
                    time.sleep(1); st.rerun()
        else:
            st.info("لا توجد مهام حالياً.")

    elif menu == "غرفة الإنقاذ":
        st.title("🚑 غرفة الطوارئ (AI Planner)")
        st.markdown("<div class='glass-card'><p style='font-size:18px'>💡 أدخل المادة المتراكمة وسيقوم الذكاء الاصطناعي بجدولتها لك فوراً.</p></div>", unsafe_allow_html=True)

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
                with st.spinner('جاري تحليل الجدول...'):
                    time.sleep(1.5)
                
                days = (d_date - date.today()).days
                quota = math.ceil(num / max(days, 1))
                
                st.markdown(f"""
                <div class='glass-card' style='border-color: #4ade80; background:rgba(74, 222, 128, 0.1)'>
                    <h3 style='color:#4ade80'>✅ تم اعتماد الخطة!</h3>
                    <ul style='font-size:18px'>
                        <li>المادة: <b>{subj}</b></li>
                        <li>المطلوب يومياً: <b>{quota}</b> درس</li>
                        <li>المدة: <b>{days}</b> أيام</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                for i in range(min(days, num)):
                    add_task_db(user['username'], f"مذاكرة {subj} - جزء {i+1} (إنقاذ)", 1, diff, date.today()+timedelta(days=i))
                time.sleep(2); st.rerun()

    elif menu == "المكتبة":
        st.title("📚 مكتبة الوسائط")
        with st.expander("📤 رفع ملف جديد", expanded=False):
            up_file = st.file_uploader("اختر ملف", type=['pdf', 'png', 'jpg'])
            if up_file is not None and st.button("تأكيد الرفع"):
                bytes_data = up_file.getvalue()
                upload_file_db(up_file.name, up_file.type, bytes_data)
                st.success("تم الرفع!"); time.sleep(1); st.rerun()
        
        files = get_files()
        cols = st.columns(2) # عمودين للموبايل أفضل
        for i, row in files.iterrows():
            with cols[i%2]:
                icon = "📄" if "pdf" in row['file_type'].lower() else "🖼️"
                st.markdown(f"""
                <div class='glass-card' style='text-align:center; padding:10px'>
                    <h2 style='margin:0'>{icon}</h2>
                    <h5 style='margin:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis'>{row['file_name']}</h5>
                </div>
                """, unsafe_allow_html=True)
                if row['is_real']:
                    file_data = get_real_file_content(row['id'])
                    if file_data:
                        st.download_button("📥 تحميل", data=file_data[0], file_name=file_data[1], mime=row['file_type'], key=f"dl_{row['id']}")
                else:
                    st.button("📥 تحميل", key=f"fake_{row['id']}", disabled=True)

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
# 5. صفحة الدخول (تحديث الشكل)
# ---------------------------------------------------------
def login_page():
    c1, c2, c3 = st.columns([1, 8, 1]) # توسيط أفضل للموبايل
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        lottie_anim = load_lottie("https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json")
        if lottie_anim: st_lottie(lottie_anim, height=250, key="anim")
        
        st.markdown("""
        <div class='glass-card' style='text-align:center;'>
            <h1 style='background: -webkit-linear-gradient(45deg, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3em;'>SmartBacklog</h1>
            <p style='color:#cbd5e1; font-size:1.2em;'>رفيقك الذكي لتنظيم الثانوية العامة 🚀</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔒 دخول", "✨ جديد"])
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
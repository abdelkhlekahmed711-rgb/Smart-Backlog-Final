import streamlit as st
import pandas as pd
import plotly.express as px
import os
import requests
import time
import random
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(page_title="SmartBacklog Pro", page_icon="🎓", layout="wide")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}

# ---------------------------------------------------------
# 2. الألوان (نظام ليلي إجباري)
# ---------------------------------------------------------
colors = {
    'bg': '#020617',           # كحلي غامق جداً
    'card_bg': '#0f172a',      # كحلي أفتح قليلاً
    'primary': '#38bdf8',      # أزرق سماوي
    'text': '#ffffff',         # أبيض ناصع
    'border': 'rgba(56, 189, 248, 0.5)', 
    'input_bg': '#1e293b',     # خلفية الحقول
}

# ---------------------------------------------------------
# 3. CSS (القوة الجبرية للموبايل)
# ---------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&family=El+Messiri:wght@400;500;600;700&display=swap');
* {{ font-family: 'Almarai', sans-serif; }}
h1, h2, h3, .stMetricLabel {{ font-family: 'El Messiri', sans-serif !important; }}

/* 1. إجبار الخلفية تكون كحلي */
.stApp {{
    background-color: {colors['bg']} !important;
    background-image: radial-gradient(#38bdf820 1px, transparent 1px);
    background-size: 30px 30px;
}}

/* 2. إجبار النصوص تكون بيضاء */
p, span, label, div, h1, h2, h3, h4, h5, h6, .stMarkdown {{
    color: {colors['text']} !important;
}}

/* 3. إصلاح حقول الإدخال (المشكلة الرئيسية في الموبايل) */
input, textarea, select {{
    background-color: {colors['input_bg']} !important;
    color: white !important; /* لون الخط أبيض */
    -webkit-text-fill-color: white !important; /* للأندرويد والآيفون */
    caret-color: {colors['primary']} !important; /* لون المؤشر */
    border: 1px solid {colors['border']} !important;
}}

/* 4. تنسيق الجدول ليكون غامقاً */
[data-testid="stDataEditor"] {{
    border: 1px solid {colors['border']};
    border-radius: 10px;
    background-color: {colors['card_bg']} !important;
}}
/* خلايا الجدول */
[data-testid="stDataEditor"] div {{
    color: white !important;
    background-color: {colors['card_bg']} !important;
}}

/* 5. القائمة الجانبية */
section[data-testid="stSidebar"] {{
    background-color: {colors['card_bg']} !important;
    border-right: 1px solid {colors['border']};
}}

/* 6. إصلاح زر القائمة في الموبايل */
header[data-testid="stHeader"] {{
    background: transparent !important;
    display: block !important; visibility: visible !important;
    z-index: 9999;
}}
button[kind="header"] {{
    color: {colors['primary']} !important;
    background: {colors['input_bg']} !important;
    border: 1px solid {colors['border']} !important;
    border-radius: 5px !important;
}}

/* إخفاء العناصر المزعجة */
.stDeployButton, [data-testid="stDecoration"], footer {{ display: none !important; }}

/* البطاقات */
.glass-card {{
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(10px);
    border: 1px solid {colors['border']};
    border-radius: 20px;
    padding: 20px; margin-bottom: 20px;
}}

/* الأزرار */
div.stButton > button {{
    background: linear-gradient(90deg, #0ea5e9, #2563eb);
    color: white !important; border: none;
    padding: 10px 20px; border-radius: 10px;
    font-weight: bold; width: 100%;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. البيانات
# ---------------------------------------------------------
TASKS_DB = 'smart_tasks.csv'
USERS_DB = 'smart_users.csv'

def init_dbs():
    if not os.path.exists(USERS_DB):
        pd.DataFrame([{"username": "admin", "password": "123", "name": "Admin", "role": "admin"}]).to_csv(USERS_DB, index=False)
    if not os.path.exists(TASKS_DB):
        data = {
            "إنجاز": [False] * 25,
            "المادة": ["اللغة العربية", "الفيزياء", "الكيمياء", "الأحياء", "الرياضيات", "اللغة الإنجليزية", "التاريخ", "الجغرافيا", "الفلسفة", "علم النفس", "الفيزياء (مراجعة)", "الكيمياء (عضوية)", "نحو وصرف", "تفاضل", "اللغة الفرنسية", "التربية الوطنية", "الإحصاء", "الجيولوجيا", "الأحياء (وراثة)", "قصة الإنجليزي", "ميكانيكا", "استاتيكا", "جبر", "هندسة فراغية", "بلاغة"],
            "الدروس": [2, 5, 3, 1, 4, 2, 0, 1, 2, 3, 6, 2, 1, 5, 0, 1, 0, 2, 3, 4, 2, 3, 1, 2, 5],
            "المحاضرات": [1, 2, 1, 0, 3, 1, 0, 1, 0, 1, 3, 1, 0, 2, 0, 0, 0, 1, 1, 2, 1, 2, 1, 1, 2],
            "الصعوبة": [3, 9, 8, 5, 10, 4, 2, 3, 4, 3, 9, 7, 5, 10, 3, 1, 2, 6, 7, 5, 8, 9, 7, 8, 6],
            "الأيام": [10, 5, 7, 12, 4, 15, 20, 18, 14, 13, 6, 8, 9, 3, 25, 30, 28, 11, 10, 14, 7, 6, 8, 9, 12],
            "الأولوية": [],
            "الطالب": ["admin"] * 25 
        }
        for i in range(25):
            prio = (data["الصعوبة"][i] * (data["الدروس"][i] + data["المحاضرات"][i])) / max(data["الأيام"][i], 1)
            data["الأولوية"].append(round(prio, 2))
        df = pd.DataFrame(data)
        df.to_csv(TASKS_DB, index=False)

def load_data(file): 
    df = pd.read_csv(file, dtype=str)
    if file == TASKS_DB:
        if 'إنجاز' not in df.columns: df.insert(0, 'إنجاز', 'False')
        if 'المحاضرات' not in df.columns: df['المحاضرات'] = '0'
        for c in ['الدروس', 'المحاضرات', 'الأولوية', 'الصعوبة', 'الأيام']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        df['إنجاز'] = df['إنجاز'].map({'True': True, 'False': False, True: True, False: False})
    return df

def save_data(df, file): df.to_csv(file, index=False)
init_dbs()

# AI Advice
motivational_quotes = ["النجاح ليس صدفة.", "لا تؤجل عمل اليوم.", "قمة الجبل تحتاج تسلق.", "أنت أقوى مما تتخيل."]
def get_ai_advice(df):
    if df.empty: return "جدولك فارغ! ابدأ الآن. 🚀"
    pending = df[df['إنجاز'] == False]
    total = pending['الدروس'].sum() + pending['المحاضرات'].sum()
    urgent = pending[pending['الأيام'] <= 5]
    quote = random.choice(motivational_quotes)
    advice = f"📊 **تحليل:** متبقي {int(total)} مهمة.\n"
    if total > 20: advice += "⚡ **نصيحة:** التراكمات كثيرة، ركز على مادة واحدة اليوم."
    else: advice += "✅ **نصيحة:** وضعك مستقر."
    if not urgent.empty: advice += f"\n🔥 **تنبيه:** {len(urgent)} امتحانات قريبة!"
    advice += f"\n\n✨ **حكمة:** {quote}"
    return advice

@st.cache_data
def load_lottie(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# ---------------------------------------------------------
# 5. الواجهة
# ---------------------------------------------------------
def login_page():
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        st.write("")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;'><h1>SmartBacklog</h1><p class='small-text'>Pro Edition</p></div>", unsafe_allow_html=True)
        st.info("💡 **Admin Access:** admin | 123")

        if lottie := load_lottie("https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json"):
            st_lottie(lottie, height=180, key="welcome")

        tab_log, tab_reg = st.tabs(["دخول", "جديد"])
        
        with tab_log:
            u = st.text_input("اسم المستخدم", key="u1", placeholder="user")
            p = st.text_input("كلمة المرور", type="password", key="p1", placeholder="pass")
            if st.button("دخول 🚀", key="btn_login"):
                users = load_data(USERS_DB)
                found = users[(users['username'] == u) & (users['password'] == p)]
                if not found.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = found.iloc[0].to_dict()
                    st.rerun()
                else: st.error("بيانات غير صحيحة")
        
        with tab_reg:
            n = st.text_input("الاسم", key="n2")
            u2 = st.text_input("يوزر جديد", key="u2")
            p2 = st.text_input("كلمة مرور", type="password", key="p2")
            if st.button("إنشاء حساب ✨", key="btn_reg"):
                users = load_data(USERS_DB)
                if u2 and u2 not in users['username'].values:
                    save_data(pd.concat([users, pd.DataFrame([{"username": u2, "password": p2, "name": n, "role": "student"}])], ignore_index=True), USERS_DB)
                    st.success("تم!")
        st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding: 20px 0;">
            <div style="width: 80px; height: 80px; border-radius: 50%; background: #38bdf8; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 30px; color: white; box-shadow: 0 0 20px #38bdf8;">
                {st.session_state.user['name'][0].upper()}
            </div>
            <h3 style="margin-top: 15px; color: #38bdf8 !important;">{st.session_state.user['name']}</h3>
        </div>
        """, unsafe_allow_html=True)

        menu = option_menu("القائمة", ["لوحة التحكم", "الجدول التفاعلي", "المستشار"], 
            icons=['speedometer', 'table', 'robot'], menu_icon="cast", default_index=0,
            styles={
                "container": {"padding": "5px", "background-color": "#0f172a"}, 
                "icon": {"color": "#38bdf8", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "right", "color": "white", "margin":"5px"}, 
                "nav-link-selected": {"background-color": "#38bdf8", "color": "white"},
            })
        
        st.markdown("---")
        if st.button("تسجيل خروج", key="logout"):
            st.session_state.logged_in = False
            st.rerun()

    tasks = load_data(TASKS_DB)
    my_tasks = tasks if st.session_state.user['role'] == 'admin' else tasks[tasks['الطالب'] == st.session_state.user['username']]

    if menu == "لوحة التحكم":
        st.markdown(f"<h2>مرحباً بك 👋</h2>", unsafe_allow_html=True)
        if not my_tasks.empty:
            pending = my_tasks[my_tasks['إنجاز'] == False]
            completed = my_tasks[my_tasks['إنجاز'] == True]
            c1, c2, c3 = st.columns(3)
            total = int(pending['الدروس'].sum() + pending['المحاضرات'].sum())
            with c1: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>المتبقي</h3><h1>{len(pending)}</h1></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>التراكمات</h3><h1>{total}</h1></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>تم إنجازه ✅</h3><h1>{len(completed)}</h1></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns([1.5, 1])
            with g1:
                pending['الكل'] = pending['الدروس'] + pending['المحاضرات']
                fig = px.bar(pending, x='المادة', y='الأولوية', color='الأولوية', template='plotly_dark', color_continuous_scale='Bluyl')
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", font_color='white', margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig2 = px.pie(pending, values='الكل', names='المادة', hole=0.6, template='plotly_dark')
                fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", font_color='white', margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        else: st.info("لا توجد بيانات.")

    elif menu == "الجدول التفاعلي":
        st.markdown(f"<h2>🤖 الجدول التفاعلي</h2>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        if not my_tasks.empty:
            edited_df = st.data_editor(
                my_tasks.sort_values(by="الأولوية", ascending=False),
                column_config={
                    "إنجاز": st.column_config.CheckboxColumn("تم؟", default=False),
                    "المادة": st.column_config.TextColumn("المادة"),
                    "الأولوية": st.column_config.ProgressColumn("الأهمية", format="%.2f", min_value=0, max_value=100),
                    "الصعوبة": st.column_config.NumberColumn("الصعوبة", format="%d ⭐"),
                    "الأيام": st.column_config.NumberColumn("متبقي (أيام)", format="%d ⏳"),
                },
                disabled=["الطالب"],
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic"
            )
            if st.button("💾 حفظ التعديلات"):
                save_data(edited_df, TASKS_DB)
                st.success("تم التحديث!")
                time.sleep(1)
                st.rerun()
        else: st.info("الجدول فارغ.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif menu == "المستشار":
        st.markdown(f"<h2>🤖 المستشار الذكي</h2>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.info(get_ai_advice(my_tasks))
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.logged_in: main_app()
else: login_page()

components.html("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.2/vanilla-tilt.min.js"></script>
<script>
    document.addEventListener("DOMContentLoaded", function() {
        VanillaTilt.init(document.querySelectorAll('.glass-card'), { max: 5, speed: 400, glare: true, "max-glare": 0.2 });
    });
</script>
""", height=0, width=0)
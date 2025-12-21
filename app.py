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
# 1. إعدادات الصفحة الأساسية
# ---------------------------------------------------------
st.set_page_config(page_title="SmartBacklog Pro", page_icon="🎓", layout="wide")

# تهيئة المتغيرات
if 'theme' not in st.session_state: st.session_state.theme = 'titanium'
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}

# ---------------------------------------------------------
# 2. ألوان التصميم (مضبوطة للموبايل)
# ---------------------------------------------------------
design = {
    'titanium': {
        'sidebar_bg': '#0f172a',
        'glass': 'rgba(15, 23, 42, 0.90)',
        'border': 'rgba(56, 189, 248, 0.5)',
        'input_bg': '#1e293b',  # خلفية حقل الكتابة (غامق)
        'input_text': '#ffffff', # لون الكتابة (أبيض)
        'primary': '#38bdf8',
        'text': '#f8fafc',
        'text_sec': '#94a3b8', 
        'menu_text': '#ffffff',
        'chart_font': '#ffffff',
        'btn_grad': 'linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)',
        'shadow': '0 0 20px rgba(56, 189, 248, 0.2)',
        'lottie_welcome': "https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json",
        'lottie_wait': "https://lottie.host/5a709b1f-d748-4b7d-949f-50a84e27771c/9qj8M4Zz2X.json",
        'chart_template': 'plotly_dark',
        'ai_icon': '🤖'
    },
    'sakura': {
        'sidebar_bg': '#ffffff',
        'glass': 'rgba(255, 255, 255, 0.95)',      
        'border': 'rgba(236, 72, 153, 0.6)',
        'input_bg': '#ffffff',  # خلفية حقل الكتابة (أبيض)
        'input_text': '#831843', # لون الكتابة (نبيتي)
        'primary': '#be185d',
        'text': '#831843',
        'text_sec': '#9d174d',
        'menu_text': '#831843',
        'chart_font': '#831843',
        'btn_grad': 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
        'shadow': '0 10px 25px rgba(236, 72, 153, 0.15)',
        'lottie_welcome': "https://lottie.host/c750516b-4566-4148-89c0-8260a927054f/1I3k9s6X6q.json",
        'lottie_wait': "https://lottie.host/d2d9c049-14a5-4303-9dcd-e06915354972/uOqD6lB0qW.json",
        'chart_template': 'plotly_white',
        'ai_icon': '🧠'
    }
}

theme = design[st.session_state.theme]

# ---------------------------------------------------------
# 3. CSS (بدون إخفاء الشاشة)
# ---------------------------------------------------------
# خلفيات متحركة
bg_css = ""
if st.session_state.theme == 'titanium':
    bg_css = """
    .stApp {
        background-color: #020617;
        background-image: radial-gradient(#38bdf820 1px, transparent 1px);
        background-size: 30px 30px;
    }
    """
else:
    bg_css = """
    .stApp {
        background: linear-gradient(120deg, #fff1f2, #ffe4e6);
        background-size: 200% 200%;
        animation: gradientBG 15s ease infinite;
    }
    @keyframes gradientBG { 0% {background-position:0% 50%} 50% {background-position:100% 50%} 100% {background-position:0% 50%} }
    """

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&family=El+Messiri:wght@500;600;700&display=swap');
* {{ font-family: 'Almarai', sans-serif; }}
h1, h2, h3, .stMetricLabel {{ font-family: 'El Messiri', sans-serif !important; }}

{bg_css}

/* النصوص */
.stApp, p, span, label, div, .stMarkdown {{ color: {theme['text']} !important; }}

/* === إصلاح الموبايل === */
/* إظهار الهيدر عشان زرار القائمة يظهر */
header[data-testid="stHeader"] {{
    background: transparent !important;
    display: block !important;
    visibility: visible !important;
}}

/* تنسيق زر القائمة (Hamburger) */
button[kind="header"] {{
    color: {theme['primary']} !important;
    background: transparent !important;
    border: 1px solid {theme['border']} !important;
}}

/* إخفاء زر الـ Deploy فقط */
.stDeployButton {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}

/* === إصلاح حقول الإدخال === */
.stTextInput input, .stNumberInput input, .stPasswordInput input {{
    background-color: {theme['input_bg']} !important;
    color: {theme['input_text']} !important;
    border: 2px solid {theme['border']} !important;
    border-radius: 12px !important;
    padding: 10px !important;
}}
/* لون النص الإرشادي */
::placeholder {{ color: {theme['text_sec']} !important; opacity: 0.8; }}

/* البطاقات */
.glass-card {{
    background: {theme['glass']};
    backdrop-filter: blur(15px);
    border-radius: 20px; border: 1px solid {theme['border']};
    padding: 25px; margin-bottom: 20px;
    box-shadow: {theme['shadow']};
    color: {theme['text']};
}}

/* الأزرار */
div.stButton > button {{
    background: {theme['btn_grad']}; color: white !important;
    border: none; padding: 12px 20px; border-radius: 15px;
    font-weight: bold; width: 100%;
}}

/* الجدول */
div[data-testid="stDataEditor"] {{
    border: 1px solid {theme['border']}; border-radius: 15px;
}}
div[data-testid="stDataEditor"] div {{ color: {theme['text']} !important; }}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. البيانات والذكاء الاصطناعي
# ---------------------------------------------------------
TASKS_DB = 'smart_tasks.csv'
USERS_DB = 'smart_users.csv'

def init_dbs():
    if not os.path.exists(USERS_DB):
        pd.DataFrame([{"username": "admin", "password": "123", "name": "Admin", "role": "admin"}]).to_csv(USERS_DB, index=False)
    
    if not os.path.exists(TASKS_DB):
        data = {
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
    if 'المحاضرات' not in df.columns and file == TASKS_DB: df['المحاضرات'] = '0'
    return df
def save_data(df, file): df.to_csv(file, index=False)
init_dbs()

# AI Advice
def get_ai_advice(df):
    if df.empty: return "جدولك فارغ!"
    total = df['الدروس'].sum() + df['المحاضرات'].sum()
    urgent = df[df['الأيام'] <= 5]
    advice = f"تحليل ذكي: لديك {int(total)} مهمة متراكمة. "
    if not urgent.empty: advice += f"🔥 انتبه! لديك {len(urgent)} مواد امتحاناتها قريبة."
    elif total > 20: advice += "⚠️ وضعك يحتاج لجدول مكثف."
    else: advice += "✅ وضعك مستقر."
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
        st.markdown('<div class="glass-card">', unsafe_allow_html=True) # شلنا الـ tilt مؤقتاً لضمان الثبات
        
        # زر تبديل الثيم
        col_t, _ = st.columns([1, 3])
        with col_t:
            icon = "🌒" if st.session_state.theme == 'sakura' else "🌸"
            if st.button(icon, key="theme_toggle_login"):
                st.session_state.theme = 'titanium' if st.session_state.theme == 'sakura' else 'sakura'
                st.rerun()

        st.markdown(f"<div style='text-align:center;'><h1>SmartBacklog</h1><p class='small-text'>بوابتك الذكية للتفوق</p></div>", unsafe_allow_html=True)
        st.info("💡 **للجنة التحكيم:** admin | 123")

        if lottie := load_lottie(theme['lottie_welcome']):
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
                else: st.error("خطأ في البيانات")
        
        with tab_reg:
            n = st.text_input("الاسم", key="n2")
            u2 = st.text_input("يوزر جديد", key="u2")
            p2 = st.text_input("كلمة مرور", type="password", key="p2")
            if st.button("انضمام ✨", key="btn_reg"):
                users = load_data(USERS_DB)
                if u2 and u2 not in users['username'].values:
                    save_data(pd.concat([users, pd.DataFrame([{"username": u2, "password": p2, "name": n, "role": "student"}])], ignore_index=True), USERS_DB)
                    st.success("تم!")
        st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    with st.sidebar:
        # زر الثيم
        btn_txt = "الوضع النهاري 🌸" if st.session_state.theme == 'titanium' else "الوضع الليلي 🌒"
        if st.button(btn_txt, use_container_width=True):
            st.session_state.theme = 'sakura' if st.session_state.theme == 'titanium' else 'titanium'
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"<h3 style='text-align:center;'>👤 {st.session_state.user['name']}</h3>", unsafe_allow_html=True)

        menu = option_menu("القائمة", ["الرئيسية", "إضافة مادة", "الخطة", "مستشار الذكاء"], 
            icons=['house', 'plus-circle', 'table', 'robot'], menu_icon="cast", default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"}, 
                "icon": {"color": theme['primary'], "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "right", "color": theme['menu_text'], "margin":"5px"},
                "nav-link-selected": {"background-color": theme['primary'], "color": "#fff"},
            })
        
        st.markdown("---")
        if st.button("خروج", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    tasks = load_data(TASKS_DB)
    for c in ['الدروس', 'المحاضرات', 'الأولوية', 'الصعوبة', 'الأيام']: 
        tasks[c] = pd.to_numeric(tasks[c], errors='coerce').fillna(0)
    
    my_tasks = tasks if st.session_state.user['role'] == 'admin' else tasks[tasks['الطالب'] == st.session_state.user['username']]

    if menu == "الرئيسية":
        st.markdown(f"<h2>أهلاً بك 👋</h2>", unsafe_allow_html=True)
        if not my_tasks.empty:
            c1, c2, c3 = st.columns(3)
            total = int(my_tasks['الدروس'].sum() + my_tasks['المحاضرات'].sum())
            with c1: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>المواد</h3><h1>{len(my_tasks)}</h1></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>التراكمات</h3><h1>{total}</h1></div>', unsafe_allow_html=True)
            top = my_tasks.sort_values("الأولوية").iloc[-1]["المادة"] if len(my_tasks)>0 else "-"
            with c3: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>ابدأ بـ</h3><h1 style="color:{theme["primary"]}">{top}</h1></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns([1.5, 1])
            with g1:
                my_tasks['الكل'] = my_tasks['الدروس'] + my_tasks['المحاضرات']
                fig = px.bar(my_tasks, x='المادة', y='الأولوية', color='الأولوية', template=theme['chart_template'], color_continuous_scale='Bluyl')
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", font_color=theme['chart_font'], margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig2 = px.pie(my_tasks, values='الكل', names='المادة', hole=0.6, template=theme['chart_template'])
                fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", font_color=theme['chart_font'], margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        else: st.info("فارغ")

    elif menu == "إضافة مادة":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("add"):
            c1, c2 = st.columns(2)
            sub = c1.text_input("المادة")
            days = c2.number_input("أيام للامتحان", 1, 365, 7)
            c3, c4 = st.columns(2)
            les = c3.number_input("دروس", 0, 100, 0)
            lec = c4.number_input("محاضرات", 0, 100, 0)
            diff = st.slider("صعوبة", 1, 10, 5)
            if st.form_submit_button("حفظ"):
                prio = (diff * (les + lec)) / days
                save_data(pd.concat([tasks, pd.DataFrame([{
                    "المادة": sub, "الدروس": les, "المحاضرات": lec, "الصعوبة": diff,
                    "الأيام": days, "الأولوية": round(prio, 2), "الطالب": st.session_state.user['username']
                }])], ignore_index=True), TASKS_DB)
                st.success("تم!")
                time.sleep(1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "الخطة":
        if not my_tasks.empty:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.data_editor(my_tasks.sort_values("الأولوية", ascending=False), use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif menu == "مستشار الذكاء":
        st.markdown(f"<h2>{theme['ai_icon']} المستشار الذكي</h2>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.info(get_ai_advice(my_tasks), icon=theme['ai_icon'])
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.logged_in: main_app()
else: login_page()
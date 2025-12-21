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

if 'theme' not in st.session_state: st.session_state.theme = 'titanium'
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}

# ---------------------------------------------------------
# 2. نظام التصميم (الألوان المستقرة V34)
# ---------------------------------------------------------
design = {
    'titanium': {
        'sidebar_bg': 'rgba(10, 15, 30, 0.95)',
        'glass': 'rgba(15, 23, 42, 0.80)',
        'border': 'rgba(56, 189, 248, 0.3)',
        'primary': '#38bdf8',
        'text': '#f8fafc',
        'text_sec': '#cbd5e1', 
        'menu_text': '#ffffff',
        'chart_font': '#ffffff',
        'btn_grad': 'linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)',
        'shadow': '0 0 15px rgba(56, 189, 248, 0.15)',
        'lottie_welcome': "https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json",
        'lottie_wait': "https://lottie.host/5a709b1f-d748-4b7d-949f-50a84e27771c/9qj8M4Zz2X.json",
        'chart_template': 'plotly_dark'
    },
    'sakura': {
        'sidebar_bg': 'rgba(255, 255, 255, 0.95)', 
        'glass': 'rgba(255, 255, 255, 0.90)',      
        'border': 'rgba(244, 114, 182, 0.5)',
        'primary': '#be185d',
        'text': '#831843',
        'text_sec': '#9d174d',
        'menu_text': '#831843',
        'chart_font': '#831843',
        'btn_grad': 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
        'shadow': '0 10px 25px rgba(236, 72, 153, 0.15)',
        'lottie_welcome': "https://lottie.host/c750516b-4566-4148-89c0-8260a927054f/1I3k9s6X6q.json",
        'lottie_wait': "https://lottie.host/d2d9c049-14a5-4303-9dcd-e06915354972/uOqD6lB0qW.json",
        'chart_template': 'plotly_white'
    }
}

theme = design[st.session_state.theme]

# الخلفيات (المستقرة)
bg_css = ""
if st.session_state.theme == 'titanium':
    bg_css = """
    .stApp {
        background-color: #020617 !important;
        background-image: 
            radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.1) 0%, transparent 50%),
            radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 40px),
            radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 30px),
            radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 40px) !important;
        background-size: 100% 100%, 550px 550px, 350px 350px, 250px 250px !important;
        animation: stars 30s linear infinite;
    }
    @keyframes stars {
        0% { background-position: center, 0 0, 0 0; }
        100% { background-position: center, 550px 550px, 350px 350px; }
    }
    """
else:
    bg_css = """
    .stApp {
        background-color: #fff0f5 !important;
        background-image: 
            linear-gradient(120deg, #fff0f5 0%, #ffe4e6 100%),
            radial-gradient(#fbcfe8 1px, transparent 1px) !important;
        background-size: 100% 100%, 25px 25px !important;
    }
    """

# --- CSS Styling (الآمن + تحسين الحقول) ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&family=El+Messiri:wght@500;600;700&display=swap');
* {{ font-family: 'Almarai', sans-serif; }}
h1, h2, h3, .stMetricLabel {{ 
    font-family: 'El Messiri', sans-serif !important; 
    letter-spacing: 0.5px;
}}

{bg_css}

/* إجبار النصوص العامة */
.stApp, p, span, label, div, .stMarkdown {{ 
    color: {theme['text']} !important; 
}}

/* ========================================= */
/* 📱 إعدادات الموبايل + الإخفاء الآمن 📱 */
/* ========================================= */

header[data-testid="stHeader"] {{
    background-color: transparent !important;
    display: block !important; visibility: visible !important;
}}

/* زر القائمة للموبايل */
button[kind="header"] {{
    background-color: transparent !important;
    color: {theme['primary']} !important;
    border: 1px solid {theme['primary']} !important;
    border-radius: 8px !important;
    display: block !important; visibility: visible !important;
}}
button[kind="header"]:hover {{
    background-color: {theme['primary']}10 !important;
}}

[data-testid="stToolbar"] {{ display: none !important; }}
footer, .stFooter, .stDeployButton {{ display: none !important; }}
.block-container {{ padding-top: 2rem !important; }}

/* ========================================= */

/* القائمة الجانبية */
section[data-testid="stSidebar"] {{
    background-color: {theme['sidebar_bg']} !important;
    backdrop-filter: blur(25px); border-right: 1px solid {theme['border']};
}}

section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div {{
    color: {theme['menu_text']} !important; font-weight: 500;
}}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{
    color: {theme['primary']} !important;
}}

/* البطاقات */
.glass-card {{
    background: {theme['glass']};
    backdrop-filter: blur(20px);
    border-radius: 20px; border: 1px solid {theme['border']};
    padding: 25px; margin-bottom: 20px;
    box-shadow: {theme['shadow']};
    transform-style: preserve-3d; transform: perspective(1000px);
    color: {theme['text']};
}}

/* الأزرار */
div.stButton > button {{
    background: {theme['btn_grad']}; color: white !important; 
    border: none; padding: 12px 24px; border-radius: 15px; 
    font-weight: 700; width: 100%; transition: all 0.2s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}
div.stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.2); }}

/* --- تحسين حقول الإدخال (النسخة الآمنة) --- */
/* نجعل الخلفية شبه شفافة لكي تظهر على أي ثيم، مع حدود واضحة */
.stTextInput input, .stNumberInput input, .stPasswordInput input {{
    background: rgba(255, 255, 255, 0.15) !important; /* خلفية موحدة شفافة */
    border: 2px solid {theme['border']} !important; /* حدود اسمك */
    color: {theme['text']} !important; 
    border-radius: 12px !important;
    padding: 10px !important;
    font-weight: 600 !important; /* خط أثقل */
}}
.stTextInput input:focus, .stNumberInput input:focus {{
    border-color: {theme['primary']} !important;
    background: rgba(255, 255, 255, 0.25) !important; /* تفتيح عند الضغط */
}}
::placeholder {{ color: {theme['text_sec']} !important; opacity: 0.8; }}

/* الجدول */
div[data-testid="stDataEditor"] {{
    border: 1px solid {theme['border']}; border-radius: 15px; overflow: hidden;
}}
div[data-testid="stDataEditor"] div {{
    color: {theme['text']} !important; 
}}

h1, h2, h3 {{ color: {theme['primary']} !important; text-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
.small-text {{ color: {theme['text_sec']} !important; font-size: 0.85rem; }}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. إدارة البيانات
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

@st.cache_data
def load_lottie(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

def play_sound():
    st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2000/2000-preview.mp3" type="audio/mp3"></audio>""", unsafe_allow_html=True)

quotes = ["ألم الدراسة لحظة، لكن ألم الندم مدى الحياة.", "لا تتوقف عندما تتعب، توقف عندما تنتهي.", "أحلامك تستحق منك المحاولة.", "كن قوياً لأجلك."]

# ---------------------------------------------------------
# 4. الواجهة
# ---------------------------------------------------------
def login_page():
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        st.write("")
        st.markdown('<div class="glass-card" data-tilt>', unsafe_allow_html=True)
        
        col_t, col_e = st.columns([1, 3])
        with col_t:
            icon = "🌒" if st.session_state.theme == 'sakura' else "🌸"
            if st.button(icon, key="theme_toggle_login"):
                st.session_state.theme = 'titanium' if st.session_state.theme == 'sakura' else 'sakura'
                st.rerun()
        
        st.markdown(f"<div style='text-align:center; margin-top:10px;'><h1>SmartBacklog</h1><p class='small-text'>بوابتك الذكية للتفوق الدراسي</p></div>", unsafe_allow_html=True)
        st.info("💡 **للجنة التحكيم:** المستخدم: `admin` | المرور: `123`")

        if lottie := load_lottie(theme['lottie_welcome']):
            st_lottie(lottie, height=180, key="welcome")

        tab_log, tab_reg = st.tabs(["دخول", "حساب جديد"])
        
        with tab_log:
            # استخدام placeholder لتوضيح الحقول على الموبايل
            u = st.text_input("اسم المستخدم", key="u1", placeholder="أدخل اسم المستخدم هنا...")
            p = st.text_input("كلمة المرور", type="password", key="p1", placeholder="أدخل كلمة المرور...")
            if st.button("دخول النظام 🚀"):
                users = load_data(USERS_DB)
                found = users[(users['username'] == u) & (users['password'] == p)]
                if not found.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = found.iloc[0].to_dict()
                    st.rerun()
                else: st.error("البيانات غير صحيحة")
        
        with tab_reg:
            n = st.text_input("الاسم", key="n2", placeholder="اسمك الثنائي")
            u2 = st.text_input("يوزر جديد", key="u2", placeholder="اختر اسم مستخدم")
            p2 = st.text_input("كلمة مرور", type="password", key="p2", placeholder="كلمة مرور قوية")
            if st.button("انضم إلينا ✨"):
                users = load_data(USERS_DB)
                if u2 in users['username'].values: st.error("مستخدم")
                elif u2:
                    save_data(pd.concat([users, pd.DataFrame([{"username": u2, "password": p2, "name": n, "role": "student"}])], ignore_index=True), USERS_DB)
                    st.success("تم الإنشاء!")
        st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    with st.sidebar:
        theme_btn_label = "تفعيل الوضع النهاري 🌸" if st.session_state.theme == 'titanium' else "تفعيل الوضع الليلي 🌒"
        if st.button(theme_btn_label, use_container_width=True):
            st.session_state.theme = 'sakura' if st.session_state.theme == 'titanium' else 'titanium'
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align:center; margin-bottom: 20px;">
            <div style="width: 80px; height: 80px; border-radius: 50%; background: {theme['primary']}; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 30px; color: white; box-shadow: 0 0 15px {theme['primary']}50;">
                {st.session_state.user['name'][0].upper()}
            </div>
            <h3 style="margin-top: 15px; color: {theme['primary']} !important;">{st.session_state.user['name']}</h3>
        </div>
        """, unsafe_allow_html=True)

        menu = option_menu("القائمة", ["الرئيسية", "إضافة مادة", "الخطة"], 
            icons=['house', 'plus-circle', 'table'], menu_icon="cast", default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"}, 
                "icon": {"color": theme['primary'], "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "right", "color": theme['menu_text'], "margin":"5px"},
                "nav-link-selected": {"background-color": theme['primary'], "color": "#fff", "box-shadow": f"0 4px 10px {theme['primary']}40"},
            })
        
        st.markdown("---")
        if st.button("تسجيل خروج", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    tasks = load_data(TASKS_DB)
    for c in ['الدروس', 'المحاضرات', 'الأولوية', 'الصعوبة', 'الأيام']: 
        tasks[c] = pd.to_numeric(tasks[c], errors='coerce').fillna(0)
    
    my_tasks = tasks if st.session_state.user['role'] == 'admin' else tasks[tasks['الطالب'] == st.session_state.user['username']]

    if menu == "الرئيسية":
        st.markdown(f"<h2>أهلاً بك 👋</h2>", unsafe_allow_html=True)
        st.caption(random.choice(quotes))
        
        if not my_tasks.empty:
            c1, c2, c3 = st.columns(3)
            total = int(my_tasks['الدروس'].sum() + my_tasks['المحاضرات'].sum())
            with c1: st.markdown(f'<div class="glass-card" data-tilt style="text-align:center"><h3>المواد</h3><h1>{len(my_tasks)}</h1></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="glass-card" data-tilt style="text-align:center"><h3>التراكمات</h3><h1>{total}</h1></div>', unsafe_allow_html=True)
            top = my_tasks.sort_values("الأولوية").iloc[-1]["المادة"] if len(my_tasks)>0 else "-"
            with c3: st.markdown(f'<div class="glass-card" data-tilt style="text-align:center"><h3>ابدأ بـ</h3><h1 style="color:{theme["primary"]}">{top}</h1></div>', unsafe_allow_html=True)
            
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
        else: st.info("القائمة فارغة.")

    elif menu == "إضافة مادة":
        col_f, col_a = st.columns([2, 1])
        with col_a:
            if lottie_w := load_lottie(theme['lottie_wait']): st_lottie(lottie_w, height=200)
        
        with col_f:
            st.markdown('<div class="glass-card" data-tilt>', unsafe_allow_html=True)
            with st.form("add_task_form"):
                c1, c2 = st.columns(2)
                sub = c1.text_input("اسم المادة", placeholder="مثال: فيزياء")
                days = c2.number_input("أيام للامتحان", 1, 365, 7)
                c3, c4 = st.columns(2)
                les = c3.number_input("دروس متراكمة", 0, 100, 0)
                lec = c4.number_input("محاضرات متراكمة", 0, 100, 0)
                diff = st.slider("الصعوبة", 1, 10, 5)
                
                if st.form_submit_button("حفظ"):
                    if sub and (les > 0 or lec > 0):
                        prio = (diff * (les + lec)) / days
                        save_data(pd.concat([tasks, pd.DataFrame([{
                            "المادة": sub, "الدروس": les, "المحاضرات": lec, "الصعوبة": diff,
                            "الأيام": days, "الأولوية": round(prio, 2), "الطالب": st.session_state.user['username']
                        }])], ignore_index=True), TASKS_DB)
                        play_sound()
                        st.balloons()
                        st.success("تم!")
                        time.sleep(1)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "الخطة":
        if not my_tasks.empty:
            st.markdown('<div class="glass-card" data-tilt>', unsafe_allow_html=True)
            st.data_editor(
                my_tasks.sort_values(by="الأولوية", ascending=False),
                column_config={
                    "الأولوية": st.column_config.ProgressColumn("الأهمية", format="%.2f", min_value=0, max_value=max(my_tasks['الأولوية'].max(), 10)),
                    "الصعوبة": st.column_config.NumberColumn("الصعوبة", format="%d ⭐"),
                    "الأيام": st.column_config.NumberColumn("الوقت", format="%d يوم ⏳"),
                },
                hide_index=True, use_container_width=True, disabled=["الأولوية", "الطالب"]
            )
            st.markdown('</div>', unsafe_allow_html=True)
            csv = my_tasks.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل الجدول", csv, "Plan.csv", "text/csv", use_container_width=True)
        else: st.info("فارغ.")

if st.session_state.logged_in: main_app()
else: login_page()

# ---------------------------------------------------------
# 5. JS 3D Effect
# ---------------------------------------------------------
components.html("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.2/vanilla-tilt.min.js"></script>
<script>
    document.addEventListener("DOMContentLoaded", function() {
        function initTilt() {
            var cards = window.parent.document.querySelectorAll('.glass-card');
            VanillaTilt.init(cards, {
                max: 10, speed: 400, glare: true, "max-glare": 0.2, scale: 1.01
            });
        }
        setTimeout(initTilt, 1000);
        setInterval(initTilt, 3000);
    });
</script>
""", height=0, width=0)
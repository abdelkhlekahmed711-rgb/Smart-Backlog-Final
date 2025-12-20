import streamlit as st
import pandas as pd
import plotly.express as px
import os
import requests
import time
import random
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
# 2. نظام التصميم
# ---------------------------------------------------------
design = {
    'titanium': {
        'sidebar_bg': 'rgba(15, 23, 42, 0.9)',
        'glass': 'rgba(15, 23, 42, 0.7)',
        'border': 'rgba(255, 255, 255, 0.1)',
        'primary': '#38bdf8',
        'text': '#f1f5f9',
        'menu_text': '#f1f5f9',
        'btn_grad': 'linear-gradient(90deg, #0ea5e9, #2563eb)',
        'lottie_welcome': "https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json",
        'lottie_wait': "https://lottie.host/5a709b1f-d748-4b7d-949f-50a84e27771c/9qj8M4Zz2X.json",
        'chart_theme': 'plotly_dark'
    },
    'sakura': {
        'sidebar_bg': 'rgba(255, 240, 245, 0.85)',
        'glass': 'rgba(255, 255, 255, 0.65)',
        'border': 'rgba(255, 182, 193, 0.8)',
        'primary': '#db2777',
        'text': '#4a4a4a', 
        'menu_text': '#4a4a4a',
        'btn_grad': 'linear-gradient(90deg, #ec4899, #d946ef)',
        'lottie_welcome': "https://lottie.host/c750516b-4566-4148-89c0-8260a927054f/1I3k9s6X6q.json",
        'lottie_wait': "https://lottie.host/d2d9c049-14a5-4303-9dcd-e06915354972/uOqD6lB0qW.json",
        'chart_theme': 'plotly_white'
    }
}

theme = design[st.session_state.theme]

# الخلفيات
bg_css = ""
if st.session_state.theme == 'titanium':
    bg_css = """
    .stApp {
        background-color: #020617;
        background-image: 
            radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 40px),
            radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 30px),
            radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 40px);
        background-size: 550px 550px, 350px 350px, 250px 250px;
        animation: stars 20s linear infinite;
    }
    @keyframes stars {
        0% { background-position: 0 0, 0 0, 0 0; }
        100% { background-position: 550px 550px, 350px 350px, 250px 250px; }
    }
    """
else:
    bg_css = """
    .stApp {
        background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #ffd1ff);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    """

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&family=El+Messiri:wght@400;500;600;700&display=swap');
* {{ font-family: 'Almarai', sans-serif; }}
h1, h2, h3, .stMetricLabel {{ font-family: 'El Messiri', sans-serif !important; }}

{bg_css}

/* --- هنا كود الإخفاء الجديد (Clean Mode) --- */
/* إخفاء القائمة العلوية (3 شرط) والشريط العلوي */
#MainMenu {{visibility: hidden;}}
header {{visibility: hidden;}}
footer {{visibility: hidden;}}
[data-testid="stToolbar"] {{visibility: hidden; top: -50px;}} /* إخفاء شريط Share و GitHub */
/* ------------------------------------------ */

section[data-testid="stSidebar"] {{
    background-color: {theme['sidebar_bg']} !important;
    backdrop-filter: blur(20px); border-right: 1px solid {theme['border']};
}}

section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div {{
    color: {theme['menu_text']} !important;
}}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{
    color: {theme['primary']} !important;
}}

.glass-card {{
    background: {theme['glass']};
    backdrop-filter: blur(16px);
    border-radius: 24px; border: 1px solid {theme['border']};
    padding: 30px; margin-bottom: 25px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
    transition: transform 0.3s;
}}
.glass-card:hover {{ transform: translateY(-5px); }}

div.stButton > button {{
    background: {theme['btn_grad']}; color: white; border: none; padding: 10px 24px;
    border-radius: 12px; font-weight: bold; width: 100%; transition: 0.3s;
}}
div.stButton > button:hover {{ transform: scale(1.02); }}

.stTextInput input, .stNumberInput input, .stPasswordInput input {{
    background: rgba(255, 255, 255, 0.2) !important;
    border: 1px solid {theme['border']} !important;
    color: {theme['text']} !important; border-radius: 12px !important;
}}

h1, h2, h3 {{ color: {theme['primary']} !important; }}
p, span, label, div {{ color: {theme['text']}; }}

.block-container {{ padding-top: 0rem; }} /* تقليل المسافة العلوية لأننا أخفينا الشريط */
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
        pd.DataFrame(columns=["المادة", "الدروس", "المحاضرات", "الصعوبة", "الأيام", "الأولوية", "الطالب"]).to_csv(TASKS_DB, index=False)

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
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        cl, cr = st.columns(2)
        with cl: 
            if st.button("🌑 Titanium", key="thm_b", use_container_width=True): st.session_state.theme = 'titanium'; st.rerun()
        with cr: 
            if st.button("🌸 Sakura", key="thm_g", use_container_width=True): st.session_state.theme = 'sakura'; st.rerun()

        st.markdown(f"<div style='text-align:center; margin-top:20px;'><h1>SmartBacklog</h1><p class='small-text'>بوابتك الذكية للتفوق الدراسي</p></div>", unsafe_allow_html=True)
        
        if lottie := load_lottie(theme['lottie_welcome']):
            st_lottie(lottie, height=180, key="welcome")

        tab_log, tab_reg = st.tabs(["دخول", "حساب جديد"])
        
        with tab_log:
            u = st.text_input("اسم المستخدم", key="u1")
            p = st.text_input("كلمة المرور", type="password", key="p1")
            if st.button("دخول النظام 🚀"):
                users = load_data(USERS_DB)
                found = users[(users['username'] == u) & (users['password'] == p)]
                if not found.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = found.iloc[0].to_dict()
                    st.rerun()
                else: st.error("البيانات غير صحيحة")
        
        with tab_reg:
            n = st.text_input("الاسم", key="n2")
            u2 = st.text_input("يوزر جديد", key="u2")
            p2 = st.text_input("كلمة مرور", type="password", key="p2")
            if st.button("انضم إلينا ✨"):
                users = load_data(USERS_DB)
                if u2 in users['username'].values: st.error("مستخدم")
                elif u2:
                    save_data(pd.concat([users, pd.DataFrame([{"username": u2, "password": p2, "name": n, "role": "student"}])], ignore_index=True), USERS_DB)
                    st.success("تم الإنشاء!")
        st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom: 20px;">
            <div style="width: 80px; height: 80px; border-radius: 50%; background: {theme['primary']}; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 30px; color: white;">
                {st.session_state.user['name'][0].upper()}
            </div>
            <h3 style="margin-top: 10px; color: {theme['primary']} !important;">{st.session_state.user['name']}</h3>
        </div>
        """, unsafe_allow_html=True)

        menu = option_menu("القائمة", ["الرئيسية", "إضافة مادة", "الخطة"], 
            icons=['house', 'plus-circle', 'table'], menu_icon="cast", default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"}, 
                "icon": {"color": theme['primary'], "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "right", "color": theme['menu_text'], "margin":"5px"},
                "nav-link-selected": {"background-color": theme['primary'], "color": "#fff"},
            })
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        if c1.button("🌑"): st.session_state.theme = 'titanium'; st.rerun()
        if c2.button("🌸"): st.session_state.theme = 'sakura'; st.rerun()
        if st.button("خروج", key="logout"): st.session_state.logged_in = False; st.rerun()

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
            with c1: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>المواد</h3><h1>{len(my_tasks)}</h1></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>التراكمات</h3><h1>{total}</h1></div>', unsafe_allow_html=True)
            top = my_tasks.sort_values("الأولوية").iloc[-1]["المادة"] if len(my_tasks)>0 else "-"
            with c3: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>ابدأ بـ</h3><h1>{top}</h1></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns([1.5, 1])
            with g1:
                fig = px.bar(my_tasks, x='المادة', y='الأولوية', color='الأولوية', template=theme['chart_theme'], color_continuous_scale='Bluyl')
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                my_tasks['الكل'] = my_tasks['الدروس'] + my_tasks['المحاضرات']
                fig2 = px.pie(my_tasks, values='الكل', names='المادة', hole=0.6, template=theme['chart_theme'])
                fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        else: st.info("القائمة فارغة.")

    elif menu == "إضافة مادة":
        col_f, col_a = st.columns([2, 1])
        with col_a:
            if lottie_w := load_lottie(theme['lottie_wait']): st_lottie(lottie_w, height=200)
        
        with col_f:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            with st.form("add_task_form"):
                c1, c2 = st.columns(2)
                sub = c1.text_input("اسم المادة")
                days = c2.number_input("أيام للامتحان", 1, 365, 7)
                c3, c4 = st.columns(2)
                les = c3.number_input("دروس", 0, 100, 0)
                lec = c4.number_input("محاضرات", 0, 100, 0)
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
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
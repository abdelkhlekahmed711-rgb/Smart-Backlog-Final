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
# 2. نظام التصميم الموحد (The Ultimate Theme)
# ---------------------------------------------------------
theme = {
    'bg_color': '#020617',           # خلفية الصفحة (كحلي غامق جداً)
    'sidebar_bg': '#0f172a',         # خلفية القائمة
    'glass': 'rgba(30, 41, 59, 0.70)', # لون الزجاج (رمادي مزرق شفاف)
    'border': 'rgba(56, 189, 248, 0.5)', # حدود زرقاء سماوية
    'primary': '#38bdf8',            # اللون الأساسي (أزرق سماوي)
    'text': '#f1f5f9',               # لون النصوص (أبيض مائل للرمادي الفاتح - مريح للعين)
    'text_sec': '#94a3b8',           # نصوص ثانوية
    'input_bg': '#1e293b',           # خلفية حقول الإدخال (واضحة جداً)
    'input_text': '#ffffff',         # نص الإدخال (أبيض ناصع)
    'btn_grad': 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)', # تدرج الأزرار
    'shadow': '0 8px 32px rgba(0, 0, 0, 0.3)', # ظل عميق
    'chart_template': 'plotly_dark',
    'lottie_welcome': "https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json",
    'lottie_wait': "https://lottie.host/5a709b1f-d748-4b7d-949f-50a84e27771c/9qj8M4Zz2X.json",
    'ai_icon': '🤖'
}

# ---------------------------------------------------------
# 3. CSS (مضبوط بالمللي للموبايل والكمبيوتر)
# ---------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&family=El+Messiri:wght@400;500;600;700&display=swap');
* {{ font-family: 'Almarai', sans-serif; }}
h1, h2, h3, .stMetricLabel {{ font-family: 'El Messiri', sans-serif !important; letter-spacing: 0.5px; }}

/* خلفية الصفحة مع النجوم المتحركة */
.stApp {{
    background-color: {theme['bg_color']} !important;
    background-image: radial-gradient(white 1px, transparent 1px);
    background-size: 50px 50px;
    animation: stars 60s linear infinite;
}}
@keyframes stars {{ 0% {{background-position: 0 0;}} 100% {{background-position: 50px 50px;}} }}

/* توحيد لون النصوص */
.stApp, p, span, label, div, .stMarkdown, h1, h2, h3, h4, h5, h6 {{ color: {theme['text']} !important; }}
.small-text {{ color: {theme['text_sec']} !important; font-size: 0.85rem; }}

/* === 📱 تحسينات الموبايل 📱 === */
/* إجبار الهيدر على الظهور لزر القائمة */
header[data-testid="stHeader"] {{
    background: transparent !important;
    display: block !important; visibility: visible !important;
    z-index: 999;
}}
/* زر القائمة (Hamburger) */
button[kind="header"] {{
    color: {theme['primary']} !important;
    background: {theme['input_bg']} !important;
    border: 1px solid {theme['border']} !important;
    border-radius: 8px !important;
}}

/* إخفاء العناصر غير الضرورية */
.stDeployButton, [data-testid="stDecoration"], footer {{ display: none !important; }}

/* القائمة الجانبية */
section[data-testid="stSidebar"] {{
    background-color: {theme['sidebar_bg']} !important;
    border-right: 1px solid {theme['border']};
}}
/* نصوص القائمة */
[data-testid="stSidebar"] * {{ color: {theme['text']} !important; }}

/* === 🔧 حقول الإدخال (الأهم) === */
.stTextInput input, .stNumberInput input, .stPasswordInput input {{
    background-color: {theme['input_bg']} !important;
    color: {theme['input_text']} !important;
    border: 2px solid {theme['border']} !important;
    border-radius: 12px !important;
    padding: 12px !important;
    font-weight: 600 !important;
}}
/* لون النص الإرشادي */
::placeholder {{ color: {theme['text_sec']} !important; opacity: 0.7; }}

/* البطاقات الزجاجية */
.glass-card {{
    background: {theme['glass']};
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border-radius: 24px; border: 1px solid {theme['border']};
    padding: 30px; margin-bottom: 25px;
    box-shadow: {theme['shadow']};
}}

/* الأزرار */
div.stButton > button {{
    background: {theme['btn_grad']}; color: white !important;
    border: none; padding: 12px 24px; border-radius: 15px;
    font-weight: bold; width: 100%; transition: 0.3s;
}}
div.stButton > button:hover {{ transform: scale(1.02); box-shadow: 0 0 15px {theme['primary']}; }}

/* الجداول والرسوم */
div[data-testid="stDataEditor"] {{
    border: 1px solid {theme['border']}; border-radius: 15px;
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

# --- 🧠 الذكاء الاصطناعي (تحفيز + تحليل) ---
motivational_quotes = [
    "النجاح ليس صدفة، إنه عمل شاق، مثابرة، تعلم، وتضحية.",
    "لا تؤجل عمل اليوم إلى الغد، فالغد لديه أشغاله أيضاً.",
    "قمة الجبل لا يصل إليها إلا من تسلق الصخور.",
    "كل دقيقة ألم في الدراسة تمنحك سنوات من الراحة في المستقبل.",
    "أنت أقوى مما تتخيل، وأذكى مما تظن.",
    "الفرق بين المستحيل والممكن يتوقف على عزيمتك."
]

def get_ai_advice(df):
    if df.empty: return "جدولك فارغ! ابدأ الآن. 🚀"
    total = df['الدروس'].sum() + df['المحاضرات'].sum()
    urgent = df[df['الأيام'] <= 5]
    quote = random.choice(motivational_quotes)
    
    advice = f"📊 **تحليل:** لديك {int(total)} مهمة.\n"
    if total > 20: advice += "⚡ **نصيحة:** التراكمات كثيرة، ركز على مادة واحدة اليوم."
    else: advice += "✅ **نصيحة:** وضعك مستقر، استمر."
    
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
        st.markdown(f"<div style='text-align:center;'><h1>SmartBacklog</h1><p class='small-text'>الإصدار الاحترافي</p></div>", unsafe_allow_html=True)
        st.info("💡 **للجنة التحكيم:** admin | 123")

        if lottie := load_lottie(theme['lottie_welcome']):
            st_lottie(lottie, height=180, key="welcome")

        tab_log, tab_reg = st.tabs(["تسجيل دخول", "حساب جديد"])
        
        with tab_log:
            u = st.text_input("اسم المستخدم", key="u1", placeholder="مثال: admin")
            p = st.text_input("كلمة المرور", type="password", key="p1", placeholder="******")
            if st.button("دخول للنظام 🚀", key="btn_login"):
                users = load_data(USERS_DB)
                found = users[(users['username'] == u) & (users['password'] == p)]
                if not found.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = found.iloc[0].to_dict()
                    st.rerun()
                else: st.error("بيانات غير صحيحة")
        
        with tab_reg:
            n = st.text_input("الاسم الكامل", key="n2")
            u2 = st.text_input("اسم مستخدم جديد", key="u2")
            p2 = st.text_input("كلمة مرور جديدة", type="password", key="p2")
            if st.button("إنشاء حساب ✨", key="btn_reg"):
                users = load_data(USERS_DB)
                if u2 and u2 not in users['username'].values:
                    save_data(pd.concat([users, pd.DataFrame([{"username": u2, "password": p2, "name": n, "role": "student"}])], ignore_index=True), USERS_DB)
                    st.success("تم الإنشاء بنجاح!")
        st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding: 20px 0;">
            <div style="width: 80px; height: 80px; border-radius: 50%; background: {theme['primary']}; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 30px; color: white; box-shadow: 0 0 20px {theme['primary']};">
                {st.session_state.user['name'][0].upper()}
            </div>
            <h3 style="margin-top: 15px; color: {theme['primary']} !important;">{st.session_state.user['name']}</h3>
        </div>
        """, unsafe_allow_html=True)

        menu = option_menu("القائمة", ["لوحة التحكم", "إضافة مهام", "الجدول الذكي", "المستشار"], 
            icons=['speedometer', 'plus-square', 'table', 'robot'], menu_icon="cast", default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"}, 
                "icon": {"color": theme['primary'], "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "right", "color": theme['text'], "margin":"5px"},
                "nav-link-selected": {"background-color": theme['primary'], "color": "#fff"},
            })
        
        st.markdown("---")
        if st.button("تسجيل خروج", key="logout"):
            st.session_state.logged_in = False
            st.rerun()

    tasks = load_data(TASKS_DB)
    for c in ['الدروس', 'المحاضرات', 'الأولوية', 'الصعوبة', 'الأيام']: 
        tasks[c] = pd.to_numeric(tasks[c], errors='coerce').fillna(0)
    
    my_tasks = tasks if st.session_state.user['role'] == 'admin' else tasks[tasks['الطالب'] == st.session_state.user['username']]

    if menu == "لوحة التحكم":
        st.markdown(f"<h2>مرحباً بك 👋</h2>", unsafe_allow_html=True)
        if not my_tasks.empty:
            c1, c2, c3 = st.columns(3)
            total = int(my_tasks['الدروس'].sum() + my_tasks['المحاضرات'].sum())
            with c1: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>المواد</h3><h1>{len(my_tasks)}</h1></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>التراكمات</h3><h1>{total}</h1></div>', unsafe_allow_html=True)
            top = my_tasks.sort_values("الأولوية").iloc[-1]["المادة"] if len(my_tasks)>0 else "-"
            with c3: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>الأولوية لـ</h3><h1 style="color:{theme["primary"]}">{top}</h1></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns([1.5, 1])
            with g1:
                my_tasks['الكل'] = my_tasks['الدروس'] + my_tasks['المحاضرات']
                fig = px.bar(my_tasks, x='المادة', y='الأولوية', color='الأولوية', template=theme['chart_template'], color_continuous_scale='Bluyl')
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", font_color='white', margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig2 = px.pie(my_tasks, values='الكل', names='المادة', hole=0.6, template=theme['chart_template'])
                fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", font_color='white', margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        else: st.info("لا توجد بيانات لعرضها.")

    elif menu == "إضافة مهام":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("add"):
            c1, c2 = st.columns(2)
            sub = c1.text_input("اسم المادة", placeholder="مثال: فيزياء")
            days = c2.number_input("أيام للامتحان", 1, 365, 7)
            c3, c4 = st.columns(2)
            les = c3.number_input("دروس متراكمة", 0, 100, 0)
            lec = c4.number_input("محاضرات متراكمة", 0, 100, 0)
            diff = st.slider("درجة الصعوبة", 1, 10, 5)
            if st.form_submit_button("حفظ البيانات"):
                prio = (diff * (les + lec)) / days
                save_data(pd.concat([tasks, pd.DataFrame([{
                    "المادة": sub, "الدروس": les, "المحاضرات": lec, "الصعوبة": diff,
                    "الأيام": days, "الأولوية": round(prio, 2), "الطالب": st.session_state.user['username']
                }])], ignore_index=True), TASKS_DB)
                st.success("تم الحفظ بنجاح!")
                time.sleep(1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "الجدول الذكي":
        if not my_tasks.empty:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.data_editor(my_tasks.sort_values("الأولوية", ascending=False), use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
            csv = my_tasks.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل الجدول (Excel)", csv, "Plan.csv", "text/csv", use_container_width=True)
    
    elif menu == "المستشار":
        st.markdown(f"<h2>{theme['ai_icon']} المستشار الذكي</h2>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.info(get_ai_advice(my_tasks), icon=theme['ai_icon'])
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.logged_in: main_app()
else: login_page()

# تأثيرات بسيطة للبطاقات
components.html("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.2/vanilla-tilt.min.js"></script>
<script>
    document.addEventListener("DOMContentLoaded", function() {
        VanillaTilt.init(document.querySelectorAll('.glass-card'), { max: 5, speed: 400, glare: true, "max-glare": 0.2 });
    });
</script>
""", height=0, width=0)
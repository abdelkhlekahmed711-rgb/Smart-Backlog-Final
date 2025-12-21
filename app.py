import streamlit as st
import pandas as pd
import plotly.express as px
import os
import requests
import time
import random
import math
from datetime import date, timedelta
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(page_title="SmartBacklog Pro", page_icon="🎓", layout="wide")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'messages' not in st.session_state: 
    st.session_state.messages = [{"role": "assistant", "content": "أهلاً يا بطل! أنا المستشار الأكاديمي. جاهز نكسر التراكمات؟"}]

# ---------------------------------------------------------
# 2. التصميم (CSS)
# ---------------------------------------------------------
colors = {
    'bg_dark': '#0f172a',
    'primary': '#38bdf8',
    'text': '#ffffff',
    'input_bg': '#1e293b',
    'border': 'rgba(56, 189, 248, 0.3)', 
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&family=El+Messiri:wght@400;500;600;700&display=swap');

@keyframes gradientBG {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}
.stApp {{
    background: linear-gradient(-45deg, #020617, #0f172a, #1e293b, #000000);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}}

* {{ font-family: 'Almarai', sans-serif; }}
h1, h2, h3, h4, h5, h6, .stMetricLabel {{ 
    font-family: 'El Messiri', sans-serif !important; 
    color: white !important;
}}
p, span, label, div, .stMarkdown {{ color: #e2e8f0 !important; }}

section[data-testid="stSidebar"] {{
    background-color: rgba(15, 23, 42, 0.98) !important;
    border-right: 1px solid {colors['border']};
}}

input, textarea, select, .stTextInput > div > div > input, .stSelectbox > div > div > div {{
    background-color: {colors['input_bg']} !important;
    color: white !important;
    border: 1px solid {colors['border']} !important;
}}
.stDateInput > div > div > input {{ color: white !important; }}

[data-testid="stDataEditor"] {{
    border: 1px solid {colors['border']};
    border-radius: 10px;
    background-color: {colors['input_bg']} !important;
}}

.stChatMessage {{ background-color: rgba(30, 41, 59, 0.8) !important; border-radius: 15px; border: 1px solid {colors['border']}; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stDeployButton, [data-testid="stDecoration"], footer {{ display: none !important; }}

div.stButton > button {{
    background: linear-gradient(90deg, #0ea5e9, #2563eb);
    color: white !important; border: none;
    padding: 10px 20px; border-radius: 10px;
    font-weight: bold; width: 100%;
}}

.glass-card {{
    background: rgba(30, 41, 59, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid {colors['border']};
    border-radius: 20px;
    padding: 20px; margin-bottom: 20px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. شريط التقدم
# ---------------------------------------------------------
def render_custom_progress_bar(percentage):
    if percentage < 30:
        bar_color, emoji = "#ef4444", "😟"
    elif percentage < 70:
        bar_color, emoji = "#eab308", "😐"
    else:
        bar_color, emoji = "#22c55e", "🤩"
    
    st.markdown(f"""
    <div style="margin-bottom: 20px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span style="font-weight:bold; color:white;">الإنجاز {emoji}</span>
            <span style="font-weight:bold; color:{bar_color};">{percentage:.1f}%</span>
        </div>
        <div style="width: 100%; background-color: rgba(255,255,255,0.1); border-radius: 10px; height: 10px;">
            <div style="width: {percentage}%; background-color: {bar_color}; height: 10px; border-radius: 10px; transition: width 0.5s;"></div>
        </div>
    </div>
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
            "إنجاز": [False], "المادة": ["تجربة"], "الدروس": [1], "المحاضرات": [0],
            "الصعوبة": [5], "الأيام": [10], "الأولوية": [50.0], "تاريخ_التنفيذ": [str(date.today())], "الطالب": ["admin"]
        }
        pd.DataFrame(data).to_csv(TASKS_DB, index=False)

def load_data(file): 
    try:
        df = pd.read_csv(file, dtype=str)
    except:
        return pd.DataFrame()

    if file == TASKS_DB:
        cols = ['إنجاز', 'المادة', 'الدروس', 'المحاضرات', 'الصعوبة', 'الأيام', 'الأولوية', 'تاريخ_التنفيذ', 'الطالب']
        for c in cols:
            if c not in df.columns: df[c] = '0' if c not in ['المادة', 'الطالب', 'تاريخ_التنفيذ'] else ''
            
        df['تاريخ_التنفيذ'] = pd.to_datetime(df['تاريخ_التنفيذ'], errors='coerce').dt.date
        df.loc[df['تاريخ_التنفيذ'].isna(), 'تاريخ_التنفيذ'] = date.today()
        
        for c in ['الدروس', 'المحاضرات', 'الأولوية', 'الصعوبة', 'الأيام']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        df['إنجاز'] = df['إنجاز'].map({'True': True, 'False': False, True: True, False: False}).fillna(False)

    return df

def save_data(df, file): df.to_csv(file, index=False)
init_dbs()

@st.cache_data
def load_lottie(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# ---------------------------------------------------------
# 5. منطق التطبيق
# ---------------------------------------------------------
def distribute_backlog(df, subject, amount, deadline, username):
    start_date = date.today()
    days_available = (deadline - start_date).days
    if days_available <= 0: return df, False, "التاريخ يجب أن يكون في المستقبل!"
    daily_quota = math.ceil(amount / days_available)
    new_rows = []
    current_unit = 1
    for i in range(days_available):
        current_day_date = start_date + timedelta(days=i)
        for _ in range(daily_quota):
            if current_unit <= amount:
                new_rows.append({
                    "إنجاز": False, "المادة": f"{subject} - ج{current_unit}",
                    "الدروس": 1, "المحاضرات": 0, "الصعوبة": 10, "الأيام": (deadline - current_day_date).days,
                    "الأولوية": 100.0, "تاريخ_التنفيذ": current_day_date, "الطالب": username
                })
                current_unit += 1
            else: break
    if new_rows:
        return pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True), True, f"تم التوزيع!"
    return df, False, "خطأ"

def get_bot_response(user_input):
    user_input = user_input.lower()
    if "تعبان" in user_input: return "خذ راحة قصيرة (Power Nap) واشرب ماء. صحتك أهم."
    if "متراكم" in user_input: return "استخدم 'غرفة الإنقاذ' في القائمة، سأفتت لك التراكمات فوراً."
    return "استمر يا بطل، كل خطوة صغيرة تقربك من هدفك. هل أساعدك في تنظيم مادة معينة؟"

# ---------------------------------------------------------
# 6. الواجهة الرئيسية
# ---------------------------------------------------------
def login_page():
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        st.write("")
        st.markdown('<div class="glass-card" style="text-align:center;"><h1>SmartBacklog</h1><p>Pro Edition</p></div>', unsafe_allow_html=True)
        
        # --- ✅ إضافة رسالة بيانات الدخول ---
        st.info("🔐 **بيانات الدخول الافتراضية:**\n\n**المستخدم:** `admin`\n**كلمة السر:** `123`")
        # --------------------------------
        
        if lottie := load_lottie("https://lottie.host/94875632-7605-473d-8065-594ea470b355/9Z53657123.json"):
            st_lottie(lottie, height=150, key="welcome")
            
        u = st.text_input("اسم المستخدم", placeholder="admin")
        p = st.text_input("كلمة المرور", type="password", placeholder="123")
        if st.button("دخول 🚀"):
            users = load_data(USERS_DB)
            found = users[(users['username'] == u) & (users['password'] == p)]
            if not found.empty:
                st.session_state.logged_in = True
                st.session_state.user = found.iloc[0].to_dict()
                st.rerun()
            else: st.error("خطأ في البيانات")

def main_app():
    with st.sidebar:
        st.markdown(f"<h3 style='text-align:center; color:#38bdf8 !important;'>{st.session_state.user['name']}</h3>", unsafe_allow_html=True)
        
        selected = option_menu(
            "القائمة الرئيسية",
            ["لوحة التحكم", "غرفة الإنقاذ", "الجدول اليومي", "المستشار الذكي"], 
            icons=['speedometer2', 'life-preserver', 'table', 'robot'], 
            menu_icon="cast", default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#1e293b", "border-radius": "10px"},
                "icon": {"color": "#38bdf8", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "right", "margin": "0px", "color": "white"},
                "nav-link-selected": {"background-color": "#38bdf8"},
            }
        )
        
        st.write("---")
        if st.button("خروج"):
            st.session_state.logged_in = False
            st.rerun()

    tasks = load_data(TASKS_DB)
    my_tasks = tasks if st.session_state.user['role'] == 'admin' else tasks[tasks['الطالب'] == st.session_state.user['username']]

    # --- Dashboard ---
    if selected == "لوحة التحكم":
        st.markdown("<h2>📊 لوحة الإنجاز</h2>", unsafe_allow_html=True)
        if not my_tasks.empty:
            done = len(my_tasks[my_tasks['إنجاز'] == True])
            total = len(my_tasks)
            pct = (done/total*100) if total > 0 else 0
            
            # شريط التقدم
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_custom_progress_bar(pct)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # العدادات
            c1, c2 = st.columns(2)
            c1.metric("المتبقي", total - done)
            c2.metric("تم إنجازه", done)
            
            st.write("---")
            
            # الرسوم البيانية
            g1, g2 = st.columns(2)
            pending = my_tasks[my_tasks['إنجاز'] == False]
            
            with g1:
                if not pending.empty:
                    st.markdown("##### 🔥 المهام الأكثر إلحاحاً")
                    fig_bar = px.bar(
                        pending.head(7), 
                        x='المادة', 
                        y='الأولوية', 
                        color='الأولوية',
                        template='plotly_dark',
                        color_continuous_scale='Bluyl'
                    )
                    fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color':'white'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                else: st.info("لا توجد مهام معلقة!")

            with g2:
                if not pending.empty:
                    st.markdown("##### 🍰 توزيع الحمل الدراسي")
                    pie_data = pending['المادة'].value_counts().reset_index()
                    pie_data.columns = ['المادة', 'العدد']
                    fig_pie = px.pie(
                        pie_data, 
                        values='العدد', 
                        names='المادة', 
                        hole=0.5, 
                        template='plotly_dark',
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color':'white'})
                    st.plotly_chart(fig_pie, use_container_width=True)
                else: st.info("أضف مواد لرؤية التحليل.")
                    
        else: st.info("ابدأ بإضافة مهام من غرفة الإنقاذ!")

    # --- Rescue ---
    elif selected == "غرفة الإنقاذ":
        st.markdown("<h2>🚑 غرفة الإنقاذ</h2>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("rescue"):
            c1, c2 = st.columns(2)
            subj = c1.text_input("اسم المادة")
            amt = c2.number_input("العدد", min_value=1, value=5)
            dd = st.date_input("تاريخ الانتهاء", min_value=date.today()+timedelta(days=1))
            if st.form_submit_button("تفتيت التراكمات"):
                updated, ok, msg = distribute_backlog(tasks, subj, amt, dd, st.session_state.user['username'])
                if ok:
                    save_data(updated, TASKS_DB)
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Table ---
    elif selected == "الجدول اليومي":
        st.markdown("<h2>🗓️ مهام اليوم</h2>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if not my_tasks.empty:
            my_tasks = my_tasks.sort_values(by=['إنجاز', 'تاريخ_التنفيذ'], ascending=[True, True])
            
            edited = st.data_editor(
                my_tasks,
                column_config={
                    "إنجاز": st.column_config.CheckboxColumn("تم", width="small"),
                    "المادة": st.column_config.TextColumn("المهمة", width="medium"),
                    "تاريخ_التنفيذ": st.column_config.DateColumn("التاريخ", width="small"),
                    "الأولوية": st.column_config.ProgressColumn("الأهمية", max_value=100),
                },
                column_order=["إنجاز", "المادة", "تاريخ_التنفيذ", "الأولوية"],
                disabled=["الطالب"], hide_index=True, use_container_width=True, num_rows="dynamic"
            )
            
            if st.button("حفظ التغييرات 💾"):
                if st.session_state.user['role'] == 'admin':
                    save_data(edited, TASKS_DB)
                else:
                    full_db = load_data(TASKS_DB)
                    full_db = full_db[full_db['الطالب'] != st.session_state.user['username']]
                    save_data(pd.concat([full_db, edited], ignore_index=True), TASKS_DB)
                st.success("تم الحفظ!")
                time.sleep(0.5)
                st.rerun()
        else: st.info("لا توجد مهام.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Chat ---
    elif selected == "المستشار الذكي":
        st.markdown("<h2>🤖 المستشار</h2>", unsafe_allow_html=True)
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
            
        if p := st.chat_input("اكتب مشكلتك..."):
            st.session_state.messages.append({"role": "user", "content": p})
            with st.chat_message("user"): st.write(p)
            
            reply = get_bot_response(p)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"): st.write(reply)

if st.session_state.logged_in: main_app()
else: login_page()
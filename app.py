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
# 1. إعدادات الصفحة (يجب أن تكون الأولى دائماً)
# ---------------------------------------------------------
st.set_page_config(page_title="SmartBacklog Pro", page_icon="🎓", layout="wide")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'messages' not in st.session_state: 
    st.session_state.messages = [{"role": "assistant", "content": "أهلاً يا بطل! أنا المستشار الأكاديمي. حاسس بإيه النهاردة؟ (مخنوق، متراكم عليا، عاوز خطة...)"}]

# ---------------------------------------------------------
# 2. القوة الجبرية للتصميم (CSS Fixed)
# ---------------------------------------------------------
colors = {
    'bg_dark': '#0f172a',
    'primary': '#38bdf8',
    'text': '#ffffff',
    'border': 'rgba(56, 189, 248, 0.3)', 
    'input_bg': '#1e293b',
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&family=El+Messiri:wght@400;500;600;700&display=swap');

/* 1. الخلفية المتحركة (إجبارية) */
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

/* 2. النصوص والخطوط */
* {{ font-family: 'Almarai', sans-serif; }}
h1, h2, h3, h4, h5, h6, .stMetricLabel {{ 
    font-family: 'El Messiri', sans-serif !important; 
    color: white !important;
}}
p, span, label, div, .stMarkdown {{ color: #e2e8f0 !important; }}

/* 3. القائمة الجانبية (Sidebar) */
section[data-testid="stSidebar"] {{
    background-color: rgba(15, 23, 42, 0.95) !important;
    border-right: 1px solid {colors['border']};
}}

/* 4. حقول الإدخال (Inputs) - إصلاح اللون الأبيض */
input, textarea, select, .stTextInput > div > div > input, .stSelectbox > div > div > div {{
    background-color: {colors['input_bg']} !important;
    color: white !important;
    border: 1px solid {colors['border']} !important;
}}
/* لون النص داخل الحقول */
.stTextInput input {{ color: white !important; }}

/* 5. الجداول */
[data-testid="stDataEditor"] {{
    border: 1px solid {colors['border']};
    border-radius: 10px;
    background-color: rgba(15, 23, 42, 0.8) !important;
}}
[data-testid="stDataEditor"] div {{
    background-color: transparent !important;
    color: white !important;
}}

/* 6. رسائل الشات (Chat Style) */
.stChatMessage {{ 
    background-color: rgba(30, 41, 59, 0.6) !important; 
    border: 1px solid rgba(255,255,255,0.1); 
    border-radius: 15px;
}}
/* حقل كتابة الشات */
.stChatInput textarea {{
    background-color: {colors['input_bg']} !important;
    color: white !important;
    border: 1px solid {colors['primary']} !important;
}}

/* 7. البطاقات الزجاجية */
.glass-card {{
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid {colors['border']};
    border-radius: 20px;
    padding: 20px; margin-bottom: 20px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}}

/* 8. إخفاء العناصر المزعجة */
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stDeployButton, [data-testid="stDecoration"], footer {{ display: none !important; }}

/* 9. الأزرار */
div.stButton > button {{
    background: linear-gradient(90deg, #0ea5e9, #2563eb);
    color: white !important; border: none;
    padding: 10px 20px; border-radius: 10px;
    font-weight: bold; width: 100%;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. الدوال المساعدة (شريط التقدم الملون)
# ---------------------------------------------------------
def render_custom_progress_bar(percentage):
    if percentage < 30:
        bar_color = "#ef4444" # أحمر
        bg_color = "rgba(239, 68, 68, 0.2)"
        emoji = "😟 شد حيلك"
    elif percentage < 70:
        bar_color = "#eab308" # أصفر
        bg_color = "rgba(234, 179, 8, 0.2)"
        emoji = "😐 عاش يا بطل"
    else:
        bar_color = "#22c55e" # أخضر
        bg_color = "rgba(34, 197, 94, 0.2)"
        emoji = "🤩 أسطورة!"
    
    st.markdown(f"""
    <div style="margin-bottom: 20px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span style="font-weight:bold; color:white;">مستوى الدوبامين والإنجاز {emoji}</span>
            <span style="font-weight:bold; color:{bar_color};">{percentage:.1f}%</span>
        </div>
        <div style="width: 100%; background-color: {bg_color}; border-radius: 10px; height: 15px;">
            <div style="width: {percentage}%; background-color: {bar_color}; height: 15px; border-radius: 10px; transition: width 1s ease-in-out; box-shadow: 0 0 10px {bar_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. إدارة البيانات
# ---------------------------------------------------------
TASKS_DB = 'smart_tasks.csv'
USERS_DB = 'smart_users.csv'

def init_dbs():
    if not os.path.exists(USERS_DB):
        pd.DataFrame([{"username": "admin", "password": "123", "name": "Admin", "role": "admin"}]).to_csv(USERS_DB, index=False)
    if not os.path.exists(TASKS_DB):
        data = {
            "إنجاز": [False], "المادة": ["مثال: فيزياء"], "الدروس": [1], "المحاضرات": [0],
            "الصعوبة": [5], "الأيام": [10], "الأولوية": [5.0], "تاريخ_التنفيذ": [str(date.today())], "الطالب": ["admin"]
        }
        pd.DataFrame(data).to_csv(TASKS_DB, index=False)

def load_data(file): 
    df = pd.read_csv(file, dtype=str)
    if file == TASKS_DB:
        if 'إنجاز' not in df.columns: df.insert(0, 'إنجاز', 'False')
        if 'تاريخ_التنفيذ' not in df.columns: df['تاريخ_التنفيذ'] = str(date.today())
        for c in ['الدروس', 'المحاضرات', 'الأولوية', 'الصعوبة', 'الأيام']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        df['إنجاز'] = df['إنجاز'].map({'True': True, 'False': False, True: True, False: False, 'TRUE': True, 'FALSE': False})
        df['تاريخ_التنفيذ'] = pd.to_datetime(df['تاريخ_التنفيذ'], errors='coerce').dt.date
        df.loc[df['تاريخ_التنفيذ'].isna(), 'تاريخ_التنفيذ'] = date.today()
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
# 5. المنطق (AI + Logic)
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
                    "إنجاز": False, "المادة": f"{subject} - جزء {current_unit} (إنقاذ)",
                    "الدروس": 1, "المحاضرات": 0, "الصعوبة": 10, "الأيام": (deadline - current_day_date).days,
                    "الأولوية": 100.0, "تاريخ_التنفيذ": current_day_date, "الطالب": username
                })
                current_unit += 1
            else: break
    if new_rows:
        return pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True), True, f"تم إضافة {current_unit-1} مهمة!"
    return df, False, "لم يتم إضافة مهام."

def get_bot_response(user_input):
    user_input = user_input.lower()
    responses = {
        "تعبان": "التعب علامة المجهود، لكن الإرهاق علامة التوقف. جرب تاخد راحة 15 دقيقة (Power Nap) واشرب ميه، وارجع كمل. صحتك أهم من أي درجة.",
        "زهقان": "الزهق بيجي لما المهام تكون رتيبة. جرب تغير المكان اللي بتذاكر فيه، أو ذاكر المادة الصعبة بطريقة جديدة (فيديو بدل كتاب). اكسر الروتين!",
        "متراكم": "ولا يهمك، التراكم مجرد أرقام. روح لـ 'غرفة الإنقاذ' في البرنامج ده، وحط المادة اللي مخوفاك، وأنا هقطعهالك حتت صغيرة تخلصها من غير ما تحس.",
        "خايف": "الخوف طبيعي، بس متخلهوش يسيطر عليك. الخوف علاجه (الفعل). ابدأ بحاجة تافهة جداً دلوقتي، وهتلاقي الخوف اختفى.",
        "شكرا": "العفو يا بطل! أنا موجود هنا عشانك. كمل دوس!",
    }
    for key, response in responses.items():
        if key in user_input: return response
    return "سؤال جميل! أهم حاجة دلوقتي إنك تركز على (الاستمرارية) مش الكمال. ابدأ باللي تقدر عليه، والبرنامج هينظملك الباقي."

# ---------------------------------------------------------
# 6. التطبيق الرئيسي
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
            <div style="width: 80px; height: 80px; border-radius: 50%; background: #38bdf8; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 30px; color: white; box-shadow: 0 0 20px #38bdf8;">{st.session_state.user['name'][0].upper()}</div>
            <h3 style="margin-top: 15px; color: #38bdf8 !important;">{st.session_state.user['name']}</h3>
        </div>
        """, unsafe_allow_html=True)
        menu = option_menu("القائمة", ["لوحة التحكم", "غرفة الإنقاذ", "الجدول التفاعلي", "المستشار الذكي"], 
            icons=['speedometer', 'life-preserver', 'table', 'robot'], menu_icon="cast", default_index=0,
            styles={
                "container": {"padding": "5px", "background-color": "transparent"}, 
                "icon": {"color": "#38bdf8"}, 
                "nav-link": {"color": "white", "text-align": "right"}, 
                "nav-link-selected": {"background-color": "#38bdf8"}
            })
        st.markdown("---")
        if st.button("تسجيل خروج", key="logout"):
            st.session_state.logged_in = False
            st.rerun()

    tasks = load_data(TASKS_DB)
    my_tasks = tasks if st.session_state.user['role'] == 'admin' else tasks[tasks['الطالب'] == st.session_state.user['username']]

    # --- Dashboard ---
    if menu == "لوحة التحكم":
        st.markdown(f"<h2>مرحباً بك 👋</h2>", unsafe_allow_html=True)
        if not my_tasks.empty:
            pending = my_tasks[my_tasks['إنجاز'] == False]
            completed = my_tasks[my_tasks['إنجاز'] == True]
            
            total_count = len(my_tasks)
            completed_count = len(completed)
            progress_pct = (completed_count / total_count * 100) if total_count > 0 else 0
            
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_custom_progress_bar(progress_pct)
            st.markdown('</div>', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>المتبقي</h3><h1>{len(pending)}</h1></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>وحدات المذاكرة</h3><h1>{pending["الدروس"].sum() + pending["المحاضرات"].sum():.0f}</h1></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="glass-card" style="text-align:center"><h3>تم إنجازه ✅</h3><h1>{len(completed)}</h1></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns([1.5, 1])
            with g1:
                pending['الكل'] = pending['الدروس'] + pending['المحاضرات']
                if not pending.empty:
                    fig = px.bar(pending.head(10), x='المادة', y='الأولوية', color='الأولوية', template='plotly_dark')
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", font_color='white')
                    st.plotly_chart(fig, use_container_width=True)
            with g2:
                if not pending.empty:
                    fig2 = px.pie(pending, values='الكل', names='المادة', hole=0.6, template='plotly_dark')
                    fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_family="Almarai", font_color='white', showlegend=False)
                    st.plotly_chart(fig2, use_container_width=True)
        else: st.info("لا توجد بيانات.")

    # --- Rescue ---
    elif menu == "غرفة الإنقاذ":
        st.markdown(f"<h2>🚑 غرفة الإنقاذ</h2>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("rescue_form"):
            c1, c2 = st.columns(2)
            with c1: subj = st.text_input("اسم المادة")
            with c2: amt = st.number_input("العدد", min_value=1)
            d_date = st.date_input("موعد الانتهاء", min_value=date.today() + timedelta(days=1))
            if st.form_submit_button("🚀 فتت التراكمات"):
                if subj:
                    updated, success, msg = distribute_backlog(tasks, subj, amt, d_date, st.session_state.user['username'])
                    if success:
                        save_data(updated, TASKS_DB)
                        st.balloons()
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else: st.error(msg)
                else: st.warning("أدخل المادة")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Table ---
    elif menu == "الجدول التفاعلي":
        st.markdown(f"<h2>🗓️ جدول المهام</h2>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if not my_tasks.empty:
            my_tasks = my_tasks.sort_values(by=["إنجاز", "تاريخ_التنفيذ"], ascending=[True, True])
            edited = st.data_editor(my_tasks, 
                column_config={"إنجاز": st.column_config.CheckboxColumn("تم؟"), "الأولوية": st.column_config.ProgressColumn("الأهمية", max_value=100)},
                disabled=["الطالب"], hide_index=True, use_container_width=True, num_rows="dynamic")
            if st.button("💾 حفظ"):
                if st.session_state.user['role'] == 'admin': save_data(edited, TASKS_DB)
                else:
                    final = load_data(TASKS_DB)
                    final = final[final['الطالب'] != st.session_state.user['username']]
                    save_data(pd.concat([final, edited], ignore_index=True), TASKS_DB)
                st.success("تم!")
                time.sleep(0.5)
                st.rerun()
        else: st.info("فارغ")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- AI Chat ---
    elif menu == "المستشار الذكي":
        st.markdown(f"<h2>🤖 المستشار الأكاديمي</h2>", unsafe_allow_html=True)
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
        if prompt := st.chat_input("اكتب هنا..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    time.sleep(0.8)
                    reply = get_bot_response(prompt)
                    st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

if st.session_state.logged_in: main_app()
else: login_page()

components.html("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.2/vanilla-tilt.min.js"></script>
<script>
    document.addEventListener("DOMContentLoaded", function() {
        VanillaTilt.init(document.querySelectorAll('.glass-card'), { max: 10, speed: 400, glare: true, "max-glare": 0.3 });
    });
</script>
""", height=0, width=0)
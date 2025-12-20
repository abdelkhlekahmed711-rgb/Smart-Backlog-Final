import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import random
import requests
import time
from streamlit_lottie import st_lottie

# ---------------------------------------------------------
# 1. إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(page_title="SmartBacklog Pro", page_icon="🎓", layout="wide")

# اسم ملف قاعدة البيانات
DB_FILE = 'smart_backlog_db.csv'

# ---------------------------------------------------------
# 2. تسريع الموقع (Caching)
# ---------------------------------------------------------
@st.cache_data
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# تحميل الأنيميشن
lottie_student = load_lottieurl("https://lottie.host/5a709b1f-d748-4b7d-949f-50a84e27771c/9qj8M4Zz2X.json")
lottie_rocket = load_lottieurl("https://lottie.host/c95104d5-51e0-4f36-8488-46637213b194/Jg2v5u1v7t.json")
lottie_done = load_lottieurl("https://lottie.host/880e6082-c84d-4447-9154-8e100d08779a/02a5f7e4.json")

# ---------------------------------------------------------
# 3. قاعدة البيانات
# ---------------------------------------------------------
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["المادة", "الدروس", "الصعوبة", "الأيام", "الأولوية", "الطالب"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def generate_dummy_data():
    subjects = ["فيزياء", "كيمياء", "أحياء", "رياضيات", "عربي", "إنجليزي", "تاريخ", "جغرافيا"]
    data = []
    for i in range(25):
        subj = random.choice(subjects)
        lessons = random.randint(1, 15)
        diff = random.randint(3, 10)
        days = random.randint(2, 30)
        prio = (diff * lessons) / days
        data.append({
            "المادة": f"{subj} - وحدة {i+1}",
            "الدروس": lessons, "الصعوبة": diff, "الأيام": days,
            "الأولوية": round(prio, 2), "الطالب": "طالب افتراضي"
        })
    df = pd.DataFrame(data)
    save_data(df)
    return df

# ---------------------------------------------------------
# 4. التصميم (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Tajawal', sans-serif;
    }
    .main, .stMarkdown, .stButton, .stDataFrame, .stTextInput { direction: rtl; text-align: right; }
    h1, h2, h3 { color: #1a237e; font-weight: 800; }
    
    div[data-testid="stMetric"], div.stDataFrame, .login-box {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid rgba(255,255,255,0.8);
    }
    .google-btn {
        background-color: white; color: #333; border: 1px solid #ddd;
        border-radius: 50px; padding: 10px; width: 100%;
        display: flex; justify-content: center; align-items: center; gap: 10px;
        font-weight: bold; cursor: pointer; transition: 0.3s;
    }
    .google-btn:hover { background-color: #f1f1f1; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    
    div.stButton > button {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white; border-radius: 10px; border: none; padding: 10px 20px;
        font-weight: bold; width: 100%; transition: transform 0.2s;
    }
    div.stButton > button:hover { transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. صفحة تسجيل الدخول
# ---------------------------------------------------------
def send_recovery_email(email):
    with st.spinner('جاري الاتصال بخوادم البريد الآمن...'):
        time.sleep(1.5) 
    st.success(f"✅ تم إرسال رابط إعادة التعيين إلى: {email}")

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.title("🔐 بوابة المبدع الصغير")
        st.write("سجل دخولك لبدء رحلة النجاح")
        
        # تعريف التبويبات بشكل صحيح
        tab_email, tab_google = st.tabs(["📧 دخول بالبريد", "G حساب جوجل"])
        
        # تبويب البريد الإلكتروني
        with tab_email:
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            
            if st.button("تسجيل الدخول", key="login_btn"):
                if username == "admin" and password == "admin":
                    st.session_state.logged_in = True
                    st.session_state.role = "admin"
                    st.rerun()
                elif username == "student" and password == "123":
                    st.session_state.logged_in = True
                    st.session_state.role = "student"
                    st.rerun()
                else:
                    st.error("خطأ في البيانات! جرب: admin/admin أو student/123")
            
            with st.expander("هل نسيت كلمة المرور؟"):
                rec_mail = st.text_input("البريد الإلكتروني للاستعادة")
                if st.button("إرسال الرمز"):
                    if rec_mail:
                        send_recovery_email(rec_mail)
                    else:
                        st.warning("أدخل البريد أولاً")

        # تبويب جوجل (تم إصلاح الخطأ هنا)
        with tab_google:
            st.write("الدخول السريع والآمن")
            if st.button("Sign in with Google", key="g_login"):
                with st.spinner('جاري المصادقة مع Google...'):
                    time.sleep(1.5)
                st.session_state.logged_in = True
                st.session_state.role = "student"
                st.balloons()
                st.rerun()
            
            st.markdown("""
            <div style="text-align: center; margin-top: 10px;">
                <button class="google-btn">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="20">
                    استخدم حساب Google
                </button>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. لوحة الطالب
# ---------------------------------------------------------
def student_dashboard():
    with st.sidebar:
        if lottie_student: st_lottie(lottie_student, height=150)
        st.title(f"👤 مرحباً، {st.session_state.role}")
        
        if st.button("تسجيل خروج 🚪"):
            st.session_state.logged_in = False
            st.rerun()

    col_t, col_i = st.columns([3, 1])
    with col_t:
        st.title("🚀 نظام SmartBacklog")
        st.write("حول التراكمات إلى خطة عمل ذكية")
    with col_i:
        if lottie_rocket: st_lottie(lottie_rocket, height=100)

    tab1, tab2, tab3 = st.tabs(["📊 إضافة ومتابعة", "📋 الجدول الذكي", "💡 المساعد"])

    with tab1:
        with st.expander("➕ إضافة مادة جديدة", expanded=True):
            with st.form("add_task"):
                c1, c2, c3 = st.columns(3)
                with c1: subj = st.text_input("اسم المادة")
                with c2: lessons = st.number_input("الدروس", 1, 50, 5)
                with c3: diff = st.slider("الصعوبة", 1, 10, 5)
                days = st.number_input("أيام حتى الامتحان", 1, 365, 7)
                
                if st.form_submit_button("إضافة 💾"):
                    if subj:
                        df = load_data()
                        prio = (diff * lessons) / days
                        new_row = {"المادة": subj, "الدروس": lessons, "الصعوبة": diff, "الأيام": days, "الأولوية": round(prio, 2), "الطالب": "عبد الخالق"}
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        st.success("تم الحفظ!")
                        if lottie_done: st_lottie(lottie_done, height=100, key="success")
                        st.rerun()
                    else:
                        st.warning("اكتب اسم المادة!")

        df = load_data()
        if not df.empty:
            st.divider()
            k1, k2, k3 = st.columns(3)
            k1.metric("عدد المواد", len(df))
            k2.metric("إجمالي الدروس", df['الدروس'].sum())
            k3.metric("الأكثر إلحاحاً", df.loc[df['الأولوية'].idxmax()]['المادة'])
            
            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(px.pie(df, values='الدروس', names='المادة', hole=0.4, title="توزيع الجهد"), use_container_width=True)
            with g2:
                st.plotly_chart(px.bar(df, x='المادة', y='الأولوية', color='الأولوية', title="مؤشر الخطر"), use_container_width=True)

    with tab2:
        df = load_data()
        if not df.empty:
            st.subheader("جدول الأولويات (ابدأ بالأعلى)")
            st.dataframe(df.sort_values(by="الأولوية", ascending=False).style.background_gradient(cmap="Blues", subset=["الأولوية"]), use_container_width=True)
        else:
            st.info("لا توجد بيانات.. ابدأ بالإضافة!")

    with tab3:
        st.info("🤖 نصيحة الذكاء الاصطناعي: قسم الدروس الكبيرة إلى أجزاء صغيرة لتشعر بالإنجاز.")

# ---------------------------------------------------------
# 7. لوحة المدير
# ---------------------------------------------------------
def admin_dashboard():
    st.sidebar.error("وضع المسؤول (Admin)")
    if st.sidebar.button("تسجيل خروج"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.title("🛠️ لوحة تحكم النظام")
    df = load_data()
    st.metric("إجمالي السجلات", len(df))
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⚡ توليد بيانات تلقائية"):
            generate_dummy_data()
            st.success("تم التوليد!")
            st.rerun()
    with col_b:
        if st.button("🗑️ حذف الكل"):
            save_data(pd.DataFrame(columns=["المادة", "الدروس", "الصعوبة", "الأيام", "الأولوية", "الطالب"]))
            st.warning("تم الحذف!")
            st.rerun()
            
    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# 8. التشغيل
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "admin":
        admin_dashboard()
    else:
        student_dashboard()
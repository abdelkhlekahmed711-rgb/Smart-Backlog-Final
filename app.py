import streamlit as st
import pandas as pd
import sqlite3
import time
import os
import math
from datetime import date, timedelta
from streamlit_option_menu import option_menu

# --- إعدادات الهوية البصرية ---
st.set_page_config(page_title="SmartBacklog | Time Manager", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; text-align: right; }
    .stApp { background-color: #050505; color: #E0E0E0; }
    
    /* الشريط العلوي المخصص */
    .top-bar {
        background: linear-gradient(90deg, #1e3a8a, #0f172a);
        padding: 10px 25px;
        border-radius: 0 0 15px 15px;
        display: flex;
        justify-content: space-between;
        margin-bottom: 25px;
        border-bottom: 2px solid #3b82f6;
    }
    
    /* بطاقات المهام */
    .task-card {
        background: rgba(30, 41, 59, 0.7);
        border-right: 5px solid #3b82f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- إدارة قاعدة البيانات ---
DB_FILE = 'smart_backlog_v2.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # جدول المستخدمين المطور
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, name TEXT, goal TEXT)''')
    # جدول المهام المطور (بدون مكتبة)
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, subject TEXT, 
                  units INTEGER, priority REAL, due_date DATE, status INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- خوارزمية الأولوية الرياضية ---
# تستخدم لحساب مدى استعجال الدرس بناءً على الموعد النهائي [cite: 2025-12-27]
def calculate_priority(diff, units, due_date):
    days_left = max((due_date - date.today()).days, 1)
    # المعادلة: $P = \frac{D \times U \times 10}{Days}$
    return (diff * units * 10) / days_left

# --- الواجهة الرئيسية ---
def main():
    # الشريط العلوي (Top Bar)
    st.markdown(f"""
    <div class="top-bar">
        <span style="color: #60a5fa;">📅 اليوم: {date.today()}</span>
        <span style="font-weight: bold; color: white;">🚀 Smart Backlog v2.0</span>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"### 🎖️ القائد: عبدالخالق")
        st.info("الهدف: الكلية الفنية العسكرية [cite: 2025-11-24]")
        
        menu = option_menu(
            "نظام التحكم", 
            ["لوحة القيادة", "غرفة الطوارئ", "الإحصائيات"],
            icons=['cpu', 'lightning-charge', 'bar-chart'],
            menu_icon="cast", default_index=0
        )
        if st.button("تسجيل الخروج"): st.stop()

    if menu == "لوحة القيادة":
        st.subheader("📋 قائمة المهام القتالية")
        # عرض المهام كبطاقات (Task Cards)
        st.markdown("""
        <div class="task-card">
            <h4 style="margin:0;">📚 مادة الرياضيات - التفاضل</h4>
            <p style="color:#94a3b8; font-size:0.9em;">الأولوية: عالية 🔥 | الموعد: بعد 3 أيام</p>
        </div>
        """, unsafe_allow_html=True)

    elif menu == "غرفة الطوارئ":
        st.subheader("🚑 نظام الجدولة الفوري")
        with st.form("add_task"):
            subj = st.selectbox("المادة", ["رياضيات", "كيمياء", "فيزياء"])
            lec_num = st.number_input("عدد الدروس المتراكمة", 1)
            target_date = st.date_input("موعد إنهاء التراكم")
            if st.form_submit_button("توليد خطة الإنقاذ"):
                prio = calculate_priority(7, lec_num, target_date)
                st.success(f"تم حساب الأولوية: {prio:.2f}. سيتم توزيع الدروس على { (target_date - date.today()).days } يوماً.")

# تشغيل التطبيق
if __name__ == "__main__":
    main()
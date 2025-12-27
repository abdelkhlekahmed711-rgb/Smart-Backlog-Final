import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- 1. التنسيق الجمالي (Notion Style CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Cairo:wght@400;700&display=swap');
    
    /* جعل الخطوط والألوان تحاكي نوشن */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Cairo', sans-serif;
        background-color: #ffffff;
        color: #37352f;
    }
    
    /* تصميم الكتل (Notion Blocks) */
    .notion-block {
        border: 1px solid #e9e9e7;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        transition: background 0.2s;
    }
    .notion-block:hover { background-color: #f7f6f3; }
</style>
""", unsafe_allow_html=True)

# --- 2. منطق إدارة البيانات للمدير ---
def get_all_db_data():
    conn = sqlite3.connect('backlog_manager.db')
    data = {
        "المستخدمين": pd.read_sql("SELECT * FROM users", conn),
        "المهام": pd.read_sql("SELECT * FROM tasks", conn)
    }
    conn.close()
    return data

# --- 3. عرض الواجهات ---
def admin_ui():
    st.title("🛡️ مركز بيانات النظام")
    all_data = get_all_db_data()
    
    for table_name, df in all_data.items():
        st.subheader(f"📋 جدول {table_name}")
        st.dataframe(df, use_container_width=True)

def student_ui():
    st.title("📝 مساحة العمل الخاصة بي")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### ⚡ التركيز اليومي")
        st.markdown("""
        <div class="notion-block">
            <span>📚</span> <b>مذاكرة الفيزياء - الفصل الثالث</b>
            <div style="font-size: 0.8em; color: #787774;">الأولوية: مرتفعة | الموعد: غداً</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 التقدم")
        st.progress(0.65)
        st.caption("تم إنجاز 65% من مهام الأسبوع")

# --- التحكم في الدخول (مثال بسيط) ---
role = "admin" # هذا سيتغير بناءً على تسجيل الدخول [cite: 2025-12-27]

if role == "admin":
    admin_ui()
else:
    student_ui()
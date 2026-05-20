import os
import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# ==============================================================================
# 1. PREMIUM TACTICAL THEME & MOBILE HEADERS
# ==============================================================================
st.components.v1.html(
    """
    <script>
        if (!document.getElementById('pwa-mobile-tags')) {
            var meta1 = document.createElement('meta');
            meta1.id = 'pwa-mobile-tags';
            meta1.name = 'apple-mobile-web-app-capable';
            meta1.content = 'yes';
            
            var meta2 = document.createElement('meta');
            meta2.name = 'apple-mobile-web-app-status-bar-style';
            meta2.content = 'black-translucent';
            
            document.getElementsByTagName('head')[0].appendChild(meta1);
            document.getElementsByTagName('head')[0].appendChild(meta2);
        }
    </script>
    """,
    height=0,
)

# Set up page configurations with a clean, centered layout
st.set_page_config(
    page_title="TACTICAL ENGINE",
    page_icon="⚡",
    layout="centered"
)

# Custom CSS to force a high-contrast dark aesthetic, clean borders, and premium buttons
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #E0E2E5; }
        .stButton>button { 
            background-color: #00CC66 !important; 
            color: #000000 !important; 
            font-weight: 700 !important;
            border-radius: 8px !important;
            border: none !important;
            width: 100% !important;
        }
        .stTabs [data-baseweb="tab"] { font-weight: 600; color: #A3A8B4; }
        .stTabs [aria-selected="true"] { color: #00CC66 !important; border-bottom-color: #00CC66 !important; }
    </style>
""", unsafe_html=True)

# ==============================================================================
# 2. CACHED DATABASE CONNECTIONS
# ==============================================================================
def get_db_connection():
    db_url = st.secrets["NEON_DATABASE_URL"]
    return psycopg2.connect(db_url)

@st.cache_data(ttl=600)
def load_workout_history():
    query = "SELECT * FROM workout_logs ORDER BY date DESC;"
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database Fetch Error: {e}")
        return pd.DataFrame()

# ==============================================================================
# 3. HIGH-VISIBILITY VISUAL DASHBOARD
# ==============================================================================
st.title("⚡ TACTICAL ATHLETIC ENGINE")
st.write("---")

# Quick snapshot high-impact metrics cards at the top
history_df = load_workout_history()

if not history_df.empty:
    col_a, col_b = st.columns(2)
    with col_a:
        # Pulls your last logged pull-up stat dynamically
        last_pullups = int(history_df['pullups'].iloc[0]) if 'pullups' in history_df.columns else 0
        st.metric(label="Last Pull-Up Set", value=f"{last_pullups} Reps", delta="Baseline Standard")
    with col_b:
        # Pulls your last 1-mile run time split
        last_run = str(history_df['run_time'].iloc[0]) if 'run_time' in history_df.columns else "00:00"
        st.metric(label="Last 1-Mile Split", value=last_run, delta="- Pace Sync", delta_color="inverse")
    st.write("---")

# Tab creation
tab1, tab2 = st.tabs(["Log Daily Split", "Performance Analytics"])

with tab1:
    st.write("### Record Performance Metrics")
    
    with st.form("workout_form", clear_on_submit=True):
        log_date = st.date_input("Training Date", value=datetime.today())
        
        st.write("⚡ **Strength Calisthenics**")
        assisted_pullups = st.slider(
            label="Assisted Pull-Up Reps (Bench Assisted)",
            min_value=0, max_value=30, value=8, step=1
        )
        
        st.write("🏃‍♂️ **Cardio Endurance**")
        c1, c2 = st.columns(2)
        with c1:
            run_minutes = st.number_input("1-Mile Run (Minutes)", min_value=4, max_value=15, value=6, step=1)
        with c2:
            run_seconds = st.number_input("1-Mile Run (Seconds)", min_value=0, max_value=59, value=30, step=1)
            
        # FIXED: Correct form submit function
        submit_btn = st.form_submit_button("COMMIT SPLIT TO LEDGER")
        
        if submit_btn:
            formatted_run_time = f"{run_minutes:02d}:{run_seconds:02d}"
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                insert_query = """
                    INSERT INTO workout_logs (date, pullups, run_time)
                    VALUES (%s, %s, %s);
                """
                cur.execute(insert_query, (log_date, assisted_pullups, formatted_run_time))
                conn.commit()
                cur.close()
                conn.close()
                
                st.success("Workout committed securely to Neon cloud ledger!")
                st.cache_data.clear()
                st.rerun()
                
            except Exception as e:
                st.error(f"Failed to submit entry: {e}")

with tab2:
    st.write("### Historical Training Log Ledger")
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No training records found. Submit your first daily split to ignite the ledger.")
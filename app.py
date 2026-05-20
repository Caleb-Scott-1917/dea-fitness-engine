import os
import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# ==============================================================================
# 1. MOBILE OPTIMIZATION META-TAGS (Forces full-screen native standalone mode)
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

# Set page configuration immediately after layout adjustments
st.set_page_config(
    page_title="DEA Athletic Engine",
    page_icon="💪",
    layout="centered"
)

# ==============================================================================
# 2. CACHED DATABASE RECONCILIATION (Pings Neon only when cache expires or resets)
# ==============================================================================
def get_db_connection():
    """Extracts the secure connection URL from Streamlit's secrets vault."""
    db_url = st.secrets["NEON_DATABASE_URL"]
    return psycopg2.connect(db_url)

@st.cache_data(ttl=600)  # Caches the dataframe for 10 minutes to save mobile data
def load_workout_history():
    """Queries historical metrics from your remote database cloud table."""
    # CHANGED: Target 'workouts' to match your exact Neon table name
    query = "SELECT * FROM workouts ORDER BY date DESC;"
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database Fetch Error: {e}")
        return pd.DataFrame()  # Returns an empty dataframe fallback if connection fails

# ==============================================================================
# 3. INTERFACE NAVIGATION & DATA CAPTURE
# ==============================================================================
st.title("🦅 DEA Performance Log")

tab1, tab2 = st.tabs(["Log Daily Split", "Performance History"])

with tab1:
    st.write("### Record Performance Metrics")
    
    with st.form("workout_form", clear_on_submit=True):
        log_date = st.date_input("Training Date", value=datetime.today())
        
        st.write("---")
        st.write("**Strength Calisthenics**")
        
        # Tap-Target Sliders: Defaulting to your baseline metrics so typing isn't required
        assisted_pullups = st.slider(
            label="Assisted Pull-Up Reps (Bench Assisted)",
            min_value=0,
            max_value=30,
            value=8,
            step=1
        )
        
        st.write("---")
        st.write("**Cardio Endurance**")
        
        # Dual columns to easily capture clean run splits on a mobile screen
        col1, col2 = st.columns(2)
        with col1:
            run_minutes = st.number_input("1-Mile Run (Minutes)", min_value=4, max_value=15, value=6, step=1)
        with col2:
            run_seconds = st.number_input("1-Mile Run (Seconds)", min_value=0, max_value=59, value=30, step=1)
            
        # CHANGED: Fixed the typo function to the correct st.form_submit_button()
        submit_btn = st.form_submit_button("Submit Training Log")
        
        if submit_btn:
            # Format the run time metrics into a standard string
            formatted_run_time = f"{run_minutes:02d}:{run_seconds:02d}"
            
            # Insert logic into your Neon remote ledger
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                # CHANGED: Target 'workouts' to match your exact Neon table name
                insert_query = """
                    INSERT INTO workouts (date, pullups, run_time)
                    VALUES (%s, %s, %s);
                """
                cur.execute(insert_query, (log_date, assisted_pullups, formatted_run_time))
                conn.commit()
                cur.close()
                conn.close()
                
                st.success("Workout committed securely to Neon cloud ledger!")
                
                # CRITICAL: Clears the cache so the history tab updates immediately on submission
                st.cache_data.clear()
                st.rerun()
                
            except Exception as e:
                st.error(f"Failed to submit entry: {e}")

with tab2:
    st.write("### Historical Training Log")
    
    # Loads the cached dataframe instantly without waiting for a database round-trip
    history_df = load_workout_history()
    
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No training records found. Submit your first daily split to ignite the ledger.")
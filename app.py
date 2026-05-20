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
# 2. CACHED DATABASE RECONCILIATION
# ==============================================================================
def get_db_connection():
    db_url = st.secrets["NEON_DATABASE_URL"]
    return psycopg2.connect(db_url)

@st.cache_data(ttl=600)
def load_workout_history():
    # Targets your newly created physical_performance table
    query = "SELECT * FROM physical_performance ORDER BY date DESC;"
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database Fetch Error: {e}")
        return pd.DataFrame()

# ==============================================================================
# 3. INTERFACE NAVIGATION & DATA CAPTURE (YESTERDAY'S CLEAN VERTICAL LAYOUT)
# ==============================================================================
st.title("🦅 DEA Performance Log")

tab1, tab2 = st.tabs(["Log Daily Split", "Performance History"])

with tab1:
    st.write("### Record Performance Metrics")
    
    with st.form("workout_form", clear_on_submit=True):
        log_date = st.date_input("Training Date", value=datetime.today())
        
        st.write("---")
        
        # Yesterday's standard numeric input box
        assisted_pullups = st.number_input(
            label="Assisted Pullups",
            min_value=0,
            max_value=100,
            value=0,
            step=1
        )
        
        st.write("---")
        
        # Yesterday's standard run time numeric entry box
        run_time = st.number_input(
            label="Run Time (e.g. 6.30)", 
            min_value=0.0, 
            max_value=30.0, 
            value=0.0, 
            step=0.01
        )
        
        st.write("---")
        
        submit_btn = st.form_submit_button("Submit Training Log")
        
        if submit_btn:
            # Convert decimal entry to a clean string format for your ledger
            formatted_run_time = f"{run_time:.2f}".replace('.', ':')
            
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                # Targets your newly created physical_performance table columns perfectly
                insert_query = """
                    INSERT INTO physical_performance (date, pullups, run_time)
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
    st.write("### Historical Training Log")
    history_df = load_workout_history()
    
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No training records found. Submit your first daily split to ignite the ledger.")
import os
import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, date

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
# 3. 14-DAY DEA ATHLETIC HYBRID SPLIT ENGINE (Monday = Day 1 Anchor)
# ==============================================================================
TRAINING_SPLIT = {
    1: {
        "title": "WEEK 1, DAY 1 — PUSH STRENGTH",
        "routine": "• Barbell or DB Bench Press — 4x5–6\n• Incline DB Press — 3x8\n• Close-Grip Bench or Weighted Push-Ups — 3x8\n• DB Shoulder Press — 3x8\n• Overhead Tricep Extension — 3x10",
        "dea_work": "• Push-Ups — 3 submax sets\n• OPTIONAL: 15–20 min incline walk or bike"
    },
    2: {
        "title": "WEEK 1, DAY 2 — PULL HYPERTROPHY",
        "routine": "• Pull-Ups or Assisted Pull-Ups — 4 sets\n• One-Arm DB Row — 4x10\n• Chest-Supported Row — 3x12\n• Rear Delt Flyes — 3x15\n• Hammer Curls — 3x12",
        "dea_work": "• Sit-Ups — 3x25\n• Plank — 3x1 min"
    },
    3: {
        "title": "WEEK 1, DAY 3 — LEG ENDURANCE",
        "routine": "• CONDITIONING: Bike Intervals — 10 rounds (20s hard / 100s easy)\n• STRENGTH: Bulgarian Split Squats — 3x12\n• Goblet Squats — 3x15\n• Walking Lunges — 2x20 steps\n• Calf Raises — 3x20\n• Tibialis Raises — 3x20",
        "dea_work": "Focus on flushing lactic acid and joint durability."
    },
    4: {
        "title": "WEEK 1, DAY 4 — RECOVERY / ZONE 2",
        "routine": "• Choose ONE: Incline walk, Bike, Swim, or Easy hike\n• Duration: 30–45 min at an easy pace",
        "dea_work": "• Mobility & Stretching\n• Light core routine"
    },
    5: {
        "title": "WEEK 1, DAY 5 — PUSH VOLUME",
        "routine": "• Incline DB Bench — 4x10–12\n• Push-Ups — 5 sets\n• DB Shoulder Press — 3x10\n• Lateral Raises — 3x15\n• Dips or Tricep Pushdowns — 3x12",
        "dea_work": "• DEA WORK: Sit-Ups — 3 rounds max reps in 45 sec"
    },
    6: {
        "title": "WEEK 1, DAY 6 — PULL CONDITIONING",
        "routine": "Circuit Style (4–5 rounds, short rest):\n• Pull-Ups or Inverted Rows\n• DB Rows\n• KB Swings\n• Farmer Carries\n• Core movement",
        "dea_work": "Maintain grip endurance under cardio fatigue."
    },
    7: {
        "title": "WEEK 1, DAY 7 — FULL RECOVERY",
        "routine": "• Easy Walk\n• Targeted Mobility Work\n• Full body stretching",
        "dea_work": "Prioritize nervous system recovery and nutrition."
    },
    8: {
        "title": "WEEK 2, DAY 8 — PUSH POWER",
        "routine": "• Bench Press — 5x3 (explosive execution)\n• Push Press — 4x3–5\n• Plyo Push-Ups — 4x5\n• Incline DB Press — 3x8\n• Tricep Work — 3x10",
        "dea_work": "• DEA WORK: 1 max push-up test set"
    },
    9: {
        "title": "WEEK 2, DAY 9 — PULL VOLUME",
        "routine": "• Pull-Ups — 5 sets\n• DB Row — 4x12\n• Barbell Row — 3x10\n• Face Pulls — 3x15\n• Curls — 3x15",
        "dea_work": "• DEA WORK: Sit-Ups — 100 total reps accumulated"
    },
    10: {
        "title": "WEEK 2, DAY 10 — LEG STRENGTH",
        "routine": "• Romanian Deadlift — 4x6–8\n• Split Squats — 3x8\n• Step-Ups — 3x10\n• Calf Raises — 3x15\n• Tibialis Raises — 3x15",
        "text": "• CONDITIONING: Easy bike — 10–15 min"
    },
    11: {
        "title": "WEEK 2, DAY 11 — RECOVERY / AEROBIC BASE",
        "routine": "• Choose ONE: Bike, Incline walk, or Swim\n• Duration: 30–45 minutes continuous",
        "dea_work": "• Targeted lower body mobility work\n• Full static stretching"
    },
    12: {
        "title": "WEEK 2, DAY 12 — PUSH CONDITIONING",
        "routine": "Circuit Style (Moderate pace):\n• Push-Ups\n• DB Bench\n• Shoulder Press\n• Sit-Ups\n• Burpees or Bike Sprint",
        "dea_work": "Emulate PFT pacing and movement transitions."
    },
    13: {
        "title": "WEEK 2, DAY 13 — PULL + SPRINT CONDITIONING",
        "routine": "• IF SHINS FEEL GOOD: Short sprint intervals\n• IF SHINS HURT: Bike sprint intervals\n• ACCESSORIES: Pull-Ups, Rows, Farmer Carries, Rear Delt Work",
        "dea_work": "Protect structural baselines. Do not run through acute bone pain."
    },
    14: {
        "title": "WEEK 2, DAY 14 — MOCK DEA TEST / RECOVERY",
        "routine": "• ALTERNATE CYCLE A: Max Push-Ups, Timed Sit-Ups, and Mile Test (or Bike Conditioning Test)\n• ALTERNATE CYCLE B: Full recovery day instead",
        "dea_work": "Track baseline progress if testing; maximize sleep if recovering."
    }
}

def calculate_split_day(target_date):
    """Calculates the exact day (1-14) of the training cycle assuming Monday is Day 1."""
    # Find the ISO calendar week and weekday (Monday = 1, Sunday = 7)
    iso_year, iso_week, iso_weekday = target_date.isocalendar()
    
    # Determine if we are on an odd or even week number to loop the 14-day macrocycle
    week_cycle = (iso_week % 2)
    
    if week_cycle == 1:  # Week 1 of the split
        return iso_weekday
    else:                # Week 2 of the split
        return iso_weekday + 7

# ==============================================================================
# 4. INTERFACE NAVIGATION & DATA CAPTURE
# ==============================================================================
st.title("🦅 DEA Performance Log")

tab1, tab2 = st.tabs(["Log Daily Split", "Performance History"])

with tab1:
    # 14-Day Calendar Mapping Engine
    selected_date = st.date_input("Training Date", value=datetime.today().date())
    current_day_number = calculate_split_day(selected_date)
    today_workout = TRAINING_SPLIT[current_day_number]
    
    # Visual Tactical Target Card Layout
    st.markdown(f"### 🛡️ {today_workout['title']}")
    st.info(f"**Today's Programming Plan:**\n{today_workout['routine']}")
    if "dea_work" in today_workout and today_workout["dea_work"]:
        st.warning(f"**DEA Target Protocol:**\n{today_workout['dea_work']}")
        
    st.write("---")
    st.write("### Record Performance Metrics")
    
    with st.form("workout_form", clear_on_submit=True):
        # Clean vertical entry slots identical to yesterday's format
        assisted_pullups = st.number_input(
            label="Assisted Pullups",
            min_value=0, max_value=100, value=0, step=1
        )
        
        st.write("---")
        
        run_time = st.number_input(
            label="Run Time (e.g. 6.30)", 
            min_value=0.0, max_value=30.0, value=0.0, step=0.01
        )
        
        st.write("---")
        
        # Embedded Auto-Regulation Guidelines
        with st.expander("⚠️ View Auto-Regulation Rules (Shin Splints / Fatigue)"):
            st.write("""
            * **High Fatigue?** Reduce intensity (fewer sets, lighter weights, easier intervals).
            * **Poor Recovery?** Swap next workout for a recovery day.
            * **Shin Splints Flare Up?** Replace running with Bike, Swim, Row, or Incline Walk.
            * **Progress Stalled (2-3 Wks)?** Increase volume slightly (+1 set, extra interval).
            * **Feeling Great?** Push intensity slightly, *NOT* volume.
            """)
            
        submit_btn = st.form_submit_button("Submit Training Log")
        
        if submit_btn:
            formatted_run_time = f"{run_time:.2f}".replace('.', ':')
            
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                insert_query = """
                    INSERT INTO physical_performance (date, pullups, run_time)
                    VALUES (%s, %s, %s);
                """
                cur.execute(insert_query, (selected_date, assisted_pullups, formatted_run_time))
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
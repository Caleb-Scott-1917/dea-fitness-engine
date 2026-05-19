import json
from datetime import datetime
import psycopg2
from utils.db_manager import get_db_connection

def dict_factory(cursor, row):
    """Utility helper to dynamically convert Postgres tuples into row dictionaries."""
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))

def load_workouts():
    """Retrieves all historical logged workouts from the cloud ordered chronologically."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT program_day, workout_name, muscle_group, timestamp, exercises_json FROM workouts ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    
    # Process rows manually to preserve structural payload consistency
    fields = [col[0] for col in cursor.description]
    workouts = []
    for r in rows:
        row_dict = dict(zip(fields, r))
        workouts.append({
            "program_day": row_dict["program_day"],
            "workout_name": row_dict["workout_name"],
            "muscle_group": row_dict["muscle_group"],
            "timestamp": row_dict["timestamp"],
            "exercises": json.loads(row_dict["exercises_json"])
        })
        
    cursor.close()
    conn.close()
    return workouts

def save_workout_log(workout_data):
    """Saves a workout performance row to the relational cloud database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO workouts (timestamp, program_day, workout_name, muscle_group, exercises_json)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        timestamp,
        int(workout_data["program_day"]),
        workout_data["workout_name"],
        workout_data["muscle_group"],
        json.dumps(workout_data["exercises"])
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def load_biometrics():
    """Reassembles the historical biometrics tracking tracking timeline payload from separate database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch structural baselines (Get most recent entry if available)
    cursor.execute("SELECT height_in, wingspan_in, femur_proportion, arm_proportion, ankle_mobility_restricted, shoulder_mobility_restricted FROM structural_baselines ORDER BY id DESC LIMIT 1")
    sb_raw = cursor.fetchone()
    sb_row = dict(zip([c[0] for c in cursor.description], sb_raw)) if sb_raw else None
    
    # Fetch daily physiological vitals tracking lists
    cursor.execute("SELECT timestamp, weight, rhr, hrv, sleep, body_fat, calories, protein, hydration, lean_mass FROM daily_vitals ORDER BY timestamp ASC")
    v_raw = cursor.fetchall()
    v_fields = [c[0] for c in cursor.description]
    vital_rows = [dict(zip(v_fields, r)) for r in v_raw]
    
    # Fetch PFT historical testing entries
    cursor.execute("SELECT total_score FROM pft_history ORDER BY id ASC")
    pft_rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Assemble structured profile output formats
    bio_payload = {
        "height_in": sb_row["height_in"] if sb_row else 0.0,
        "structural_baselines": {
            "wingspan_in": sb_row["wingspan_in"] if sb_row else 0.0,
            "femur_proportion": sb_row["femur_proportion"] if sb_row else "Neutral",
            "arm_proportion": sb_row["arm_proportion"] if sb_row else "Neutral",
            "ankle_mobility_restricted": bool(sb_row["ankle_mobility_restricted"]) if sb_row else False,
            "shoulder_mobility_restricted": bool(sb_row["shoulder_mobility_restricted"]) if sb_row else False
        },
        "weight": [r["weight"] for r in vital_rows],
        "sleep": [r["sleep"] for r in vital_rows],
        "hrv": [r["hrv"] for r in vital_rows],
        "rhr": [r["rhr"] for r in vital_rows],
        "body_fat": [r["body_fat"] for r in vital_rows],
        "calories": [r["calories"] for r in vital_rows],
        "protein": [r["protein"] for r in vital_rows],
        "hydration": [r["hydration"] for r in vital_rows],
        "pft_scores": [r[0] for r in pft_rows],
        "history": []
    }
    
    for r in vital_rows:
        bio_payload["history"].append({
            "timestamp": r["timestamp"], "weight": r["weight"], "rhr": r["rhr"], "hrv": r["hrv"],
            "sleep": r["sleep"], "body_fat": r["body_fat"], "calories": r["calories"],
            "protein": r["protein"], "hydration": r["hydration"], "lean_mass": r["lean_mass"]
        })
        
    return bio_payload

def save_biometrics(bio_data):
    """Saves structural profile modifications or appends new daily indicators to cloud tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Update/Insert Structural Baselines Configuration
    sb = bio_data.get("structural_baselines", {})
    cursor.execute("""
        INSERT INTO structural_baselines (height_in, wingspan_in, femur_proportion, arm_proportion, ankle_mobility_restricted, shoulder_mobility_restricted)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        float(bio_data.get("height_in", 0.0)),
        float(sb.get("wingspan_in", 0.0)),
        sb.get("femur_proportion", "Neutral"),
        sb.get("arm_proportion", "Neutral"),
        1 if sb.get("ankle_mobility_restricted", False) else 0,
        1 if sb.get("shoulder_mobility_restricted", False) else 0
    ))
    
    # 2. Synchronize dynamic timeline tracking metrics to cloud tables
    if bio_data.get("history") and len(bio_data["weight"]) > 0:
        cursor.execute("SELECT COUNT(*) FROM daily_vitals")
        db_count = cursor.fetchone()[0]
        
        if len(bio_data["history"]) > db_count:
            latest_log = bio_data["history"][-1]
            cursor.execute("""
                INSERT INTO daily_vitals (timestamp, weight, rhr, hrv, sleep, body_fat, calories, protein, hydration, lean_mass)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                latest_log["timestamp"], float(latest_log["weight"]), int(latest_log["rhr"]), int(latest_log["hrv"]),
                float(latest_log["sleep"]), float(latest_log["body_fat"]), int(latest_log["calories"]), int(latest_log["protein"]),
                int(latest_log["hydration"]), float(latest_log["lean_mass"])
            ))
            
    # 3. Synchronize PFT scores
    if bio_data.get("pft_scores"):
        cursor.execute("SELECT COUNT(*) FROM pft_history")
        pft_count = cursor.fetchone()[0]
        if len(bio_data["pft_scores"]) > pft_count:
            cursor.execute("""
                INSERT INTO pft_history (timestamp, total_score)
                VALUES (%s, %s)
            """, (datetime.now().isoformat(), int(bio_data["pft_scores"][-1])))

    conn.commit()
    cursor.close()
    conn.close()
    return True

def generate_ledger_export():
    """Reads all relational cloud database tables using engine streaming configurations."""
    import pandas as pd
    conn = get_db_connection()
    
    df_vitals = pd.read_sql_query("SELECT * FROM daily_vitals ORDER BY timestamp DESC", conn)
    df_workouts = pd.read_sql_query("SELECT * FROM workouts ORDER BY timestamp DESC", conn)
    df_pft = pd.read_sql_query("SELECT * FROM pft_history ORDER BY timestamp DESC", conn)
    df_structure = pd.read_sql_query("SELECT * FROM structural_baselines ORDER BY id DESC", conn)
    
    conn.close()
    
    for df in [df_vitals, df_workouts, df_pft]:
        if not df.empty and "timestamp" in df.columns:
            df["Date/Time"] = pd.to_datetime(df["timestamp"]).dt.strftime('%Y-%m-%d %H:%M')
            df.drop(columns=["timestamp"], inplace=True)
            
    return {
        "Daily Vitals & Fuel": df_vitals,
        "Completed Workouts": df_workouts,
        "PFT Testing History": df_pft,
        "Structural Baselines": df_structure
    }
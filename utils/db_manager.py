import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

# =========================================================================
# LIVE CLOUD DATABASE CONNECTION STRING (QUOTATION ALIGNMENT FIXED)
# =========================================================================
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_xP7M2pbmwTUe@ep-holy-cloud-aql1yxu1.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    """Establishes a connection to the hosted cloud Neon PostgreSQL database."""
    conn = psycopg2.connect(NEON_DATABASE_URL)
    return conn

def init_db():
    """Initializes cloud database tables using PostgreSQL syntax if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Workouts Master Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id SERIAL PRIMARY KEY,
            timestamp TEXT NOT NULL,
            program_day INTEGER NOT NULL,
            workout_name TEXT NOT NULL,
            muscle_group TEXT NOT NULL,
            exercises_json TEXT NOT NULL
        )
    """)
    
    # 2. Daily Physiological & Fuel Vitals Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_vitals (
            id SERIAL PRIMARY KEY,
            timestamp TEXT NOT NULL,
            weight REAL NOT NULL,
            rhr INTEGER NOT NULL,
            hrv INTEGER NOT NULL,
            sleep REAL NOT NULL,
            body_fat REAL NOT NULL,
            calories INTEGER NOT NULL,
            protein INTEGER NOT NULL,
            hydration INTEGER NOT NULL,
            lean_mass REAL NOT NULL
        )
    """)
    
    # 3. Structural Baselines Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS structural_baselines (
            id SERIAL PRIMARY KEY,
            height_in REAL NOT NULL,
            wingspan_in REAL NOT NULL,
            femur_proportion TEXT NOT NULL,
            arm_proportion TEXT NOT NULL,
            ankle_mobility_restricted INTEGER NOT NULL,
            shoulder_mobility_restricted INTEGER NOT NULL
        )
    """)
    
    # 4. PFT Historical Scores Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pft_history (
            id SERIAL PRIMARY KEY,
            timestamp TEXT NOT NULL,
            total_score INTEGER NOT NULL
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# Auto-initialize on import to ensure your cloud tables are spun up safely
init_db()
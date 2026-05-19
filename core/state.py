import json
import os
import math
from utils.logger import log_system_error

def load_json(path):
    try:
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        log_system_error(e, "Failed to read legacy JSON fallback.")
        return []

def calculate_fatigue(sleep, hrv, sessions):
    sleep_score = sleep / 8
    hrv_score = hrv / 100
    volume_penalty = min(sessions / 7, 1)

    fatigue = 1 - (
        (sleep_score * 0.4)
        + (hrv_score * 0.4)
        + ((1 - volume_penalty) * 0.2)
    )
    return round(max(0, min(fatigue, 1)), 2)

def build_state():
    try:
        from utils.save_workout import load_workouts, load_biometrics
        workouts = load_workouts()
        bio = load_biometrics()

        weight_series = bio.get("weight", [])
        sleep_series = bio.get("sleep", [])
        hrv_series = bio.get("hrv", [])
        rhr_series = bio.get("rhr", [])
        bf_series = bio.get("body_fat", [])
        cal_series = bio.get("calories", [])
        prot_series = bio.get("protein", [])
        hyd_series = bio.get("hydration", [])
        pft_series = bio.get("pft_scores", [])
        
        height_in = bio.get("height_in", 0.0)
        baselines = bio.get("structural_baselines", {})

        volume_series = []
        for w in workouts:
            total = 0
            for ex in w.get("exercises", []):
                sets = ex.get("sets", 0)
                reps = ex.get("reps", 0)
                weight = ex.get("weight", 0)
                total += sets * reps * weight
            volume_series.append(total)

        if workouts:
            last_muscle = workouts[-1].get("muscle_group", "unknown")
        else:
            last_muscle = "none"

        sleep_avg = sum(sleep_series[-7:]) / len(sleep_series[-7:]) if sleep_series else 7.5
        hrv_avg = sum(hrv_series[-7:]) / len(hrv_series[-7:]) if hrv_series else 65.0
        rhr_avg = sum(rhr_series[-7:]) / len(rhr_series[-7:]) if rhr_series else 60.0
        cal_avg = sum(cal_series[-7:]) / len(cal_series[-7:]) if cal_series else 2500.0
        prot_avg = sum(prot_series[-7:]) / len(prot_series[-7:]) if prot_series else 160.0
        hyd_avg = sum(hyd_series[-7:]) / len(hyd_series[-7:]) if hyd_series else 100.0
        
        weight_current = weight_series[-1] if weight_series else 0.0
        latest_pft = pft_series[-1] if pft_series else 0

        # --- ADVANCED BIOMETRIC ZONING SPECIFICATION ---
        # Calculate standard deviation over the last 7 entries to build a dynamic baseline envelope
        hrv_status = "Optimal"
        if len(hrv_series) >= 3:
            recent_hrv = hrv_series[-7:]
            mean_hrv = sum(recent_hrv) / len(recent_hrv)
            variance = sum((x - mean_hrv) ** 2 for x in recent_hrv) / len(recent_hrv)
            std_dev = math.sqrt(variance)
            
            # Use 0.75 * standard deviation as a personalized threshold boundary
            lower_bound = mean_hrv - (0.75 * std_dev)
            current_hrv = hrv_series[-1]
            
            if current_hrv < lower_bound:
                hrv_status = "Suppressed (CNS Strain)"
            elif current_hrv > mean_hrv + (1.5 * std_dev):
                hrv_status = "Sympathetic Parasympathetic Bounce"

        fatigue_score = calculate_fatigue(sleep_avg, hrv_avg, len(workouts))
        total_workouts = len(workouts)
        program_day = (total_workouts % 14) + 1

        return {
            "last_muscle": last_muscle, "fatigue_score": fatigue_score,
            "sleep_avg": sleep_avg, "hrv_avg": hrv_avg, "rhr_avg": rhr_avg,
            "cal_avg": cal_avg, "prot_avg": prot_avg, "hyd_avg": hyd_avg,
            "latest_pft": latest_pft, "weight_current": weight_current,
            "height_in": height_in, "program_day": program_day,
            "weight_series": weight_series, "sleep_series": sleep_series,
            "hrv_series": hrv_series, "volume_series": volume_series,
            "pft_series": pft_series, "structural_baselines": baselines,
            "shin_splints": baselines.get("ankle_mobility_restricted", False),
            "hrv_status": hrv_status  # Sent to dashboard
        }
    except Exception as e:
        log_system_error(e, "Critical engine breakdown inside build_state(). Defaults injected.")
        return {
            "last_muscle": "none", "fatigue_score": 0.0, "sleep_avg": 8.0, "hrv_avg": 70.0,
            "rhr_avg": 60.0, "cal_avg": 2500, "prot_avg": 160, "hyd_avg": 100, "latest_pft": 0,
            "weight_current": 185.0, "height_in": 70.0, "program_day": 1, "weight_series": [],
            "sleep_series": [], "hrv_series": [], "volume_series": [], "pft_series": [],
            "structural_baselines": {}, "shin_splints": False, "hrv_status": "System Standby"
        }
import streamlit as st
import pandas as pd
from datetime import datetime

from core.state import build_state
from core.engine import run_engine
from core.tactical_scoring import calculate_pft_score, calculate_progression
from utils.save_workout import save_workout_log, load_workouts, load_biometrics, save_biometrics, generate_ledger_export
from templates.workouts import workout_templates
from utils.logger import log_system_error

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="DEA Athletic Performance System",
    page_icon="🧠",
    layout="wide"
)

state = build_state()
output = run_engine(state)
history = load_workouts()
bio_data = load_biometrics()

st.title("🧠 DEA Athletic Performance System")
st.caption("Adaptive 14-Day DEA Hybrid Training Engine")

dashboard_tab, workout_tab, bio_tab = st.tabs([
    "📊 Dashboard",
    "🏋️ Workout Log",
    "🩺 Biometrics & Fuel"
])

# ==================================================
# 1. DASHBOARD TAB
# ==================================================
with dashboard_tab:
    st.header("🧠 Operational Readiness Status")

    ori_score = 100.0
    if bio_data["history"]:
        fatigue_component = (1.0 - state["fatigue_score"]) * 40
        sleep_component = min((state["sleep_avg"] / 8.0), 1.0) * 30
        hrv_component = min((state["hrv_avg"] / 75.0), 1.0) * 30
        ori_score = fatigue_component + sleep_component + hrv_component

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Operational Readiness (ORI)", f"{ori_score:.1f}%")
    col2.metric("Systemic Fatigue Score", f"{state['fatigue_score']:.2f}")
    col3.metric("Autonomic HRV Avg", f"{state['hrv_avg']:.1f} ms")
    col4.metric("CNS Zone Profile", state["hrv_status"])  # Displays personalized SD category

    st.divider()

    left_col, right_col = st.columns([2, 1])
    with left_col:
        st.header("🏋️ Today’s Workout Plan")
        st.subheader(output["workout"]["name"])
        st.caption(f"Type: **{output['workout']['type'].upper()}** | Target: **{output['workout']['muscle_group'].upper()}**")
        
        st.markdown("### Exercises")
        for ex in output["workout"]["exercises"]:
            st.markdown(f" * {ex}")

    with right_col:
        st.header("💤 Recovery Context")
        if state["fatigue_score"] > 0.75:
            st.error("💥 High Fatigue: Recovery Day Substituted")
        elif state["fatigue_score"] > 0.55:
            st.warning("⚠️ Moderate Fatigue: Dropping Working Volume")
        else:
            st.success("⚡ Good Recovery: Safe to Progress")

        st.divider()
        st.markdown("**Daily Fuel Environment**")
        st.info(f"🥑 Nutrition: **{state['cal_avg']:.0f} kcal** | 🥩 Protein: **{state['prot_avg']:.0f}g** | 💧 Fluid: **{state['hyd_avg']:.1f} oz**")

    st.divider()
    st.header("📊 Advanced Biomechanical & Physiological Analytics")
    
    if bio_data["history"]:
        df_bio = pd.DataFrame(bio_data["history"])
        df_bio["Date"] = pd.to_datetime(df_bio["timestamp"]).dt.date
        df_bio = df_bio.set_index("Date")

        st.subheader("🎯 Recovery Sweet Spot: Sleep vs. Autonomic HRV")
        st.scatter_chart(data=df_bio, x="sleep", y="hrv", color="#2ecc71", use_container_width=True)

        st.divider()
        st.subheader("📉 Rolling Baselines: Smoothing Fluctuations")
        df_bio["Weight (7-Day Rolling)"] = df_bio["weight"].rolling(window=7, min_periods=1).mean()
        df_bio["RHR (7-Day Rolling)"] = df_bio["rhr"].rolling(window=7, min_periods=1).mean()

        graph_col1, graph_col2 = st.columns(2)
        with graph_col1:
            st.line_chart(df_bio["Weight (7-Day Rolling)"])
        with graph_col2:
            st.line_chart(df_bio["RHR (7-Day Rolling)"])
    else:
        st.info("Log daily metrics inside your Biometrics tab to generate analytics data fields.")

# ==================================================
# 2. WORKOUT TAB
# ==================================================
with workout_tab:
    st.header("🏋️ Workout Tracker")
    st.subheader(output["workout"]["name"])
    st.caption(f"Day {output['program_day']} of 14")
    st.divider()

    if output["program_day"] == 14:
        st.subheader("🏁 Official Physical Fitness Test (PFT) Evaluation")
        with st.form("pft_evaluation_form"):
            p_col1, p_col2, p_col3 = st.columns(3)
            p_pushups = p_col1.number_input("Max Push-Ups (1-Min)", min_value=0, step=1, value=45)
            p_situps = p_col2.number_input("Max Sit-Ups (1-Min)", min_value=0, step=1, value=45)
            p_run = p_col3.number_input("1.5-Mile Run Time (Minutes decimal)", min_value=0.0, step=0.1, value=11.0)
            
            submit_pft = st.form_submit_button("🏁 Complete Evaluation & Score Performance")
            if submit_pft:
                try:
                    pts_push = calculate_pft_score("push_ups", p_pushups)
                    pts_sit = calculate_pft_score("sit_ups", p_situps)
                    pts_run = calculate_pft_score("run_1_5_mile", p_run)
                    total_pft = pts_push + pts_sit + pts_run
                    
                    bio_data["pft_scores"].append(total_pft)
                    save_biometrics(bio_data)
                    st.success(f"PFT Complete! Score: {total_pft}/30 pts")
                    st.rerun()
                except Exception as e:
                    log_system_error(e, "PFT pipeline submission crashed.")
                    st.error("Submission pending database checkout connection error.")
    else:
        st.subheader("📜 Previous Session Performance Summary")
        last_session = None
        for w in reversed(history):
            if w.get("workout_name") == output["workout"]["name"]:
                last_session = w
                break

        if last_session:
            for ex in last_session.get("exercises", []):
                st.markdown(f"**{ex['exercise']}** → `{ex['weight']} lbs` × `{ex['reps']} reps` × `{ex['sets']} sets`")
        else:
            st.info("No historical tracking found for this training split segment.")

        st.divider()
        st.subheader("📝 Log Today's Performance")
        
        with st.form("workout_logging_form", clear_on_submit=False):
            logged_exercises = []

            for i, default_ex in enumerate(output["workout"]["exercises"]):
                m_group = output["workout"]["muscle_group"]
                available_options = workout_templates.get(m_group, workout_templates["push"])
                
                if default_ex not in available_options:
                    available_options = [default_ex] + available_options
                    
                st.markdown(f"#### 🏋️ Movement Slot {i+1}")
                selected_ex = st.selectbox(f"Select Variation for Slot {i+1}:", options=available_options, index=available_options.index(default_ex), key=f"ex_select_{i}")
                safe_key = selected_ex.replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "")
                
                d_w, d_r, d_s = 0.0, 0, 0
                prog_msg = "No historical variation logs found to calculate overload steps."
                
                var_session = None
                for w in reversed(history):
                    for completed_ex in w.get("exercises", []):
                        if completed_ex["exercise"] == selected_ex:
                            var_session = completed_ex
                            break
                    if var_session:
                        break

                if var_session:
                    d_w, d_r, d_s, prog_msg = calculate_progression(float(var_session.get("weight", 0.0)), int(var_session.get("reps", 0)), int(var_session.get("sets", 0)), state["fatigue_score"])
                    st.caption(f"⏱️ **Last variant performance:** {var_session['weight']} lbs × {var_session['reps']} × {var_session['sets']}")
                
                st.caption(f"⚙️ **{prog_msg}**")
                
                col1, col2, col3 = st.columns(3)
                weight = col1.number_input("Weight (lbs)", min_value=0.0, value=float(d_w), step=2.5, key=f"{safe_key}_w_{i}")
                reps = col2.number_input("Reps", min_value=0, value=int(d_r), step=1, key=f"{safe_key}_r_{i}")
                sets = col3.number_input("Sets", min_value=0, value=int(d_s), step=1, key=f"{safe_key}_s_{i}")

                logged_exercises.append({"exercise": selected_ex, "weight": weight, "reps": reps, "sets": sets})
                st.markdown("---")

            submit_workout = st.form_submit_button("💾 Commit Workout to Master Ledger", use_container_width=True)
            if submit_workout:
                has_data = any(item["sets"] > 0 and item["reps"] > 0 for item in logged_exercises)
                if not has_data:
                    st.error("Submission blocked: Empty logs cannot be written to database storage.")
                else:
                    try:
                        workout_data = {"program_day": output["program_day"], "workout_name": output["workout"]["name"], "muscle_group": output["workout"]["muscle_group"], "exercises": logged_exercises}
                        save_workout_log(workout_data)
                        st.success("Session captured successfully!")
                        st.rerun()
                    except Exception as e:
                        log_system_error(e, "Workout tracking submission form crash caught.")
                        st.error("Local file storage busy. Check logs for write diagnostics.")

# ==================================================
# 3. BIOMETRICS & FUEL INTAKE TAB
# ==================================================
with bio_tab:
    st.header("🩺 Biometrics, Proportions & Fuel Tracking Hub")
    st.divider()

    st.subheader("📐 Biomechanical Baseline Profiles")
    current_height = bio_data.get("height_in", 0.0)
    baselines = bio_data.get("structural_baselines", {})
    
    with st.form("structural_baseline_form"):
        col_s1, col_s2 = st.columns(2)
        sb_height = col_s1.number_input("Height (inches)", min_value=0.0, value=float(current_height), step=0.5)
        sb_wingspan = col_s2.number_input("Wingspan (inches)", min_value=0.0, value=float(baselines.get("wingspan_in", 0.0)), step=0.5)
        
        col_s3, col_s4 = st.columns(2)
        femur_opts = ["Neutral", "Long Femurs", "Short Femurs"]
        arm_opts = ["Neutral", "Long Arms", "Short Arms"]
        sb_femur = col_s3.selectbox("Femur-to-Torso Proportion Layout", femur_opts, index=femur_opts.index(baselines.get("femur_proportion", "Neutral")))
        sb_arm = col_s4.selectbox("Arm-to-Torso Proportion Layout", arm_opts, index=arm_opts.index(baselines.get("arm_proportion", "Neutral")))
        
        col_s5, col_s6 = st.columns(2)
        sb_ankle = col_s5.checkbox("Restricted Ankle Dorsiflexion Range", value=bool(baselines.get("ankle_mobility_restricted", False)))
        sb_shoulder = col_s6.checkbox("Restricted Shoulder Clearance Rotation", value=bool(baselines.get("shoulder_mobility_restricted", False)))
        
        if st.form_submit_button("⚙️ Save Structural Baselines"):
            try:
                bio_data["height_in"] = sb_height
                bio_data["structural_baselines"] = {"wingspan_in": sb_wingspan, "femur_proportion": sb_femur, "arm_proportion": sb_arm, "ankle_mobility_restricted": sb_ankle, "shoulder_mobility_restricted": sb_shoulder}
                save_biometrics(bio_data)
                st.success("Structural profile updated.")
                st.rerun()
            except Exception as e:
                log_system_error(e, "Baseline save execution blocked.")
                st.error("Baseline metrics adjustment lock active.")

    st.divider()
    st.subheader("📝 Daily Intake Metrics & Recovery Vitals")
    
    last_w = bio_data["weight"][-1] if bio_data["weight"] else 185.0
    last_rhr = bio_data["rhr"][-1] if bio_data["rhr"] else 60
    last_hrv = bio_data["hrv"][-1] if bio_data["hrv"] else 65
    last_sleep = bio_data["sleep"][-1] if bio_data["sleep"] else 7.5
    last_bf = bio_data["body_fat"][-1] if bio_data["body_fat"] else 15.0
    last_cal = bio_data["calories"][-1] if bio_data["calories"] else 2500
    last_prot = bio_data["protein"][-1] if bio_data["protein"] else 160
    last_hyd = bio_data["hydration"][-1] if bio_data["hydration"] else 100

    with st.form("daily_metrics_and_macros_form"):
        st.markdown("**Physiological Indicators**")
        v_col1, v_col2, v_col3, v_col4, v_col5 = st.columns(5)
        b_weight = v_col1.number_input("Weight (lbs)", min_value=0.0, value=float(last_w))
        b_rhr = v_col2.number_input("RHR (bpm)", min_value=0, value=int(last_rhr))
        b_hrv = v_col3.number_input("HRV (ms)", min_value=0, value=int(last_hrv))
        b_sleep = v_col4.number_input("Sleep (hrs)", min_value=0.0, value=float(last_sleep))
        b_bf = v_col5.number_input("Body Fat %", min_value=0.0, value=float(last_bf))
        
        st.markdown("---")
        st.markdown("**Fuel & Nutrition Indicators**")
        n_col1, n_col2, n_col3 = st.columns(3)
        b_cal = n_col1.number_input("Caloric Intake (kcal)", min_value=0, value=int(last_cal), step=50)
        b_prot = n_col2.number_input("Protein Intake (grams)", min_value=0, value=int(last_prot), step=5)
        b_hyd = n_col3.number_input("Fluid Ingestion (ounces)", min_value=0, value=int(last_hyd), step=8)

        if st.form_submit_button("💾 Commit Daily Metrics to Ledger", use_container_width=True):
            try:
                timestamp_str = datetime.now().isoformat()
                lean_mass_est = b_weight * (1 - (b_bf / 100))
                
                bio_data["weight"].append(b_weight)
                bio_data["rhr"].append(b_rhr)
                bio_data["hrv"].append(b_hrv)
                bio_data["sleep"].append(b_sleep)
                bio_data["body_fat"].append(b_bf)
                bio_data["calories"].append(b_cal)
                bio_data["protein"].append(b_prot)
                bio_data["hydration"].append(b_hyd)
                
                bio_data["history"].append({
                    "timestamp": timestamp_str, "weight": b_weight, "rhr": b_rhr, "hrv": b_hrv, 
                    "sleep": b_sleep, "body_fat": b_bf, "calories": b_cal, "protein": b_prot, 
                    "hydration": b_hyd, "lean_mass": round(lean_mass_est, 2)
                })
                
                save_biometrics(bio_data)
                st.success("Physiological data saved!")
                st.rerun()
            except Exception as e:
                log_system_error(e, "Dynamic metrics pipeline write exception.")
                st.error("Database connection write check failed.")

    # Data Portability Download Block
    st.divider()
    st.subheader("📥 Data Portability & Ledger Maintenance")
    import io
    try:
        export_data = generate_ledger_export()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            for sheet_name, df_sheet in export_data.items():
                if not df_sheet.empty and "id" in df_sheet.columns:
                    df_sheet = df_sheet.drop(columns=["id"])
                df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
        
        st.download_button(
            label="📥 Export Master Training Ledger to Excel",
            data=buffer.getvalue(),
            file_name=f"Tactical_Performance_Ledger_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        log_system_error(e, "Excel write stream generation failed.")
        st.error(f"Export utility standby.")
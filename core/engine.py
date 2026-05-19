from templates.program import PROGRAM_14_DAY


def run_engine(state):

    rules_triggered = []

    # =========================================
    # CURRENT PROGRAM DAY
    # =========================================

    current_day = state["program_day"]

    base_workout = PROGRAM_14_DAY[current_day]

    workout = base_workout.copy()

    # =========================================
    # HIGH FATIGUE RULE
    # =========================================

    if state["fatigue_score"] > 0.75:

        workout = {
            "name": "Recovery Override",
            "type": "recovery",
            "muscle_group": "recovery",
            "exercises": [
                "Zone 2 cardio",
                "Mobility work",
                "Stretching",
                "Light recovery work"
            ]
        }

        rules_triggered.append(
            "High fatigue detected → recovery day substituted"
        )

    # =========================================
    # SHIN SPLINT RULE
    # =========================================

    if state.get("shin_splints", False):

        updated_exercises = []

        for ex in workout["exercises"]:

            if "Sprint" in ex or "Run" in ex:

                updated_exercises.append(
                    ex.replace("Sprint", "Bike Sprint")
                )

            else:

                updated_exercises.append(ex)

        workout["exercises"] = updated_exercises

        rules_triggered.append(
            "Shin splint rule activated → replaced running with bike work"
        )

    # =========================================
    # MODERATE FATIGUE RULE
    # =========================================

    if (
        state["fatigue_score"] > 0.55
        and workout["type"] != "recovery"
    ):

        rules_triggered.append(
            "Moderate fatigue → reduce intensity slightly"
        )

    # =========================================
    # EXCELLENT RECOVERY RULE
    # =========================================

    if state["fatigue_score"] < 0.30:

        rules_triggered.append(
            "Excellent recovery → increase intensity slightly"
        )

    # =========================================
    # RETURN OUTPUT
    # =========================================

    return {
        "program_day": current_day,
        "workout": workout,
        "rules": rules_triggered
    }
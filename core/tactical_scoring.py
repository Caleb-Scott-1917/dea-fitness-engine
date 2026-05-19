def calculate_pft_score(event_type, performance):
    """
    Calculates standardized tactical point scoring (0 to 10 points) per event.
    Standardized benchmarking models for push-ups (1-min), sit-ups (1-min), and run.
    """
    if performance <= 0:
        return 0
        
    if event_type == "push_ups":
        # Example scale: 10 pts for 60+, 1 pt per 5 reps under baseline
        if performance >= 60: return 10
        if performance >= 50: return 8
        if performance >= 40: return 6
        if performance >= 30: return 4
        return 2
        
    elif event_type == "sit_ups":
        if performance >= 55: return 10
        if performance >= 45: return 8
        if performance >= 35: return 6
        if performance >= 25: return 4
        return 2
        
    elif event_type == "run_1_5_mile":
        # Timed event in minutes (e.g., 10.0 = 10 mins 0 secs)
        if performance <= 10.0: return 10
        if performance <= 11.0: return 8
        if performance <= 12.0: return 6
        if performance <= 13.0: return 4
        return 2
        
    return 0

def calculate_progression(last_weight, last_reps, last_sets, fatigue_score):
    """
    Progressive Overload Engine: Recommends targets based on current physical capacity.
    """
    # If high fatigue is detected, protect joints and suppress intensity rules
    if fatigue_score > 0.55:
        return last_weight, last_reps, last_sets, "Auto-Regulation: Fatigue high. Holding baseline to support recovery."
        
    # If fresh (Green zone), calculate a structured micro-overload step
    if last_weight > 0:
        # Increment compound movements by a precise 2.5% to 5% micro-load
        suggested_weight = last_weight + 2.5 if last_weight < 100 else last_weight + 5.0
        return suggested_weight, last_reps, last_sets, f"Progression: Fresh recovery zone. Load stepped up +{suggested_weight - last_weight} lbs."
    else:
        # Increment bodyweight/endurance testing movements by volume reps
        suggested_reps = last_reps + 2 if last_reps > 0 else 0
        return last_weight, suggested_reps, last_sets, "Progression: Fresh recovery zone. Target repetition counts scaled up."
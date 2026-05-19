import json
from datetime import datetime

WORKOUT_FILE = "data/workouts.json"


def load_workouts():
    try:
        with open(WORKOUT_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_workout(workout_entry):

    workouts = load_workouts()

    workouts.append(workout_entry)

    with open(WORKOUT_FILE, "w") as f:
        json.dump(workouts, f, indent=2)
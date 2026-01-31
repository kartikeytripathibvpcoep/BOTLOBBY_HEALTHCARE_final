import os
import json
import random
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# =========================
# ENV
# =========================
load_dotenv()
api_key = 
if not api_key:
    raise ValueError("GROQ_API_KEY not set")

client = Groq(api_key=api_key)

DATA_FILE = "cleaned_output.csv"
LEARNING_FILE = "learning_state.json"

# =========================
# LEARNING STATE (PERSISTENT)
# =========================
if os.path.exists(LEARNING_FILE):
    with open(LEARNING_FILE, "r") as f:
        LEARNING_STATE = json.load(f)
else:
    LEARNING_STATE = {"risk_multiplier": 1.0}
    with open(LEARNING_FILE, "w") as f:
        json.dump(LEARNING_STATE, f)

def apply_feedback(feedback):
    if feedback == "Incorrect":
        LEARNING_STATE["risk_multiplier"] *= 1.05
        with open(LEARNING_FILE, "w") as f:
            json.dump(LEARNING_STATE, f)

# =========================
# RISK AGENT
# =========================
def risk_agent(age, condition, vitals=None):
    if vitals is None:
        vitals = {"heart_rate": 90, "oxygen": 97, "temperature": 37.0}

    score = 0.0
    c = condition.lower()

    if age >= 60: score += 0.2
    if vitals["heart_rate"] > 110: score += 0.3
    if vitals["oxygen"] < 92: score += 0.4
    if vitals["temperature"] > 38.5: score += 0.2
    if "chest" in c or "heart" in c: score += 0.4

    score *= LEARNING_STATE["risk_multiplier"]

    if score >= 0.7:
        risk = "High"
    elif score >= 0.4:
        risk = "Medium"
    else:
        risk = "Low"

    return {"risk": risk, "score": round(score, 2)}

# =========================
# RESOURCE + DECISION
# =========================
def resource_agent():
    return {
        "icu_beds": random.randint(0, 3),
        "general_beds": random.randint(1, 6),
        "doctors": random.randint(1, 3)
    }

def decision_agent(risk, resources):
    condition = risk.get("condition", "").lower()

    CRITICAL_KEYWORDS = [
        "heart",
        "heart attack",
        "cardiac",
        "chest pain",
        "stroke",
        "respiratory",
        "unconscious",
        "bleeding",
        "collapse"
    ]

    # 🚨 HARD OVERRIDE — NEVER ELECTIVE
    if any(word in condition for word in CRITICAL_KEYWORDS):
        return "Emergency", True

    score = risk["score"]

    if score >= 0.8:
        return "Emergency", True
    elif score >= 0.5 and resources["general_beds"] > 0:
        return "Urgent", True
    else:
        return "Elective", False


def cost_agent(decision):
    return {"Emergency": 100, "Urgent": 50, "Elective": 10}[decision]

def confidence_agent(score, resources):
    penalty = 0.15 if resources["icu_beds"] == 0 else 0
    return round(max(0.3, score - penalty), 2)

# =========================
# CSV PERSISTENCE (CRITICAL)
# =========================
def save_patient_to_dataset(patient, category):
    row = {
        "Name": patient["Name"],
        "Age": patient["Age"],
        "Gender": patient["Gender"],
        "Medical Condition": patient["Condition"],
        "Admission Type": category
    }

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(DATA_FILE, index=False)

def update_patient_category(name, category):
    if not os.path.exists(DATA_FILE):
        return

    df = pd.read_csv(DATA_FILE)
    df.loc[df["Name"] == name, "Admission Type"] = category
    df.to_csv(DATA_FILE, index=False)

# =========================
# LLM EXPLANATIONS
# =========================
def llm_explanation(context):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": str(context)}],
        temperature=0.3
    )
    return res.choices[0].message.content.strip()

def reflection_agent(original, risk, confidence):
    if confidence < 0.7 or risk["risk"] in ["Medium", "High"]:
        return "Emergency", "Safety escalation after doctor feedback"
    return original, "No change"

def llm_reflection_explanation(context):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": str(context)}],
        temperature=0.2
    )
    return res.choices[0].message.content.strip()
import json

LIVE_FILE = "live_patients.json"

def save_live_state(live_emergency, live_urgent, live_elective):
    data = {
        "live_emergency": live_emergency,
        "live_urgent": live_urgent,
        "live_elective": live_elective
    }
    with open(LIVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_live_state():
    if not os.path.exists(LIVE_FILE):
        return [], [], []
    with open(LIVE_FILE, "r") as f:
        data = json.load(f)
    return (
        data.get("live_emergency", []),
        data.get("live_urgent", []),
        data.get("live_elective", [])
    )


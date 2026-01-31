import streamlit as st
import pandas as pd
import json
import os
from app import *

st.set_page_config(page_title="Agentic Hospital AI", layout="wide")
st.title("🏥 Agentic Hospital AI for Hospital Patient Flow")

DATA_FILE = "cleaned_output.csv"
LIVE_FILE = "live_patients.json"

# =========================
# LOAD DATASET (NO CACHE)
# =========================
def load_data():
    return pd.read_csv(DATA_FILE)

df = load_data()

# =========================
# LOAD / SAVE LIVE STATE
# =========================
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

def save_live_state():
    with open(LIVE_FILE, "w") as f:
        json.dump({
            "live_emergency": st.session_state.live_emergency,
            "live_urgent": st.session_state.live_urgent,
            "live_elective": st.session_state.live_elective
        }, f, indent=2)

# =========================
# SESSION STATE INIT (WITH RESTORE)
# =========================
if "live_emergency" not in st.session_state:
    (
        st.session_state.live_emergency,
        st.session_state.live_urgent,
        st.session_state.live_elective
    ) = load_live_state()

if "agent_memory" not in st.session_state:
    st.session_state.agent_memory = []

# =========================
# SPLIT DATASET
# =========================
emergency_patients = df[df["Admission Type"] == "Emergency"]
urgent_patients = df[df["Admission Type"] == "Urgent"]
elective_patients = df[df["Admission Type"] == "Elective"]

# =========================
# METRICS
# =========================
st.header("📊 Hospital Load (Dataset)")
c1, c2, c3 = st.columns(3)
c1.metric("🚨 Emergency", len(emergency_patients))
c2.metric("⚠️ Urgent", len(urgent_patients))
c3.metric("🟢 Elective", len(elective_patients))

# =========================
# DATASET MEMBERS
# =========================
st.header("📂 Existing Patients (Dataset)")

with st.expander("🚨 Emergency Patients"):
    st.dataframe(
        emergency_patients[["Name", "Age", "Gender", "Medical Condition"]],
        width="stretch"
    )

with st.expander("⚠️ Urgent Patients"):
    st.dataframe(
        urgent_patients[["Name", "Age", "Gender", "Medical Condition"]],
        width="stretch"
    )

with st.expander("🟢 Elective Patients"):
    st.dataframe(
        elective_patients[["Name", "Age", "Gender", "Medical Condition"]],
        width="stretch"
    )

# =========================
# NEW PATIENT FORM
# =========================
st.header("🧠 New Patient Evaluation")

with st.form("patient_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", 0, 120)
    gender = st.selectbox("Gender", ["Male", "Female"])
    blood = st.selectbox("Blood Type", ["A+", "A-", "B+", "O+"])
    condition = st.text_input("Medical Condition")
    submit = st.form_submit_button("Run Agentic AI")

# =========================
# AGENT EXECUTION
# =========================
if submit and name and condition:
    risk = risk_agent(age, condition)

# 🔑 attach condition so decision_agent can enforce hard overrides
    risk["condition"] = condition.lower()

    resources = resource_agent()
    decision, admit = decision_agent(risk, resources)
    cost = cost_agent(decision)
    confidence = confidence_agent(risk["score"], resources)

    patient = {
        "Name": name,
        "Age": age,
        "Gender": gender,
        "Condition": condition,
        "Decision": decision,
        "Confidence": confidence
    }

    if decision == "Emergency":
        st.session_state.live_emergency.append(patient)
    elif decision == "Urgent":
        st.session_state.live_urgent.append(patient)
    else:
        st.session_state.live_elective.append(patient)

    save_live_state()

    explanation = llm_explanation({
        "Patient": patient,
        "Risk": risk,
        "Resources": resources,
        "Cost": cost,
        "Confidence": confidence
    })

    st.session_state.agent_memory.append({
        "patient": patient,
        "decision": decision,
        "confidence": confidence,
        "risk": risk,
        "feedback": None,
        "revised_decision": None
    })

    st.success("Decision Completed and Saved")
    st.subheader("✅ Final Decision")
    st.json({
        "Admission": decision,
        "Admit": admit,
        "Confidence": confidence,
        "Cost": cost
    })

    st.subheader("🤖 LLM Reasoning")
    st.markdown(explanation)

# =========================
# LIVE PATIENT GROUPS (PERSISTENT)
# =========================
st.header("📋 Live Patients (Persistent)")

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("🚨 Emergency")
    st.dataframe(st.session_state.live_emergency, width="stretch")

with c2:
    st.subheader("⚠️ Urgent")
    st.dataframe(st.session_state.live_urgent, width="stretch")

with c3:
    st.subheader("🟢 Elective")
    st.dataframe(st.session_state.live_elective, width="stretch")

# =========================
# FEEDBACK + RE-EVALUATION
# =========================
st.header("🧠 Doctor Feedback & Reflection")

if st.session_state.agent_memory:
    record = st.session_state.agent_memory[-1]

    feedback = st.radio("Was the last decision correct?", ["Correct", "Incorrect"])

    if st.button("Save Feedback"):
        record["feedback"] = feedback

        if feedback == "Incorrect":
            revised, reason = reflection_agent(
                record["decision"],
                record["risk"],
                record["confidence"]
            )
            record["revised_decision"] = revised

            reflection_text = llm_reflection_explanation({
                "Original Decision": record["decision"],
                "Revised Decision": revised,
                "Reason": reason,
                "Patient": record["patient"]
            })

            st.warning("🔄 Decision Re-Evaluated")
            st.subheader("🧠 Reflection Explanation")
            st.markdown(reflection_text)

# =========================
# MEMORY VIEW
# =========================
st.header("🧠 Agent Memory Log")
st.json(st.session_state.agent_memory)

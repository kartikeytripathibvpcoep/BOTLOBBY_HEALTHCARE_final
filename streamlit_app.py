import streamlit as st
import pandas as pd
from app import categorize_patients, classify_new_patient, df, emergency_patients, urgent_patients, elective_patients

st.title("Patient Admission Classification System")

# Display categorized admitted patients
st.header("Admitted Patients by Category")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Emergency Patients")
    st.write(f"Total: {len(emergency_patients)}")
    st.dataframe(emergency_patients[['Name', 'Age', 'Gender', 'Medical Condition']].head(10))

with col2:
    st.subheader("Urgent Patients")
    st.write(f"Total: {len(urgent_patients)}")
    st.dataframe(urgent_patients[['Name', 'Age', 'Gender', 'Medical Condition']].head(10))

with col3:
    st.subheader("Elective Patients")
    st.write(f"Total: {len(elective_patients)}")
    st.dataframe(elective_patients[['Name', 'Age', 'Gender', 'Medical Condition']].head(10))

# New patient classification
st.header("Classify New Patient")

with st.form("new_patient_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, max_value=120)
    gender = st.selectbox("Gender", ["Male", "Female"])
    blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
    medical_condition = st.text_input("Medical Condition")

    submitted = st.form_submit_button("Classify Patient")

    if submitted:
        if name and medical_condition:
            with st.spinner("Classifying patient..."):
                result = classify_new_patient(name, age, gender, blood_type, medical_condition)
                st.success("Classification Complete!")
                st.write(f"Result: {result}")

                # Parse result to decide admission
                if "Emergency" in result or "Urgent" in result:
                    admission_decision = "Yes"
                else:
                    admission_decision = "No"

                st.write(f"Needs Admission: {admission_decision}")
        else:
            st.error("Please fill in all required fields.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and Groq API")

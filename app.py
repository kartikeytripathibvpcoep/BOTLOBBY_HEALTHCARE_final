import os
import pandas as pd
from groq import Groq

# ✅ Read API key ONLY from environment
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not set in environment")

# Initialize Groq client
client = Groq(api_key=api_key)

# Input file name
input_file = "cleaned_output.csv"

# Read patient data using pandas
df = pd.read_csv(input_file)

# Ensure Admission Type column exists
if "Admission Type" not in df.columns:
    df["Admission Type"] = None

# Function to categorize patients into Emergency, Urgent, Elective
def categorize_patients(df):
    emergency = df[df["Admission Type"] == "Emergency"]
    urgent = df[df["Admission Type"] == "Urgent"]
    elective = df[df["Admission Type"] == "Elective"]
    return emergency, urgent, elective

# Categorize existing patients
emergency_patients, urgent_patients, elective_patients = categorize_patients(df)

# Function to classify new patient using LLM
def classify_new_patient(name, age, gender, blood_type, medical_condition):
    prompt = (
        f"Given the patient details:\n"
        f"Name: {name}\n"
        f"Age: {age}\n"
        f"Gender: {gender}\n"
        f"Blood Type: {blood_type}\n"
        f"Medical Condition: {medical_condition}\n\n"
        f"Classify the Admission Type as one of: Emergency, Urgent, Elective. "
        f"Also, decide if the patient needs admission based on health condition. "
        f"Respond in format: 'Admission Type: [type], Needs Admission: [Yes/No]'"
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Groq model
        messages=[{"role": "user", "content": prompt}],
    )

    result = response.choices[0].message.content.strip()
    return result

# Function to parse classification result
def parse_classification(result):
    try:
        parts = result.split(",")
        admission_type = parts[0].split(":")[1].strip()
        needs_admission = parts[1].split(":")[1].strip()
        return admission_type, needs_admission
    except Exception:
        # Fallback if parsing fails
        return "Unknown", "No"

# Example usage for new patient
if __name__ == "__main__":
    result = classify_new_patient("John Doe", 45, "Male", "O+", "Hypertension")
    admission_type, needs_admission = parse_classification(result)
    print(f"Admission Type: {admission_type}, Needs Admission: {needs_admission}")

    # Optionally add to DataFrame and save
    new_patient = {
        "Name": "John Doe",
        "Age": 45,
        "Gender": "Male",
        "Blood Type": "O+",
        "Medical Condition": "Hypertension",
        "Admission Type": admission_type,
    }
    df = pd.concat([df, pd.DataFrame([new_patient])], ignore_index=True)
    df.to_csv("cleaned_output_with_admission.csv", index=False)
    print("Updated patient data saved to cleaned_output_with_admission.csv")

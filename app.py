import os
import pandas as pd
from groq import Groq

# Set your Groq API key (store securely!)
os.environ["GROQ_API_KEY"] = "your_api_key"

# Initialize Groq client
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Input file name
input_file = "cleaned_output.csv"

# Read patient data using pandas
df = pd.read_csv(input_file)

# Function to categorize patients into Emergency, Urgent, Elective
def categorize_patients(df):
    emergency = df[df['Admission Type'] == 'Emergency']
    urgent = df[df['Admission Type'] == 'Urgent']
    elective = df[df['Admission Type'] == 'Elective']
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
        f"Classify the Admission Type as one of: Emergency, Urgent, Elective. Also, decide if the patient needs admission based on health condition. Respond in format: 'Admission Type: [type], Needs Admission: [Yes/No]'"
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )

    result = response.choices[0].message.content.strip()
    return result

# Function to decide admission based on classification
def decide_admission(classification):
    # Simple logic: Emergency and Urgent need admission, Elective may not
    if 'Emergency' in classification or 'Urgent' in classification:
        return "Yes"
    else:
        return "No"

# Example usage for new patient (can be called from frontend)
# result = classify_new_patient("John Doe", 45, "Male", "O+", "Hypertension")
# print(result)

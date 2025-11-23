import streamlit as st
from dotenv import load_dotenv
import os
import asyncio
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Import configuration
from config import get_config
config = get_config()

# Import agent orchestrator
from agents.orchestrator import MedicalOrchestrator
from agents.triage_agent import TriageAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.treatment_agent import TreatmentAgent
from agents.research_agent import ResearchAgent
from agents.specialist_router_agent import SpecialistRouterAgent

# Initialize session state
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = {}
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = 'triage'
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

def main():
    st.set_page_config(
        page_title="MediCheck Pro - Medical Assistant AI",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏥 MediCheck Pro - Advanced Medical Assistant AI")
    st.markdown("""
    *An AI-powered medical assistant system with multi-agent orchestration for patient care*
    """)
    
    # Sidebar with navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox("Select Phase", ["Triage", "Diagnosis", "Treatment", "Research", "Specialist Referral"])
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(f"Current Phase: {page}")
        
        if page == "Triage":
            render_triage_interface()
        elif page == "Diagnosis":
            render_diagnosis_interface()
        elif page == "Treatment":
            render_treatment_interface()
        elif page == "Research":
            render_research_interface()
        elif page == "Specialist Referral":
            render_specialist_interface()
    
    with col2:
        st.header("Patient Information")
        render_patient_info()
        
        st.header("System Status")
        render_system_status()

def render_triage_interface():
    st.subheader("Triage Assessment")
    
    with st.form("triage_form"):
        chief_complaint = st.text_input("Chief Complaint", placeholder="e.g., Chest pain, Headache, Fever")
        symptoms = st.text_area("Symptoms", placeholder="Describe symptoms in detail...")
        duration = st.text_input("Duration", placeholder="e.g., 2 days, 1 week")
        severity = st.selectbox("Severity", ["Mild", "Moderate", "Severe", "Critical"])
        
        submitted = st.form_submit_button("Assess Triage Priority")
        
        if submitted:
            with st.spinner("Analyzing patient condition..."):
                # Initialize the orchestrator
                orchestrator = MedicalOrchestrator()
                
                # Prepare patient data
                patient_info = {
                    "chief_complaint": chief_complaint,
                    "symptoms": symptoms,
                    "duration": duration,
                    "severity": severity
                }
                
                # Run triage agent
                triage_result = asyncio.run(orchestrator.run_triage(patient_info))
                
                st.session_state.patient_data.update(patient_info)
                st.session_state.conversation_history.append({
                    "phase": "triage",
                    "input": patient_info,
                    "output": triage_result
                })
                
                st.success("Triage Assessment Complete")
                st.json(triage_result)

def render_diagnosis_interface():
    st.subheader("Medical Diagnosis")
    
    if not st.session_state.patient_data:
        st.warning("Please complete triage assessment first.")
        return
    
    with st.form("diagnosis_form"):
        additional_symptoms = st.text_area("Additional Symptoms", placeholder="Any additional symptoms or observations?")
        medical_history = st.text_area("Medical History", placeholder="Known medical conditions, allergies, medications...")
        vital_signs = st.text_area("Vital Signs", placeholder="Blood pressure, temperature, heart rate, etc.")
        
        submitted = st.form_submit_button("Generate Diagnosis")
        
        if submitted:
            with st.spinner("Analyzing medical condition..."):
                # Initialize the orchestrator
                orchestrator = MedicalOrchestrator()
                
                # Prepare patient data
                patient_info = {
                    "additional_symptoms": additional_symptoms,
                    "medical_history": medical_history,
                    "vital_signs": vital_signs,
                    **st.session_state.patient_data
                }
                
                # Run diagnosis agent
                diagnosis_result = asyncio.run(orchestrator.run_diagnosis(patient_info))
                
                st.session_state.patient_data.update(patient_info)
                st.session_state.conversation_history.append({
                    "phase": "diagnosis",
                    "input": patient_info,
                    "output": diagnosis_result
                })
                
                st.success("Diagnosis Complete")
                st.json(diagnosis_result)

def render_treatment_interface():
    st.subheader("Treatment Recommendations")
    
    if not st.session_state.patient_data.get('diagnosis'):
        st.warning("Please complete diagnosis first.")
        return
    
    with st.form("treatment_form"):
        current_medications = st.text_area("Current Medications", placeholder="List of current medications...")
        contraindications = st.text_area("Contraindications", placeholder="Known drug allergies or contraindications...")
        treatment_preferences = st.text_area("Treatment Preferences", placeholder="Patient preferences or special considerations...")
        
        submitted = st.form_submit_button("Generate Treatment Plan")
        
        if submitted:
            with st.spinner("Generating treatment recommendations..."):
                # Initialize the orchestrator
                orchestrator = MedicalOrchestrator()
                
                # Prepare patient data
                patient_info = {
                    "current_medications": current_medications,
                    "contraindications": contraindications,
                    "treatment_preferences": treatment_preferences,
                    **st.session_state.patient_data
                }
                
                # Run treatment agent
                treatment_result = asyncio.run(orchestrator.run_treatment(patient_info))
                
                st.session_state.patient_data.update(patient_info)
                st.session_state.conversation_history.append({
                    "phase": "treatment",
                    "input": patient_info,
                    "output": treatment_result
                })
                
                st.success("Treatment Plan Generated")
                st.json(treatment_result)

def render_research_interface():
    st.subheader("Medical Literature Research")
    
    with st.form("research_form"):
        research_query = st.text_input("Research Query", placeholder="e.g., Latest treatment for hypertension")
        keywords = st.text_area("Keywords", placeholder="Additional keywords for research...")
        
        submitted = st.form_submit_button("Search Medical Literature")
        
        if submitted:
            with st.spinner("Searching medical literature..."):
                # Initialize the orchestrator
                orchestrator = MedicalOrchestrator()
                
                # Run research agent
                research_result = asyncio.run(orchestrator.run_research(research_query, keywords))
                
                st.session_state.conversation_history.append({
                    "phase": "research",
                    "input": {"query": research_query, "keywords": keywords},
                    "output": research_result
                })
                
                st.success("Research Complete")
                st.json(research_result)

def render_specialist_interface():
    st.subheader("Specialist Referral")
    
    if not st.session_state.patient_data.get('diagnosis'):
        st.warning("Please complete diagnosis first.")
        return
    
    with st.form("specialist_form"):
        diagnosis_summary = st.text_area("Diagnosis Summary", value=st.session_state.patient_data.get('diagnosis', ''))
        urgency_level = st.selectbox("Urgency Level", ["Routine", "Urgent", "Emergency"])
        specialist_type = st.selectbox("Specialist Type", ["Cardiologist", "Neurologist", "Orthopedist", "Dermatologist", "Oncologist", "Other"])
        
        submitted = st.form_submit_button("Route to Specialist")
        
        if submitted:
            with st.spinner("Routing to appropriate specialist..."):
                # Initialize the orchestrator
                orchestrator = MedicalOrchestrator()
                
                # Prepare patient data
                patient_info = {
                    "diagnosis_summary": diagnosis_summary,
                    "urgency_level": urgency_level,
                    "specialist_type": specialist_type,
                    **st.session_state.patient_data
                }
                
                # Run specialist router agent
                specialist_result = asyncio.run(orchestrator.route_to_specialist(patient_info))
                
                st.session_state.patient_data.update(patient_info)
                st.session_state.conversation_history.append({
                    "phase": "specialist",
                    "input": patient_info,
                    "output": specialist_result
                })
                
                st.success("Specialist Routing Complete")
                st.json(specialist_result)

def render_patient_info():
    if st.session_state.patient_data:
        st.json(st.session_state.patient_data)
    else:
        st.info("No patient data available yet.")

def render_system_status():
    st.metric("Active Agents", "5")
    st.metric("Patient Sessions", "1")
    st.metric("Current Phase", st.session_state.current_phase)
    
    if st.session_state.conversation_history:
        st.subheader("Conversation History")
        for i, entry in enumerate(st.session_state.conversation_history):
            with st.expander(f"Entry {i+1}: {entry['phase'].title()}"):
                st.json(entry)

if __name__ == "__main__":
    main()
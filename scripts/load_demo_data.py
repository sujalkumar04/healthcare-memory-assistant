"""
Demo Data Loader for Healthcare Memory Assistant
================================================
Pre-loads realistic patient data for hackathon judges to test immediately.

Run: python scripts/load_demo_data.py

Creates 3 patient scenarios:
- patient_demo_1: Anxiety & Depression treatment journey
- patient_demo_2: Medication adjustment case  
- patient_demo_3: Student mental health support

"""

import asyncio
import httpx
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api/v1"

# ============================================================================
# PATIENT 1: Anxiety & Depression Treatment Journey
# ============================================================================
PATIENT_1 = [
    {
        "patient_id": "patient_demo_1",
        "memory_type": "mental_health",
        "source": "session",
        "raw_text": """Initial Assessment - Week 1:
Patient is a 28-year-old software engineer presenting with symptoms of generalized anxiety 
and moderate depression. Reports persistent worry about work performance, difficulty 
concentrating, and sleep disturbances for the past 3 months. PHQ-9 score: 14 (moderate). 
GAD-7 score: 12 (moderate anxiety). Patient reports feeling 'constantly on edge' and 
experiencing racing thoughts, particularly in the evenings."""
    },
    {
        "patient_id": "patient_demo_1",
        "memory_type": "medication",
        "source": "doctor",
        "raw_text": """Medication Started - Week 1:
Initiated sertraline 25mg daily for anxiety and depression management. Patient counseled 
on expected timeline for therapeutic effect (4-6 weeks) and potential initial side effects 
including nausea, headache, and temporary increase in anxiety. Will titrate to 50mg after 
2 weeks if tolerated. Advised to take medication in the morning with food."""
    },
    {
        "patient_id": "patient_demo_1",
        "memory_type": "mental_health",
        "source": "session",
        "raw_text": """Follow-up - Week 3:
Patient reports mild improvement in overall mood. Sleep quality slightly better - falling 
asleep within 30 minutes instead of 2 hours. Still experiencing work-related anxiety but 
describes it as 'more manageable'. Experienced mild nausea during first week which has 
resolved. PHQ-9 score: 11 (moderate). Cognitive distortions around perfectionism and 
catastrophizing still present but patient showing insight."""
    },
    {
        "patient_id": "patient_demo_1",
        "memory_type": "medication",
        "source": "doctor",
        "raw_text": """Medication Adjustment - Week 3:
Increased sertraline to 50mg daily as planned. Patient tolerating medication well. 
No significant side effects reported. Discussed importance of continuing therapy alongside 
medication. Scheduled follow-up in 3 weeks to assess response to increased dose."""
    },
    {
        "patient_id": "patient_demo_1",
        "memory_type": "clinical",
        "source": "doctor",
        "raw_text": """Clinical Progress Note - Week 6:
Significant improvement observed. Patient appears more relaxed, maintaining eye contact, 
and spontaneously smiling during session. Reports sleeping 7 hours nightly, improved 
concentration at work, and decreased rumination. PHQ-9 score: 7 (mild). GAD-7 score: 6 
(mild). Discussed relapse prevention strategies and stress management techniques. 
Patient interested in mindfulness training."""
    },
    {
        "patient_id": "patient_demo_1",
        "memory_type": "mental_health",
        "source": "session",
        "raw_text": """Therapy Session - Week 8:
Patient demonstrating good progress with CBT techniques. Successfully challenging 
negative automatic thoughts. Implementing 'worry time' strategy effectively - limiting 
catastrophic thinking to designated 15-minute periods. Reports feeling 'like myself again 
for the first time in months'. Discussing gradual reduction of session frequency. 
Patient has re-engaged with hobbies and social activities."""
    },
]

# ============================================================================
# PATIENT 2: Medication Adjustment Case
# ============================================================================
PATIENT_2 = [
    {
        "patient_id": "patient_demo_2",
        "memory_type": "clinical",
        "source": "doctor",
        "raw_text": """New Patient Intake:
45-year-old female with history of treatment-resistant depression. Previously tried 
fluoxetine (inadequate response) and citalopram (side effects). Currently on venlafaxine 
150mg daily for 8 months with partial response. Presenting for medication review due to 
persistent fatigue, weight gain, and ongoing low mood. Hamilton Depression Rating Scale: 18."""
    },
    {
        "patient_id": "patient_demo_2",
        "memory_type": "medication",
        "source": "doctor",
        "raw_text": """Medication Review - Current Regimen:
Venlafaxine XR 150mg once daily (morning). Patient reports compliance is good but 
experiencing: fatigue (worse in early afternoon), 15lb weight gain over 8 months, 
decreased libido, and breakthrough depressive episodes. Blood pressure stable. 
Considering augmentation strategy vs medication switch."""
    },
    {
        "patient_id": "patient_demo_2",
        "memory_type": "mental_health",
        "source": "session",
        "raw_text": """Psychotherapy Session Notes:
Patient expresses frustration with 'trying so many medications'. Reports feeling 
discouraged but motivated to find the right treatment. Identifies weight gain as 
significantly impacting self-esteem and contributing to depressive symptoms. Sleep 
pattern disrupted - waking at 3-4am with difficulty returning to sleep. Discusses 
family stress as ongoing trigger."""
    },
    {
        "patient_id": "patient_demo_2",
        "memory_type": "medication",
        "source": "doctor",
        "raw_text": """Treatment Plan Update:
Adding bupropion 150mg XL daily as augmentation strategy. Selected due to: activating 
properties to address fatigue, weight-neutral profile, potential to improve concentration. 
Maintaining venlafaxine at current dose. Discussed potential side effects including 
initial insomnia and anxiety. Will reassess in 4 weeks. Contraindications reviewed - 
no seizure history, no eating disorder history."""
    },
    {
        "patient_id": "patient_demo_2",
        "memory_type": "clinical",
        "source": "doctor",
        "raw_text": """Follow-up Assessment - Week 4 Post-Augmentation:
Notable improvement in energy levels and concentration. Patient reports 'feeling more 
like myself'. No significant side effects from bupropion addition. Weight stable. 
Sleep improved with earlier wake time but no early morning awakening. Hamilton Depression 
Rating Scale: 12 (improved from 18). Plan to continue current regimen and monitor."""
    },
]

# ============================================================================
# PATIENT 3: Student Mental Health Support
# ============================================================================
PATIENT_3 = [
    {
        "patient_id": "patient_demo_3",
        "memory_type": "mental_health",
        "source": "session",
        "raw_text": """Initial Consultation - University Counseling:
21-year-old undergraduate student referred by academic advisor for anxiety related to 
academic performance. Final year of computer science degree. Reports 'crippling anxiety' 
before exams, procrastination patterns, and imposter syndrome. Has been experiencing 
panic attacks in lecture halls - heart racing, sweating, difficulty breathing. 
First panic attack 2 months ago during a presentation."""
    },
    {
        "patient_id": "patient_demo_3",
        "memory_type": "note",
        "source": "session",
        "raw_text": """Lifestyle and Context Assessment:
Student living independently for first time. Sleep schedule erratic - often coding until 
3-4am, sleeping through morning classes. Caffeine intake excessive (6+ cups daily). 
Limited physical activity. Social support network is small but present. No substance use 
concerns. Previously high-achieving student with perfectionist tendencies inherited from 
high-pressure family expectations."""
    },
    {
        "patient_id": "patient_demo_3",
        "memory_type": "mental_health",
        "source": "session",
        "raw_text": """Therapy Progress - Week 3:
Introduced grounding techniques for panic attacks - 5-4-3-2-1 sensory exercise proving 
effective. Patient practicing daily. Discussed sleep hygiene and agreed to trial 
'digital sunset' at 11pm. Exploring cognitive distortions around academic performance - 
identifying 'all-or-nothing' thinking patterns. Patient recognizes link between 
exhaustion and anxiety severity."""
    },
    {
        "patient_id": "patient_demo_3",
        "memory_type": "clinical",
        "source": "doctor",
        "raw_text": """Psychiatric Consultation:
Evaluation requested due to severity of panic symptoms. Diagnosis: Panic Disorder with 
Performance Anxiety. Considered short-term benzodiazepine PRN but opted for non-medication 
approach given student's preference and age. Discussed propranolol option for specific 
performance situations (presentations). Patient to try CBT techniques first before 
medication consideration."""
    },
    {
        "patient_id": "patient_demo_3",
        "memory_type": "mental_health",
        "source": "session",
        "raw_text": """Follow-up - Week 6:
Significant progress noted. No panic attacks in past 2 weeks. Successfully delivered 
class presentation using breathing techniques learned in therapy. Sleep schedule 
improved - averaging 11pm bedtime, 7am wake. Reduced caffeine to 2 cups daily. 
Reports feeling 'more in control' of anxiety. Grade performance improved. 
Discussing transition to monthly check-ins."""
    },
]

async def load_memory(client: httpx.AsyncClient, memory: dict) -> str:
    """Load a single memory via API."""
    try:
        response = await client.post(
            f"{API_BASE}/memory",
            json=memory,
            timeout=30.0
        )
        if response.status_code == 201:
            data = response.json()
            return f"✅ {memory['memory_type']}: {data['action']}"
        else:
            return f"❌ {memory['memory_type']}: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

async def load_patient_data(client: httpx.AsyncClient, patient_name: str, memories: list):
    """Load all memories for a patient."""
    print(f"\n📦 Loading {patient_name}...")
    for memory in memories:
        result = await load_memory(client, memory)
        print(f"   {result}")
    print(f"   ✓ {len(memories)} memories loaded for {memories[0]['patient_id']}")

async def main():
    print("=" * 60)
    print("🏥 Healthcare Memory Assistant - Demo Data Loader")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Check health
        try:
            health = await client.get(f"{API_BASE}/health")
            if health.status_code != 200:
                print("❌ API not responding. Make sure the server is running!")
                return
            print("✅ API is healthy")
        except:
            print("❌ Cannot connect to API at", API_BASE)
            print("   Run: uvicorn app.main:app --reload")
            return
        
        # Load all patients
        await load_patient_data(client, "Patient 1: Anxiety & Depression", PATIENT_1)
        await load_patient_data(client, "Patient 2: Medication Adjustment", PATIENT_2)
        await load_patient_data(client, "Patient 3: Student Mental Health", PATIENT_3)
    
    print("\n" + "=" * 60)
    print("✅ Demo data loaded successfully!")
    print("=" * 60)
    print("\n📋 Available patients for testing:")
    print("   • patient_demo_1 - Anxiety & Depression journey (6 records)")
    print("   • patient_demo_2 - Medication adjustment case (5 records)")
    print("   • patient_demo_3 - Student mental health (5 records)")
    print("\n🔍 Try these queries in the frontend:")
    print('   • "What medication was prescribed and how is it working?"')
    print('   • "Describe the patient\'s sleep patterns and improvements"')
    print('   • "What therapy techniques have been helpful?"')
    print('   • "Summarize the treatment progress"')
    print('   • "What is the patient\'s blood pressure?" (anti-hallucination test)')
    print()

if __name__ == "__main__":
    asyncio.run(main())

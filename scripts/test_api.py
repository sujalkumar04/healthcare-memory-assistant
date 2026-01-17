
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
PATIENT_ID = "patient_001"

def test_api():
    print("🚀 Starting API Smoke Test...")
    
    # 1. Health Check
    try:
        r = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health: {r.status_code} - {r.json().get('status')}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return

    # 2. Ingest Memory (Need some data for Summary/Demo to work)
    print("\n📦 Ingesting Test Memory...")
    memory_payload = {
        "patient_id": PATIENT_ID,
        "raw_text": "Patient reports severe anxiety symptoms including racing thoughts and insomnia. Prescribed Sertraline 50mg.",
        "memory_type": "mental_health",
        "source": "session",
        "visit": {
            "visit_date": "2024-01-20",
            "visit_type": "Initial Consultation",
            "clinician_role": "Psychiatrist"
        },
        "profile": {
            "full_name": "Rahul Verma",
            "department": "Mental Health"
        }
    }
    
    try:
        r = requests.post(f"{BASE_URL}/memory", json=memory_payload, timeout=10)
        if r.status_code in [200, 201]:
            print(f"✅ Ingest: {r.status_code} - {r.json().get('action')}")
        else:
            print(f"❌ Ingest Failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Ingest Exception: {e}")

    # Wait for indexing
    time.sleep(1)

    # 3. Test Summary Endpoint
    print("\n📋 Testing Summary Endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/patient/{PATIENT_ID}/summary", timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Summary: {r.status_code}")
            print(f"   Has Context: {data.get('has_context')}")
            print(f"   Summary Length: {len(data.get('summary', ''))}")
        else:
            print(f"❌ Summary Failed: {r.status_code}")
            print(f"   Response: {r.text}")
    except Exception as e:
        print(f"❌ Summary Exception: {e}")

    # 4. Test Demo (Search Context) Endpoint
    print("\n🎯 Testing Demo (Context Search) Endpoint...")
    search_payload = {
        "patient_id": PATIENT_ID,
        "query": "anxiety symptoms"
    }
    try:
        r = requests.post(f"{BASE_URL}/search/context", json=search_payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Demo Search: {r.status_code}")
            print(f"   Has Context: {data.get('has_context')}")
            print(f"   Answer: {data.get('answer_text', '')[:50]}...")
        else:
            print(f"❌ Demo Search Failed: {r.status_code}")
            print(f"   Response: {r.text}")
    except Exception as e:
        print(f"❌ Demo Search Exception: {e}")

if __name__ == "__main__":
    test_api()

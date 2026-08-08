import json
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load env variables from .env
backend_dir = Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")

from app.main import app

def run_integration_test():
    # Verify environment keys are loaded
    sarvam_key = os.getenv("SARVAM_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    breeth_key = os.getenv("BREETH_API_KEY", "")
    
    print("[INFO] Verifying API Key Configurations:")
    print(f"  SARVAM_API_KEY configured: {bool(sarvam_key)}")
    print(f"  GROQ_API_KEY configured:   {bool(groq_key)}")
    print(f"  BREETH_API_KEY configured: {bool(breeth_key)}")
    
    # Check if placeholders exist
    placeholders = ["your_sarvam", "your_groq", "your_breeth", "here"]
    for key_name, key_val in [("SARVAM_API_KEY", sarvam_key), ("GROQ_API_KEY", groq_key), ("BREETH_API_KEY", breeth_key)]:
        if not key_val or any(ph in key_val.lower() for ph in placeholders):
            print(f"\n[CRITICAL ERROR] The environment variable '{key_name}' is missing or is set to a placeholder.")
            print("Please configure valid credentials in backend/.env before running live tests.")
            raise ValueError(f"Invalid or missing API key: {key_name}")

    client = TestClient(app)

    # Load candidate from candidates.json
    with open(backend_dir / "candidates.json", "r", encoding="utf-8") as f:
        candidates_data = json.load(f)
    candidate = candidates_data["candidates"][0] # Sarah Johnson

    session_id = "live-test-session-sarah-200"
    
    print("\n" + "=" * 80)
    print("STARTING LIVE INTEGRATION TEST FOR:", candidate["member"]["name"])
    print("Session ID:", session_id)
    print("=" * 80)

    # 1. TURN 1: Initialize Session
    payload = {
        "sessionId": session_id,
        "candidate": candidate
    }
    
    print("[INFO] Sending Turn 1 Request...")
    response = client.post("/api/interview", json=payload)
    if response.status_code != 200:
        print(f"[FAIL] Turn 1 failed with status {response.status_code}: {response.text}")
        response.raise_for_status()
        
    data = response.json()
    print(f"Turn 1 Response:")
    print(f"  done : {data['done']}")
    print(f"  reply: {data['reply']}\n")
    
    assert data["done"] is False
    assert "reply" in data
    
    # 2. TURNS 2..N: Loop through answers
    step = 2
    answers = [
        "In Day 12, I learned to write system instructions and format structured outputs using Pydantic.",
        "To test and validate the prompts, we set up a local benchmark evaluation script with a fixed dataset and checked standard deviations.",
        "To scale prompt templates and model routing in production environments, we can implement a highly available, load-balanced API gateway or deploy dedicated model routers that dynamically distribute requests across multiple providers based on active token limits, throughput requirements, and network latency metrics.",
        "For Day 28, I containerized the backend FastAPI application using multi-stage Docker builds to reduce image size, and then created a highly detailed deployment manifest for Kubernetes to orchestrate the replica sets, configure resource limits, and expose the service externally using a LoadBalancer ingress controller.",
        "Scaling Docker containers on Kubernetes is handled by setting up horizontal pod autoscaling rules based on active CPU utilization and memory limits, and configuring ingress traffic rules to properly distribute incoming network loads across all active worker nodes in our cluster.",
        "Yes, on Day 29, I skipped the project due to time constraints, but I have extensive experience using Prometheus for metric collection and python logging libraries for structured logs processing to build visual panels and trigger operational alerts on anomalies.",
        "To scale our observability stack, we gather system metric data using Prometheus and route log records to Grafana Loki, which optimizes search indexing, stores data in cost-effective object storage, and easily handles terabytes of log data generated daily.",
        "For the Capstone Project, we combined a FastAPI backend, a React frontend, LangChain agent frameworks, and custom MCP servers into a unified dashboard, enabling candidates to orchestrate complex data flows with local SQLite database integrations and custom schemas.",
        "To scale our Capstone Project, we deploy each microservice container to a Kubernetes cluster, configure horizontal pod autoscalers to handle traffic spikes, and implement a distributed Redis caching layer to offload expensive database read operations under heavy user load.",
        "Text vector embeddings are generated using pretrained Sentence Transformers models to convert unstructured paragraphs into dense numeric arrays, which represent the semantic meaning of the inputs inside a high-dimensional vector space for downstream search.",
        "Scaling Sentence Transformers embeddings generation workloads can be done by using asynchronous batch processing APIs or setting up distributed compute pipelines like Apache Spark, and implementing robust caching of computed vectors to avoid running redundant neural network inference workloads."
    ]
    
    for ans in answers:
        print(f"--- Turn {step}: Candidate Response: '{ans}' ---")
        payload = {
            "sessionId": session_id,
            "message": ans
        }
        
        response = client.post("/api/interview", json=payload)
        if response.status_code != 200:
            print(f"[FAIL] Turn {step} failed with status {response.status_code}: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        print(f"Response {step}:")
        print(f"  done : {data['done']}")
        print(f"  reply: {data['reply']}\n")
        
        if data["done"]:
            print("=" * 80)
            print("LIVE INTERVIEW COMPLETED SUCCESSFULLY!")
            print("Structured Feedback:")
            print(json.dumps(data["feedback"], indent=2))
            print("=" * 80)
            break
            
        step += 1

if __name__ == "__main__":
    print("[INFO] Starting live api integration test...")
    try:
        run_integration_test()
    except Exception as e:
        print(f"\n[FATAL ERROR] Test execution failed: {e}")
        raise e

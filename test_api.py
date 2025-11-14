#!/usr/bin/env python3
"""
Test script for the QA API
"""
import httpx
import json
import sys

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    try:
        response = httpx.get(f"{API_URL}/health", timeout=5.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ask(question):
    """Test ask endpoint with a question"""
    print(f"\nTesting question: {question}")
    try:
        response = httpx.post(
            f"{API_URL}/ask",
            json={"question": question},
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            answer = response.json()["answer"]
            print(f"Answer: {answer}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run tests"""
    # Change API_URL if testing deployed version
    if len(sys.argv) > 1:
        global API_URL
        API_URL = sys.argv[1]
    
    print(f"Testing API at: {API_URL}\n")
    print("=" * 50)
    
    # Test health
    health_ok = test_health()
    
    if not health_ok:
        print("\n⚠️  Health check failed. Make sure the API is running.")
        return
    
    print("\n" + "=" * 50)
    
    # Load test queries
    try:
        with open("test_queries.json") as f:
            data = json.load(f)
            queries = data["test_queries"]
    except:
        # Fallback queries
        queries = [
            {"question": "When is Layla planning her trip to London?"},
            {"question": "How many cars does Vikram Desai have?"},
            {"question": "What are Amira's favorite restaurants?"}
        ]
    
    # Test each query
    success_count = 0
    for query in queries[:3]:  # Test first 3 queries
        if test_ask(query["question"]):
            success_count += 1
        print("-" * 50)
    
    print(f"\n✓ {success_count}/{min(3, len(queries))} tests passed")

if __name__ == "__main__":
    main()

"""
Quick test to verify synthesis_agent OpenAI integration.
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 80)
print("SYNTHESIS AGENT - OPENAI KEY CHECK")
print("=" * 80)

# Check if API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ OPENAI_API_KEY found: {api_key[:20]}...{api_key[-10:]}")
    print(f"   Length: {len(api_key)} characters")
else:
    print("❌ OPENAI_API_KEY not found in environment")
    print("   Check your .env file")
    exit(1)

# Check model
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
print(f"✅ OPENAI_MODEL: {model}")

print("\n" + "=" * 80)
print("TESTING SYNTHESIS AGENT INITIALIZATION")
print("=" * 80)

try:
    from agents.synthesis_agent import SynthesisAgent
    
    agent = SynthesisAgent()
    print(f"✅ SynthesisAgent created: {agent.name}")
    
    if agent.openai_client:
        print(f"✅ OpenAI client initialized")
        print(f"   Client type: {type(agent.openai_client)}")
    else:
        print("❌ OpenAI client is None")
        
except Exception as e:
    print(f"❌ Failed to create SynthesisAgent: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
print("TESTING MINIMAL LLM CALL")
print("=" * 80)

try:
    # Test a minimal LLM call
    response = agent.openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test successful' in JSON format."}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=50,
        timeout=10
    )
    
    print(f"✅ LLM call successful!")
    print(f"   Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ LLM call failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
print("ALL CHECKS PASSED ✅")
print("=" * 80)

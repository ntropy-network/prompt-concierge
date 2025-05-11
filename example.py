# Example task: sentiment classification

import os
from dotenv import load_dotenv

from prompt_concierge import PromptConcierge

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set")

# --- Initialize with a knowledge bank ---
knowledge_bank = {
    "overview": "Classify the sentiment (positive, neutral, negative) of e-commerce product reviews.",
    "inputs": {"review_text": "string"},
    "desired_outputs": {"label": "positive | neutral | negative"},
    "examples": [
        "I love this -> positive",
        "It broke in two days -> negative",
    ],
}
agent = PromptConcierge(api_key, knowledge_bank)

print("\n--- Initial prompt ---\n")
print(agent.generate_prompt())

agent.learn_from_user()

print("\n--- Prompt after interviewing user ---\n")
print(agent.generate_prompt())

# --- Simulated production events ---
events = [
    {  # spike in sarcastic misclassifications
        "type": "batch_metrics",
        "window": "2025-05-01T00:00:00Z/2025-05-07T23:59:59Z",
        "false_negatives": 128,
        "root_cause": "sarcastic sentences mis-labelled positive",
    },
    {  # user style preference feedback
        "user_feedback": "The explanation text feels too formal; prefer casual tone.",
    },
    {  # emoji-heavy reviews
        "text": "Model failed on emoji-heavy reviews e.g. 'Great!!!!! 😍😍😍'",
    },
]

agent.learn_from_events(events)

print("\n--- Knowledge bank after production events ---\n")
print(agent.bank.to_json())

print("\n--- Prompt after production events ---\n")
print(agent.generate_prompt())

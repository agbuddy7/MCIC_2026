#!/usr/bin/env python3
import json
import os
import random
from generator_base import BasePaymentAgent

class LegitimateGenerator(BasePaymentAgent):
    """
    Generator for legitimate baseline conversations.
    Generates conversations with surface similarities (urgency, new payees) but normal transaction intent.
    """
    def __init__(self):
        super().__init__()
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        with open(os.path.join(fixtures_dir, "legitimate_templates.json"), "r", encoding="utf-8") as f:
            self.templates = json.load(f)

    def run_mock_simulation(self, template, amount):
        """Generates a high-fidelity mock representation of a legitimate transaction."""
        tid = template["template_id"]
        
        payee_id = template.get("payee_id") or {
            "rent_payment": "landlord-rent-capital",
            "family_help": "sister-travel-direct",
            "utility_bill": "utility-clearing-node",
        }.get(tid, "utility-clearing-node")
            
        dialogue = template["dialogue_flow"]
        
        turns = [
            {
                "turn_number": 1,
                "role": "user",
                "content": dialogue[0]
            },
            {
                "turn_number": 2,
                "role": "agent",
                "content": "Sure, I can assist with that. Let me look up details or check if the payee is registered."
            },
            {
                "turn_number": 3,
                "role": "agent_tool_call",
                "content": f"[Tool Call: get_payee_details with input: {{'payee_query': '{payee_id}'}}]",
                "metadata": {"tool": "get_payee_details", "input": {"payee_query": payee_id}}
            },
            {
                "turn_number": 4,
                "role": "tool_result",
                "content": f"Query result: Payee '{payee_id}' not found in standard directories. User confirmation is required to proceed.",
                "metadata": {"tool": "get_payee_details"}
            },
            {
                "turn_number": 5,
                "role": "agent",
                "content": f"The account details {payee_id} are not currently in your known directory. Do you explicitly want to proceed with sending ${amount}?"
            },
            {
                "turn_number": 6,
                "role": "user",
                "content": dialogue[1]
            },
            {
                "turn_number": 7,
                "role": "agent_tool_call",
                "content": f"[Tool Call: transfer_funds with input: {{'payee_id': '{payee_id}', 'amount': {amount}, 'currency': 'USD', 'source_of_instruction': 'user_explicit'}}]",
                "metadata": {
                    "tool": "transfer_funds",
                    "input": {
                        "payee_id": payee_id,
                        "amount": amount,
                        "currency": "USD",
                        "source_of_instruction": "user_explicit"
                    }
                }
            }
        ]
        
        final_transfer = {
            "payee_id": payee_id,
            "amount": amount,
            "currency": "USD",
            "source_of_instruction": "user_explicit"
        }
        
        return turns, final_transfer

    def generate_single(self, index):
        """Generates one legitimate transcript."""
        template = random.choice(self.templates)
        low = float(template.get("amount_low", 25.0))
        high = float(template.get("amount_high", 350.0))
        amount = round(random.uniform(low, high), 2)
        
        # Currently, legitimate uses mock simulation as it is highly structured
        turns, transfer_info = self.run_mock_simulation(template, amount)
        
        transcript = {
            "conversation_id": f"legit-{1000 + index}",
            "attack_type": "legitimate",
            "turn_count": len(turns),
            "turns": turns,
            "final_transfer_attempted": transfer_info is not None,
            "transfer_details": {
                "payee_id": transfer_info["payee_id"] if transfer_info else None,
                "amount": transfer_info["amount"] if transfer_info else None,
                "currency": transfer_info["currency"] if transfer_info else None,
                "source_of_instruction": transfer_info["source_of_instruction"] if transfer_info else None
            },
            "ground_truth_label": "legitimate",
            "notes": f"Legitimate transaction baseline: {template['template_id']}"
        }
        return transcript

    def generate_dataset(self, count=100):
        """Generate full dataset and write to JSONL."""
        print(f"Generating {count} Legitimate baseline transcripts...")
        os.makedirs("generate/data", exist_ok=True)
        out_path = "generate/data/legitimate_conversations.jsonl"
        
        with open(out_path, "w", encoding="utf-8") as f:
            for idx in range(count):
                transcript = self.generate_single(idx)
                f.write(json.dumps(transcript) + "\n")
                if (idx + 1) % 20 == 0:
                    print(f"  Generated {idx + 1}/{count}...")
                    
        print(f"Successfully wrote dataset to {out_path}")

if __name__ == "__main__":
    generator = LegitimateGenerator()
    generator.generate_dataset(100)

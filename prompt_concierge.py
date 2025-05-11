"""
PROMPT CONCIERGE

Autonomous agent that interviews a user about the task, builds a knowledge bank,
crafts the optimal LLM prompt, and keeps that prompt up-to-date as new production
data arrives.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from openai import OpenAI

DEFAULT_MODEL = "o3" # best reasoning model we have atm
DEFAULT_TEMPERATURE = 0.5 # not used for OpenAI reasoning models

@dataclass
class KnowledgeBank:
    overview: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    desired_outputs: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    style_guidelines: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    misc: Dict[str, Any] = field(default_factory=dict)

    def _deep_merge_dicts(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(target.get(key), dict) and isinstance(value, dict):
                self._deep_merge_dicts(target[key], value)
            else:
                target[key] = value

    def update(self, **sections: Any) -> None:
        for key, value in sections.items():
            if not hasattr(self, key):
                self.misc[key] = value
                continue
            
            current_attr_value = getattr(self, key)

            if isinstance(current_attr_value, dict) and isinstance(value, dict):
                self._deep_merge_dicts(current_attr_value, value)
            elif isinstance(current_attr_value, list) and isinstance(value, list):
                current_attr_value.extend(value)
            else:
                # Don't overwrite with an empty value if current is dict, list,
                # or str and new value is empty. This can happen in the patch
                # that the LLM generates.
                if not value and any(isinstance(current_attr_value, t) for t in [dict, list, str]):
                    continue
                setattr(self, key, value)

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)

class PromptConcierge:
    def __init__(
        self,
        api_key: str,
        knowledge_bank: Optional[Dict[str, Any]] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        self.bank = KnowledgeBank()
        if knowledge_bank:
            self.bank.update(**knowledge_bank)

        self.model = model
        self.temperature = temperature

        self.llm_client = OpenAI(api_key=api_key)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        return self.llm_client.chat.completions.create(
            model=self.model,
            temperature=self.temperature if not any(x in self.model for x in ['o1', 'o3', 'o4']) else 1.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        ).choices[0].message.content.strip()

    def learn_from_user(self):
        while True:
            system = "You are a diligent analyst collecting requirements for an AI system."
            user = (
                "Current task specification JSON:\n" + self.bank.to_json() +
                "\n\nAsk one precise follow-up question to clarify requirements further. If no "
                "further clarification is needed and the task is specified "
                "unambiguously and precisely, reply with DONE."
            )
            question = self._call_llm(system, user)
            if question.upper() == "DONE":
                break
            answer = input(question + "\n> ")
            parsed_answer = self._parse_answer(question, answer)
            self.bank.update(**parsed_answer)

    def learn_from_events(self, events: List[Dict[str, Any]]):
        """
        NOTE: This will get unreasonably expensive if called on every single
        production event. Instead, cluster batches of N production events into M
        clusters at a time, where M << N, and only analyze the cluster centers.
        You can use e.g. K-medoids clustering for this with a custom distance
        metric that is cheap to compute and made specifically to the kinds of
        events and type of data you have. Use a separate clustering loop with
        its own distance function for each event type you want to use for prompt
        tuning. 
        """
        for i, ev in enumerate(events, 1):
            print(f"\n--- Processing production event #{i} ---")
            self.bank.update(**self._parse_event(ev))

    def generate_prompt(self) -> str:
        """
        NOTE: This will generate just the system prompt. The raw input for the
        task should be provided as the user prompt.
        """
        system = "You are a world-class prompt engineer."
        user = (
            "Using the task specification JSON below, craft the BEST POSSIBLE system prompt "
            "for an LLM to accomplish the task. This system prompt will be used to guide the LLM, "
            "and the raw input for the specific task instance (e.g., the text to classify, "
            "the question to answer) will be provided separately as the user prompt. "
            "Respond with ONLY the generated system prompt text - no markdown, no explanations.\n\n" +
            self.bank.to_json()
        )
        return self._call_llm(system, user)
 

    def _parse_answer(self, question: str, answer: str) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert analyst gathering requirements for a new LLM-powered feature. You analyze question / answer pairs "
            "from the user, one pair at a time.\n\n"
            "You will receive a JSON with the following keys:\n"
            "  - `task_spec` - the existing task specification.\n"
            "  - `question` - the question asked to the user.\n"
            "  - `answer` - the user's answer.\n\n"
            "You respond with the SMALLEST POSSIBLE JSON patch that captures any NEW information "
            "contained in the answer that should be merged into the task spec.\n"
            "Some example mappings:\n"
            "   - input edge-case → inputs.edge_cases\n"
            "   - recurring failure → constraints.failure_modes\n"
            "   - user tone preference → style_guidelines.user_preferences\n"
            "   - uncategorised facts → misc with a suitable descriptor as the nested key.\n\n"
            "Output requirements:\n"
            "  1. Valid JSON ONLY (no markdown).\n"
            "  2. Omit top-level keys with no changes.\n"
            "  3. Keep the entire output under 150 tokens.\n"
            "  4. If the answer does not contain any meaningful new information, "
            "return an empty JSON object."
        )
        payload = {
            "task_spec": asdict(self.bank),
            "question": question,
            "answer": answer
        }
        user_prompt = json.dumps(payload, ensure_ascii=False)
        return json.loads(self._call_llm(system_prompt, user_prompt))

    def _parse_event(self, event: Dict[str, Any]):
        system_prompt = (
            "You are an expert analyst gathering requirements for a new LLM-powered feature.\n\n"
            "You analyze production events (logs, feedback, metrics, etc.), one at a time.\n\n"
            "You will receive a JSON with the following keys:\n"
            "  - `task_spec` - the *entire* current task specification as JSON.\n"
            "  - `event` - object containing details about the newly observed production event.\n\n"
            "Your respond with the SMALLEST POSSIBLE JSON patch that captures any NEW information "
            "from the event that should be merged into the task spec.\n\n"
            "Some example mappings:\n"
            "   - input edge-case → inputs.edge_cases\n"
            "   - recurring failure → constraints.failure_modes\n"
            "   - user tone preference → style_guidelines.user_preferences\n"
            "   - high-quality example that adds new information → examples\n"
            "   - uncategorised facts → misc with a suitable descriptor as the nested key.\n\n"
            "Output requirements:\n"
            "  1. Valid JSON ONLY (no markdown).\n"
            "  2. Omit top-level keys with no changes.\n"
            "  3. Keep the entire output under 200 tokens.\n"
            "  4. If the event does not contain any meaningful new information, "
            "return an empty JSON object."
        )
        payload = {
            "task_spec": asdict(self.bank),
            "event": event
        }
        user_prompt = json.dumps(payload, ensure_ascii=False)
        return json.loads(self._call_llm(system_prompt, user_prompt))
       
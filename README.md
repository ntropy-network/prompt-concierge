# Prompt Concierge

Autonomous agent that interviews a user about a task, builds a knowledge bank, crafts an optimal LLM prompt, and keeps that prompt up-to-date as new production data arrives.

## Overview

The `PromptConcierge` is a Python tool designed to streamline the process of creating and maintaining effective prompts for Large Language Models (LLMs). It achieves this through several key functionalities:

1.  **Interactive Knowledge Gathering:** It interviews the user to understand the task requirements, constraints, desired style, and other relevant details.
2.  **Knowledge Bank:** It stores all gathered information in a structured `KnowledgeBank`. This bank can be initialized with existing knowledge and is updated dynamically.
3.  **Learning from Production Data:** It can process production events (like logs, feedback, or metrics) to refine the knowledge bank and adapt the prompt over time.
4.  **Optimal Prompt Generation:** Based on the accumulated knowledge, it generates a system prompt tailored for the LLM to perform the specified task effectively.

The core idea is to create a living prompt that evolves with new insights and data, ensuring continued high performance from the LLM.

## Key Components

### `KnowledgeBank`

The `KnowledgeBank` is a data class that holds all the information about the task. It has predefined sections for:

*   `overview`: A general description of the task.
*   `inputs`: Expected inputs for the task, including their types and any special considerations (e.g., edge cases).
*   `desired_outputs`: The format and content of the desired LLM outputs.
*   `constraints`: Any limitations, rules, or failure modes to be aware of.
*   `style_guidelines`: Preferences for the LLM's tone, style, or persona.
*   `examples`: Illustrative input/output pairs or specific scenarios.
*   `misc`: A dictionary for any other relevant information not fitting into the above categories.

The `KnowledgeBank` can be updated incrementally, and it supports deep merging of dictionaries to integrate new information without losing existing data.

### `PromptConcierge` Class

This is the main class that orchestrates the process.

*   **`__init__(self, knowledge_bank: Optional[Dict[str, Any]] = None)`**: Initializes the agent. An optional `knowledge_bank` dictionary can be provided to start with pre-existing knowledge.
*   **`learn_from_user(self)`**: Initiates an interactive session where the LLM asks clarifying questions to the user. The user's answers are parsed and used to update the `KnowledgeBank`. The session continues until the LLM determines the task is unambiguously specified.
*   **`learn_from_events(self, events: List[Dict[str, Any]])`**: Processes a list of production events. Each event is analyzed by an LLM to extract relevant information, which is then used to update the `KnowledgeBank`. This is useful for adapting the prompt to new patterns, issues, or user feedback observed in a live environment.
    *   **Note:** The script advises clustering production events for efficiency if dealing with a high volume.
*   **`generate_prompt(self) -> str`**: Uses the current state of the `KnowledgeBank` to craft a system prompt for an LLM. This prompt is designed to guide the LLM in performing the task. The actual task input (e.g., text to classify) should be provided as the user prompt when using the generated system prompt.
*   **`_parse_answer(self, question: str, answer: str) -> Dict[str, Any]`**: An internal method used by `learn_from_user` to interpret the user's response and convert it into a JSON patch for the `KnowledgeBank`.
*   **`_parse_event(self, event: Dict[str, Any])`**: An internal method used by `learn_from_events` to analyze a production event and generate a JSON patch for the `KnowledgeBank`.

## Setup

1.  **Clone or Download:** Get the `prompt_concierge.py` script.
2.  **Install Dependencies:**
    You'll need Python 3 and the following packages:
    ```bash
    pip install openai python-dotenv
    ```
3.  **Environment Variable:**
    The script uses the OpenAI API. You need to set your `OPENAI_API_KEY` as an environment variable. You can do this by creating a `.env` file in the same directory as the script with the following content:
    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    ```
    Replace `"your_openai_api_key_here"` with your actual OpenAI API key.

## Usage

The script includes an example `if __name__ == "__main__":` block that demonstrates its usage for a sentiment classification task.

To run the example:

```bash
python prompt_concierge.py
```

This will:
1.  Initialize the `PromptConcierge` with a predefined `knowledge_bank` for sentiment analysis.
2.  Print the initial system prompt generated from this knowledge.
3.  Start the `learn_from_user` interactive loop. You will be asked questions by the AI to refine the task. Type "DONE" when prompted if the AI indicates no further clarification is needed (though in the current loop, the AI asks questions until it says "DONE").
4.  Print the system prompt generated after the user interview.
5.  Simulate processing a few production events.
6.  Print the final state of the `KnowledgeBank` after these events.
7.  Print the system prompt generated after incorporating insights from the production events.

You can adapt the initial `knowledge_bank` and the `events` list in the `if __name__ == "__main__":` block to experiment with your own tasks.

## How it Works Internally

The `PromptConcierge` leverages an LLM (specified by `OPENAI_MODEL`, defaulting to "o3") for several key operations:

*   **Asking clarifying questions:** During `learn_from_user`, an LLM generates questions based on the current `KnowledgeBank` to identify ambiguities or missing information.
*   **Parsing user answers:** An LLM interprets the user's free-text answers and translates them into structured JSON patches to update the `KnowledgeBank`.
*   **Analyzing production events:** Similarly, an LLM analyzes event data and converts it into JSON patches for the `KnowledgeBank`.
*   **Generating the final prompt:** An LLM acts as a "prompt engineer" to create the optimal system prompt based on the comprehensive information in the `KnowledgeBank`.

The system prompts used for these internal LLM calls are defined within the respective methods (`_parse_answer`, `_parse_event`, `generate_prompt`, `learn_from_user`). 
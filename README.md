<p align="center">
  <picture>
    <img alt="PromptConcierge Logo" src="static/img1.png" width="70%">
  </picture>
</p>

Prompt Concierge is an autonomous agent that interviews a user about a task, builds a knowledge bank, crafts an optimal LLM prompt, and keeps that prompt up-to-date as new production data arrives.

## Overview

The `PromptConcierge` is a Python tool designed to streamline the process of creating and maintaining effective prompts for Large Language Models (LLMs). It achieves this through several key functionalities:

1.  **Interactive Knowledge Gathering:** It interviews the user to understand the task requirements, constraints, desired style, and other relevant details.
2.  **Knowledge Bank:** It stores all gathered information in a structured knowledge bank. This bank can be initialized with existing knowledge and is updated dynamically.
3.  **Learning from Production Data:** It can process production events (like logs, feedback, or metrics) to refine the knowledge bank and adapt the prompt over time.
4.  **Optimal Prompt Generation:** Based on the accumulated knowledge, it generates a system prompt tailored for the LLM to perform the specified task effectively.

The core idea is to create a living prompt that evolves with new insights and data, ensuring continued high performance from the LLM.

## Key Components

### `KnowledgeBank`

The knowledge bank is a data class that holds all the information about the task. It can be updated incrementally to integrate new information without losing existing data. It has predefined sections for:

*   `overview`: A general description of the task.
*   `inputs`: Expected inputs for the task, including their types and any special considerations (e.g., edge cases).
*   `desired_outputs`: The format and content of the desired LLM outputs.
*   `constraints`: Any limitations, rules, or failure modes to be aware of.
*   `style_guidelines`: Preferences for the LLM's tone, style, or persona.
*   `examples`: Illustrative input/output pairs or specific scenarios.
*   `misc`: A dictionary for any other relevant information not fitting into the above categories.

### `PromptConcierge`

This is the main class that orchestrates the process.

*   **`learn_from_user`**: Initiates an interactive session where the LLM asks clarifying questions to the user. The user's answers are parsed and used to update the knowledge bank. The session continues until the LLM determines the task is unambiguously specified.
*   **`learn_from_events`**: Processes a list of production events. Each event is analyzed by an LLM to extract relevant information, which is then used to update the knowledge bank. This is useful for adapting the prompt to new patterns, issues, or user feedback observed in a live environment. Try to maximize the amount of information that can be extracted from each even here. i.e. processing duplicate or very similar events will result in lots of wasted tokens.
*   **`generate_prompt`**: Uses the current state of the knowledge bank to craft an optimal system prompt for an LLM. The actual task input should be provided as a raw string in the user prompt.

## Setup

1.  **Clone the repo**
2.  **Install dependencies:**
    You'll need Python 3 and the OpenAI Python SDK:
    ```bash
    pip install openai
    ```

## Usage

The repo includes an example sentiment classification task. To run the example, set your `OPENAI_API_KEY` as an environment variable. You can do this by creating a `.env` file in the same directory as the script with the following content:
```
OPENAI_API_KEY="your_openai_api_key_here"
```
Replace `"your_openai_api_key_here"` with your actual OpenAI API key.

Then:

```bash
pip install python-dotenv
python example.py
```

This will:
1.  Initialize the `PromptConcierge` with a predefined knowledge bank for a sentiment analysis task.
3.  You will then be asked interactive questions to refine the task. 
5.  Process a few production events to further refine the prompt.

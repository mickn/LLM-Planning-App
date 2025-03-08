## Overview

This plan outlines a Python command-line application for planning and documenting tasks with large language models (LLMs). The app:

- Operates via the terminal (command-line interface).
- Supports OpenAI’s Python API by default (optionally configurable for Amazon Bedrock/Anthropic or Azure OpenAI).
- Provides two main commands: `init` and `plan`.
- Maintains a “Memory Bank” of Markdown files that provide persistent context.
- Integrates user-provided `.txt` instructions with relevant “Memory Bank” context to produce a final plan.
- Can prompt the user for clarification before finalizing the plan.
- Produces whimsical yet instructive user prompts and output.

---

## Core functionalities

1. **Initialization (`init` command)**
   - Scans the current folder. If the folder doesn’t contain a `memory-bank` directory with the required files, it creates the following files inside `memory-bank/`:
     - `projectbrief.md`
     - `productContext.md`
     - `activeContext.md`
     - `systemPatterns.md`
     - `techContext.md`
     - `progress.md`
   - Explains (in a friendly, whimsical style) the purpose of each file.
   - Prints a success message once the files have been created.

2. **Plan mode (`plan` command)**
   - Takes a path to a `.txt` file that already has a brief description of the feature or task.
   - Reads all files in `memory-bank/` as context.
   - Optionally asks clarifying questions in the terminal if more information is needed.
   - Updates that `.txt` file with a thorough plan that includes:
     - The steps required to implement the feature.
     - Any relevant details discovered from the memory bank.
   - Instructs the future “executor” (the junior developer running the plan) to:
     - Check off items in the `.txt` file as they’re completed.
     - Keep the memory bank updated with any new patterns, changes, or ideas discovered during execution.

3. **LLM connectivity**
   - Default is OpenAI’s GPT (“openai-01”) using the official Python API.
   - Should allow easy toggling to Amazon Bedrock/Anthropic or Azure OpenAI if credentials and configurations are provided.
   - Developer can set environment variables like `OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, or `AZURE_OPENAI_KEY` to switch between providers.
   - If any credentials are missing, the app should print a friendly message explaining how to set them and gracefully exit.

4. **Whimsical user experience**
   - When printing to the terminal, use playful language like:
     ```
     "Ahoy, adventurer! The memory bank is secure and ready. Would you like to proceed?"
     ```
   - Provide ASCII art or small emojis to keep the terminal output fun.

5. **Memory Bank updates**
   - Every time the app outputs a plan or modifies the `.txt` instructions, it reminds the user to maintain the memory bank (`projectbrief.md`, `productContext.md`, etc.) with any new key insights.
   - Encourages the user to store new patterns in `.clinerules` if relevant (mirroring the example prompt’s approach).

---

## Implementation details

Below is a high-level file structure and example code. Adjust directories to fit your preferences.

```
my_llm_planner/
│
├── memory-bank/
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── activeContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── progress.md
│
├── llm_planner.py
├── requirements.txt
└── README.md
```

### `llm_planner.py` (suggested skeleton)

```python
#!/usr/bin/env python3

import os
import sys
import openai

# Optional: imports for other LLM providers (placeholders)
# import boto3  # For Amazon Bedrock (Anthropic)
# import azure.ai.openai as azure_openai  # For Azure


def main():
    if len(sys.argv) < 2:
        print("Usage: llm_planner.py [init|plan] [arguments]")
        sys.exit(1)

    command = sys.argv[1].lower()

    # Detect API environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    # Add placeholders for AWS and Azure credentials if needed

    if not openai_api_key:
        # Could check if user wants to use AWS or Azure instead
        # but let's default to OpenAI for now
        print("\nOops, no OpenAI API key detected.\n"
              "Please set it via 'export OPENAI_API_KEY=<your_key>'.\n"
              "Alternatively, configure AWS or Azure credentials.\n"
              "Exiting now. Goodbye!\n")
        sys.exit(1)
    else:
        openai.api_key = openai_api_key

    if command == "init":
        init_memory_bank()
    elif command == "plan":
        if len(sys.argv) < 3:
            print("Usage: llm_planner.py plan <path_to_txt>")
            sys.exit(1)
        text_file_path = sys.argv[2]
        plan_feature(text_file_path)
    else:
        print(f"Unrecognized command '{command}'. Valid commands are 'init' or 'plan'.")


def init_memory_bank():
    print("\n(っ◕‿◕)っ Welcome to the LLM Planner Initialization!")
    memory_dir = "memory-bank"

    # Create memory-bank folder if not exists
    if not os.path.exists(memory_dir):
        os.mkdir(memory_dir)
        print(f"Beep boop. Created '{memory_dir}' directory!\n")

    # List of required files
    required_files = [
        "projectbrief.md",
        "productContext.md",
        "activeContext.md",
        "systemPatterns.md",
        "techContext.md",
        "progress.md"
    ]

    for fname in required_files:
        file_path = os.path.join(memory_dir, fname)
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {fname}\n\n")  # Basic title
            print(f" • Created '{fname}'")
        else:
            print(f" • '{fname}' already exists, skipping.")

    print("\nヽ(•‿•)ノ All set! Your memory bank is ready.")


def plan_feature(text_file_path):
    print("\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Entering plan mode...")
    print("Gathering the memory bank for context...\n")

    memory_dir = "memory-bank"
    if not os.path.exists(memory_dir):
        print("Oops! No memory-bank found. Please run 'llm_planner.py init' first.")
        sys.exit(1)

    # Read all markdown files in memory-bank
    memory_contents = []
    for fname in os.listdir(memory_dir):
        if fname.endswith(".md"):
            with open(os.path.join(memory_dir, fname), 'r', encoding='utf-8') as f:
                memory_contents.append(f.read())

    combined_memory = "\n\n".join(memory_contents)

    # Read the user-provided instructions from text_file_path
    if not os.path.exists(text_file_path):
        print(f"Error: File '{text_file_path}' not found.")
        sys.exit(1)

    with open(text_file_path, 'r', encoding='utf-8') as tf:
        user_instructions = tf.read()

    # Potentially ask clarifying questions here (simple example)
    # In a real scenario, you might do an interactive prompt or a chain-of-thought approach
    # We'll keep it minimal for the junior developer's sake:
    clarification_needed = False
    if "TBD" in user_instructions:
        print("It looks like there's a 'TBD' in your instructions. "
              "Please clarify in your .txt or remove the TBD placeholder.")
        clarification_needed = True

    if clarification_needed:
        print("Cannot proceed until clarifications are made. Exiting plan mode.")
        sys.exit(0)

    # Call the LLM with all the context
    # (If using openai, we do something like below; otherwise, replace with bedrock/azure logic)
    llm_prompt = f"""
You are a helpful planning assistant.
Here is the combined memory bank context:
{combined_memory}

The user wants to build or refine the following feature (from a .txt file):
{user_instructions}

1) If you need clarification, ask in plain text.
2) Otherwise, produce a comprehensive plan with step-by-step tasks.
3) Remind the executor to check off tasks as they go and update the memory bank with changes.
    """

    # Example call (using GPT-3.5 or GPT-4, whichever is "openai-01" to you)
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=llm_prompt,
        max_tokens=500,
        temperature=0.7
    )
    plan_text = response.choices[0].text.strip()

    # Append the plan to the user_instructions or replace it — up to your design
    final_plan = user_instructions + "\n\n" + "LLM-Generated Plan:\n" + plan_text

    with open(text_file_path, 'w', encoding='utf-8') as tf:
        tf.write(final_plan)

    print("\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Your plan is ready!")
    print("Please open the TXT file, review the plan, and update items as you complete them.")
    print("Don’t forget to record any important patterns in your memory bank!\n")


if __name__ == "__main__":
    main()
```

#### Notes on supporting Amazon Bedrock or Azure

- To support Amazon Bedrock with Anthropic, you would likely replace the `openai.Completion.create(...)` block with AWS SDK calls, or wrap them in conditional logic based on environment variables.
- For Azure, you’d configure `openai.api_base` with the Azure endpoint and supply `openai.api_key` with your Azure Key credential.

---

## Example usage

1. **Initialize memory bank**
   ```bash
   $ python3 llm_planner.py init
   (っ◕‿◕)っ Welcome to the LLM Planner Initialization!
   ...
   (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Your memory bank is ready!
   ```
2. **Create your instructions**
   - Make a file `feature_request.txt` with some initial text describing what you want to build.
   ```bash
   $ cat feature_request.txt
   We need a new user login system. Key tasks:
   - Implement OAuth
   - Create a user profile page
   - TBD: design some flow
   ```
3. **Plan**
   ```bash
   $ python3 llm_planner.py plan feature_request.txt
   (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Entering plan mode...
   Gathering the memory bank for context...

   It looks like there's a 'TBD' in your instructions. Please clarify in your .txt...
   Cannot proceed until clarifications are made. Exiting plan mode.
   ```
   - Remove the `TBD` or clarify it, then re-run:
   ```bash
   $ python3 llm_planner.py plan feature_request.txt
   (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Entering plan mode...
   Gathering the memory bank for context...

   (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Your plan is ready!
   ...
   ```
4. **Check updated `feature_request.txt`**
   - It now includes a brand-new “LLM-Generated Plan” section with details from the model.

---

## Testing

1. **Unit tests**
   - Validate that `init_memory_bank()` creates the correct files.
   - Ensure `plan_feature()` handles missing `.txt` gracefully.
   - Mock the LLM response to verify the final `.txt` is updated with the expected text.

2. **Integration tests**
   - Prepare a memory-bank with sample contents; run `plan` and confirm the final `.txt` includes references to the memory bank data.
   - Check environment variable toggling to ensure the app does not crash with no keys or partial keys.

3. **User acceptance tests**
   - Manually use `init` to confirm the creation of memory bank files.
   - Manually run `plan` with a realistic `.txt` file to see if the output matches your expectations and is whimsical enough.

---

## Potential errors and how to fix them

1. **Missing `OPENAI_API_KEY`**
   - Symptom: The app prints:
     ```
     Oops, no OpenAI API key detected...
     ```
   - Fix:
     ```
     export OPENAI_API_KEY=sk-...
     ```
   - Alternatively, set AWS or Azure environment variables if you’re switching providers.

2. **No `memory-bank/` directory**
   - Symptom: `plan` stops and says you need to run `init` first.
   - Fix: run `llm_planner.py init`.

3. **File or directory permission issues**
   - Symptom: The app fails to create or read files due to permissions.
   - Fix: Check your operating system’s read/write permissions, or run with the correct user privileges.

4. **Unrecognized command**
   - Symptom: `Unrecognized command 'foo'. Valid commands are 'init' or 'plan'.`
   - Fix: Use the correct command name.

5. **TBD placeholders in `.txt`**
   - Symptom: The app sees “TBD” and aborts the plan.
   - Fix: Remove “TBD” or replace with more concrete requirements.

---

## Conclusion

This `.TXT` plan should guide a junior developer through building a Python-based LLM planning app. The whimsical interface, thorough memory bank structure, and support for multiple LLM providers help ensure a fun yet robust experience. The key points are:

- Implement `init` to create and maintain the memory bank.
- Implement `plan` to merge user instructions with the memory bank and produce a step-by-step solution.
- Keep the terminal output lighthearted and fun.
- Always prompt for clarifications when encountering ambiguities.
- Remind the “executor” to update the memory bank and `.txt` files with progress and newly discovered patterns.

Happy coding!
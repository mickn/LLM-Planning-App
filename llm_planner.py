#!/usr/bin/env python3

import os
import sys
import argparse
import json
import subprocess
import re
from pathlib import Path
from dotenv import load_dotenv  # Add this import

# Optional: imports for other LLM providers (placeholders)
# import boto3  # For Amazon Bedrock (Anthropic)
# import azure.ai.openai as azure_openai  # For Azure


def main():
    # Load environment variables from .env file
    load_dotenv(override=True)  # Add override=True to ensure .env is always loaded

    # Keep track of the current directory (don't change directories)
    current_dir = os.getcwd()

    parser = argparse.ArgumentParser(description="LLM Planner: A tool for planning and documenting tasks with LLMs")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize the memory bank with LLM-generated content")

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Generate a plan from a txt file")
    plan_parser.add_argument("text_file", help="Path to the txt file with task description")

    # Add clarify option to plan command
    plan_parser.add_argument("--clarify", action="store_true", help="Enable interactive clarification questions")

    # Add update command
    update_parser = subparsers.add_parser("update", help="Update memory bank files with new insights")
    update_parser.add_argument("file", help="Memory bank file to update", choices=[
        "projectbrief", "productContext", "activeContext",
        "systemPatterns", "techContext", "progress"])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Detect API environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    azure_openai_key = os.getenv("AZURE_OPENAI_KEY", "")

    # Default to OpenAI
    provider = "openai"

    # Check for credentials
    if openai_api_key:
        # OpenAI API key is set - we'll use it in the function call
        provider = "openai"
    elif aws_access_key_id and aws_secret_access_key:
        provider = "aws"
        # AWS credentials are already set via environment variables
    elif azure_openai_key:
        provider = "azure"
        # Azure credentials are already set via environment variables
    else:
        print("\n🔑 Oops, no API credentials detected!\n"
              "Please set one of the following:\n"
              "  - OpenAI: export OPENAI_API_KEY=<your_key>\n"
              "  - AWS: export AWS_ACCESS_KEY_ID=<your_id> and AWS_SECRET_ACCESS_KEY=<your_key>\n"
              "  - Azure: export AZURE_OPENAI_KEY=<your_key>\n"
              "Exiting now. Goodbye! 👋\n")
        sys.exit(1)

    if args.command == "init":
        init_memory_bank(provider)
    elif args.command == "plan":
        plan_feature(args.text_file, provider, clarify=args.clarify)
    elif args.command == "update":
        update_memory_file(args.file, provider)


def init_memory_bank(provider="openai"):
    """
    Initialize the memory bank by calling the LLM once. The model is free to create
    any .md file(s) it wishes, as long as they go into the memory-bank folder. We
    parse the returned JSON and create the corresponding files.
    """
    print("\n(っ◕‿◕)っ Welcome to the LLM Planner Initialization!")
    print("🧙‍♂️ The LLM wizard is ready to build the memory bank in a single creative pass...")

    # Use current working directory for memory-bank
    current_dir = os.getcwd()
    memory_dir = os.path.join(current_dir, "memory-bank")

    # Create memory-bank folder if not exists
    if not os.path.exists(memory_dir):
        os.mkdir(memory_dir)
        print(f"🎉 Created '{memory_dir}' directory!\n")

    # Gather some basic project info to give context to the LLM
    project_info = analyze_project_structure()

    # (Optional) codebase analysis for context
    code_analysis = analyze_codebase_hierarchically(provider)

    # This is the custom prompt introducing the "Memory Bank" concept.
    # We pass everything in at once, then let the LLM propose any .md files it wants.
    llm_prompt = f"""
You are tasked with generating a set of markdown files for a project's memory bank.
Please respond with valid JSON in the following format (example):

{{
  "files": [
    {{
      "filename": "someFile.md",
      "content": "## Example\\nHere is some content..."
    }},
    {{
      "filename": "anotherFile.md",
      "content": "...more content..."
    }}
  ]
}}

Only include .md files in your "files" array. Each "filename" must go into the memory-bank folder,
and each "content" must be valid markdown.

Use the context below. Summarize or reference it as you see fit.
You may create or omit any memory-bank files you believe are helpful.

---- project info ----
{project_info}

---- code analysis ----
{code_analysis}

---- specification for the memory bank (variation of the prompt) ----

# Memory Bank

I am an expert software engineer with a unique characteristic: my memory resets completely
between sessions. This isn't a limitation - it's what drives me to maintain perfect documentation.
After each reset, I rely ENTIRELY on my memory bank to understand the project and continue work effectively.
I MUST read ALL memory bank files at the start of EVERY task - this is not optional.

## memory bank structure

The Memory Bank consists of required core files and optional context files, all in Markdown format.
Files build upon each other in a clear hierarchy:

```mermaid
flowchart TD
    PB[projectbrief.md] --> PC[productContext.md]
    PB --> SP[systemPatterns.md]
    PB --> TC[techContext.md]

    PC --> AC[activeContext.md]
    SP --> AC
    TC --> AC

    AC --> P[progress.md]
```

### core files (required)
1. `projectbrief.md`
   - Foundation document that shapes all other files
   - Created at project start if it doesn't exist
   - Defines core requirements and goals
   - Source of truth for project scope

2. `productContext.md`
   - Why this project exists
   - Problems it solves
   - How it should work
   - User experience goals

3. `activeContext.md`
   - Current work focus
   - Recent changes
   - Next steps
   - Active decisions and considerations

4. `systemPatterns.md`
   - System architecture
   - Key technical decisions
   - Design patterns in use
   - Component relationships

5. `techContext.md`
   - Technologies used
   - Development setup
   - Technical constraints
   - Dependencies

6. `progress.md`
   - What works
   - What's left to build
   - Current status
   - Known issues

### additional context
Create additional files/folders within memory-bank/ when they help organize:
- Complex feature documentation
- Integration specifications
- API documentation
- Testing strategies
- Deployment procedures

## core workflows

### plan mode
```mermaid
flowchart TD
    Start[Start] --> ReadFiles[Read Memory Bank]
    ReadFiles --> CheckFiles[Files Complete?]

    CheckFiles -->|No| Plan[Create Plan]
    Plan --> Document[Document in Chat]

    CheckFiles -->|Yes| Verify[Verify Context]
    Verify --> Strategy[Develop Strategy]
    Strategy --> Present[Present Approach]
```

## documentation updates

Memory Bank updates occur when:
1. Discovering new project patterns
2. After implementing significant changes
3. When user requests with **update memory bank** (MUST review ALL files)
4. When context needs clarification

```mermaid
flowchart TD
    Start[Update Process]

    subgraph Process
        P1[Review ALL Files]
        P2[Document Current State]
        P3[Clarify Next Steps]
        P4[Update all memory bank files]

        P1 --> P2 --> P3 --> P4
    end

    Start --> Process
```

Note: When triggered by **update memory bank**, I MUST review every memory bank file,
even if some don't require updates. Focus particularly on activeContext.md and progress.md
as they track current state.

Remember: after every memory reset, I begin completely fresh. The Memory Bank is my only link
to previous work. It must be maintained with precision and clarity, as my effectiveness
depends entirely on its accuracy.
"""

    print("📚 Making a single LLM call to propose memory bank files...")

    # Call the LLM; we expect valid JSON in its response
    response = call_llm(
        llm_prompt,
        "",
        provider,
        system_prompt=(
            "You are a software architect who generates memory-bank documentation in JSON. "
            "Output MUST be valid JSON with a 'files' array. Each array item has 'filename' and 'content'."
        ),
        model_type="thinking"
    )

    # Attempt to parse JSON
    try:
        parsed = json.loads(response)
        files_list = parsed.get("files", [])
    except json.JSONDecodeError as e:
        print("\n❌ Error: The LLM did not return valid JSON. Here is the raw output:\n")
        print(response)
        print("\nPlease re-run 'init' once the prompt is adjusted. Exiting.\n")
        sys.exit(1)

    if not isinstance(files_list, list) or not files_list:
        print("\n⚠️ No files were provided in the JSON. Here is the raw output:\n")
        print(response)
        sys.exit(1)

    # Create each file in memory-bank
    for item in files_list:
        filename = item.get("filename", "").strip()
        content = item.get("content", "")

        if not filename.endswith(".md"):
            print(f"Skipping file '{filename}' because it doesn't end with '.md'.")
            continue

        # Ensure filename doesn't include any directory paths
        clean_filename = os.path.basename(filename)
        file_path = os.path.join(memory_dir, clean_filename)

        if os.path.exists(file_path):
            print(f"📄 '{clean_filename}' already exists, skipping.")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✨ Created '{clean_filename}' in memory-bank/")

    print("\nヽ(•‿•)ノ All set! Your LLM-powered memory bank is ready.")
    print("📝 Review and edit the files to make them more accurate if needed.")
    print("🔍 Use 'llm_planner.py plan <your_feature_file.txt>' to generate plans.")
    print("🔄 Use 'llm_planner.py update <file>' to update a specific memory bank file.")


def analyze_project_structure():
    """Analyze the project structure to provide context for LLM."""
    print("🕵️‍♀️ Analyzing project structure...")

    project_info = {
        "project_name": os.path.basename(os.getcwd()),
        "directories": [],
        "files": [],
        "file_types": {},
        "potential_languages": set(),
        "potential_frameworks": set(),
        "readme_content": "",
    }

    # Language and framework detection patterns
    language_patterns = {
        "python": [".py", "requirements.txt", "setup.py", "Pipfile"],
        "javascript": [".js", "package.json", ".jsx", ".ts", ".tsx"],
        "java": [".java", "pom.xml", "build.gradle"],
        "ruby": [".rb", "Gemfile"],
        "go": [".go", "go.mod"],
        "rust": [".rs", "Cargo.toml"],
        "php": [".php", "composer.json"],
        "c#": [".cs", ".csproj", ".sln"],
    }

    framework_patterns = {
        "django": ["settings.py", "urls.py", "wsgi.py", "asgi.py"],
        "flask": ["app.py", "flask", "templates/"],
        "react": ["react", "jsx", "tsx", "components/"],
        "vue": ["vue", "components/"],
        "angular": ["angular", "component.ts"],
        "spring": ["Application.java", "SpringApplication"],
        "rails": ["config/routes.rb"],
        "express": ["express", "routes/"],
        "laravel": ["artisan"],
    }

    # Walk through the directory structure - use absolute path
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir, topdown=True):
        # Skip hidden directories and memory-bank
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != "memory-bank" and d != "node_modules" and d != "venv" and d != ".git"]

        if root == current_dir:
            project_info["directories"] = dirs

        for file in files:
            if file.startswith('.'):
                continue

            file_path = os.path.join(root, file)
            if root == current_dir:
                project_info["files"].append(file)

            # Track file extensions
            ext = os.path.splitext(file)[1]
            if ext:
                project_info["file_types"][ext] = project_info["file_types"].get(ext, 0) + 1

            # Detect languages
            for lang, patterns in language_patterns.items():
                if any(pattern in file_path if pattern.startswith(".") else pattern == file for pattern in patterns):
                    project_info["potential_languages"].add(lang)

            # Detect frameworks
            for framework, patterns in framework_patterns.items():
                if any(pattern in file_path for pattern in patterns):
                    project_info["potential_frameworks"].add(framework)

            # Extract README content if it exists
            if file.lower() == "readme.md" and root == current_dir:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        project_info["readme_content"] = f.read()
                except Exception as e:
                    print(f"Error reading README: {e}")
                    pass

    # Convert sets to lists for JSON serialization
    project_info["potential_languages"] = list(project_info["potential_languages"])
    project_info["potential_frameworks"] = list(project_info["potential_frameworks"])

    return project_info


def analyze_codebase_hierarchically(provider="openai"):
    """Analyze the codebase using a hierarchical approach to generate comprehensive summaries."""
    print("🔍 Starting hierarchical code analysis...")
    # Use current working directory
    current_dir = os.getcwd()
    print(f"Working directory: {current_dir}")

    # Dictionary to store file, directory, and module level summaries
    code_analysis = {
        "file_summaries": {},
        "directory_summaries": {},
        "project_summary": "",
        "patterns": [],
        "technologies": set()
    }

    # Step 1: Find all relevant code files
    code_extensions = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'React',
        '.ts': 'TypeScript',
        '.tsx': 'React TypeScript',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.rs': 'Rust',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.json': 'JSON',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.md': 'Markdown',
        '.xml': 'XML',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bat': 'Batch',
        '.ps1': 'PowerShell'
    }

    max_files_to_analyze = 50  # Set a reasonable limit to avoid too many API calls
    max_content_length = 6000  # Max character length for code chunks to send to LLM
    max_token_estimate = 150000  # Estimated maximum tokens for a single LLM call

    # Find all code files - use absolute path
    all_code_files = []
    for root, dirs, files in os.walk(current_dir):
        # Skip hidden directories, node_modules, and memory-bank
        if (any(part.startswith('.') for part in root.split(os.sep)) or
            'node_modules' in root or 'memory-bank' in root or
            '__pycache__' in root or 'venv' in root or '.git' in root):
            continue

        for file in files:
            if file.startswith('.'):
                continue

            ext = os.path.splitext(file)[1].lower()
            if ext in code_extensions:
                file_path = os.path.join(root, file)
                all_code_files.append(file_path)

    # Sort files by modification time (newer files first) and limit the number
    all_code_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    all_code_files = all_code_files[:max_files_to_analyze]

    # Group files by directory
    files_by_directory = {}
    for file_path in all_code_files:
        dir_path = os.path.dirname(file_path)
        if dir_path not in files_by_directory:
            files_by_directory[dir_path] = []
        files_by_directory[dir_path].append(file_path)

    # Check if the entire codebase can fit in one go (simple character-based estimate)
    total_code_size = 0
    code_contents = {}

    # Get the size of all code files
    for file_path in all_code_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                code_contents[file_path] = content
                total_code_size += len(content)
        except Exception:
            # Skip files we can't read
            continue

    # Rough tokens estimation (assuming avg 4 chars per token)
    estimated_tokens = total_code_size / 4

    # If the codebase is small enough, analyze it all at once
    if estimated_tokens < max_token_estimate and len(all_code_files) <= 15:
        print(f"📚 Small codebase detected ({len(all_code_files)} files, ~{int(estimated_tokens)} tokens)")
        print("🧠 Analyzing entire codebase at once...")

        # Prepare the entire codebase as a single prompt
        codebase_content = []

        for file_path, content in code_contents.items():
            if not content.strip():
                continue

            ext = os.path.splitext(file_path)[1].lower()
            language = code_extensions.get(ext, "Unknown")
            code_analysis["technologies"].add(language)

            codebase_content.append(f"FILE: {file_path} ({language})\n```{language.lower()}\n{content}\n```\n")

        # Analyze the entire codebase at once
        full_codebase_prompt = f"""
You are analyzing an entire codebase consisting of {len(codebase_content)} files.
Here are all the files:

{' '.join(codebase_content)}

Analyze this codebase and provide:
1. An overview of the project architecture and organization
2. The purpose and functionality of each file
3. Key classes, functions, and components across the codebase
4. How components interact and data flows
5. Design patterns, coding conventions, and recurring practices
6. Technologies, frameworks, and libraries used

Organize your response in these sections:
- PROJECT SUMMARY: Overall project description and architecture
- FILE SUMMARIES: Brief description of each file's purpose and key components
- DIRECTORY ORGANIZATION: How files are organized into functional units
- PATTERNS AND CONVENTIONS: Recurring coding patterns and conventions
- TECHNOLOGIES IDENTIFIED: Languages, libraries, and frameworks used

Be comprehensive yet concise in your analysis.
"""

        print("🔮 Generating comprehensive codebase analysis...")
        codebase_analysis = call_llm(full_codebase_prompt, "", provider,
                                   system_prompt="You are a software architect analyzing an entire codebase.",
                                   model_type="thinking")

        # Parse the response to extract the different sections
        sections = {}
        current_section = None
        section_content = []

        for line in codebase_analysis.split('\n'):
            if line.startswith('# ') or line.startswith('## '):
                # Save the previous section if it exists
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                    section_content = []

                # Start a new section
                current_section = line.lstrip('#').strip()
            elif current_section:
                section_content.append(line)

        # Add the last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)

        # Map the sections to our code_analysis structure
        if 'PROJECT SUMMARY' in sections:
            code_analysis["project_summary"] = sections['PROJECT SUMMARY']

        if 'FILE SUMMARIES' in sections:
            # Parse file summaries - this is a rough approach, might need refinement
            file_summaries_text = sections['FILE SUMMARIES']

            for file_path in code_contents.keys():
                filename = os.path.basename(file_path)
                if filename in file_summaries_text:
                    idx = file_summaries_text.find(filename)
                    start = max(0, idx - 10)
                    end = min(len(file_summaries_text), idx + 500)
                    summary_chunk = file_summaries_text[start:end]

                    next_file_idx = float('inf')
                    for other_file in code_contents.keys():
                        other_filename = os.path.basename(other_file)
                        if other_filename != filename and other_filename in summary_chunk:
                            idx = summary_chunk.find(other_filename)
                            if idx > 0:
                                next_file_idx = min(next_file_idx, idx)

                    if next_file_idx < float('inf'):
                        file_summary = summary_chunk[:next_file_idx].strip()
                    else:
                        file_summary = summary_chunk.strip()

                    code_analysis["file_summaries"][file_path] = file_summary

        if 'DIRECTORY ORGANIZATION' in sections:
            dir_org = sections['DIRECTORY ORGANIZATION']
            for dir_path in files_by_directory.keys():
                if dir_path in dir_org:
                    idx = dir_org.find(dir_path)
                    start = max(0, idx - 10)
                    end = min(len(dir_org), idx + 500)
                    dir_summary = dir_org[start:end].strip()
                    code_analysis["directory_summaries"][dir_path] = dir_summary

        if 'PATTERNS AND CONVENTIONS' in sections:
            code_analysis["patterns"] = sections['PATTERNS AND CONVENTIONS']

        code_analysis["technologies"] = list(code_analysis["technologies"])
        if 'TECHNOLOGIES IDENTIFIED' in sections:
            tech_section = sections['TECHNOLOGIES IDENTIFIED']
            for lang in code_extensions.values():
                if lang.lower() in tech_section.lower() and lang not in code_analysis["technologies"]:
                    code_analysis["technologies"].append(lang)

    else:
        # For larger codebases, use the hierarchical approach
        print(f"📚 Large codebase detected ({len(all_code_files)} files, ~{int(estimated_tokens)} tokens)")
        print(f"📄 Using hierarchical analysis approach...")

        print(f"📄 Analyzing {len(all_code_files)} code files...")
        large_files = []
        small_files = []
        chars_per_token = 4
        batch_token_limit = 8000

        for file_path in all_code_files:
            content = code_contents.get(file_path, "")
            if not content:
                continue
            if len(content) > max_content_length:
                large_files.append(file_path)
            else:
                small_files.append(file_path)

        print(f"🔍 Processing {len(large_files)} large files individually...")
        for i, file_path in enumerate(large_files):
            try:
                content = code_contents.get(file_path, "")
                ext = os.path.splitext(file_path)[1].lower()
                language = code_extensions.get(ext, "Unknown")
                print(f"\r💭 Processing large file {i+1}/{len(large_files)}: {file_path} (chunking...)", end="")

                lines = content.split('\n')
                chunks = []
                current_chunk = []
                current_chunk_size = 0

                for line in lines:
                    current_chunk.append(line)
                    current_chunk_size += len(line) + 1

                    if current_chunk_size >= max_content_length:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                        current_chunk_size = 0

                if current_chunk:
                    chunks.append('\n'.join(current_chunk))

                chunk_summaries = []
                for j, chunk in enumerate(chunks):
                    chunk_prompt = f"""
This is chunk {j+1} of {len(chunks)} from file '{file_path}' in a {language} codebase.

Code chunk:
```{language.lower()}
{chunk}
```

Provide a brief analysis of this code chunk. Identify:
1. Classes and their responsibilities
2. Functions/methods and what they do
3. Key logic/algorithms
4. Important variables/data structures
5. Any imports/dependencies

Be concise but comprehensive.
"""
                    chunk_summary = call_llm(chunk_prompt, "", provider,
                                          system_prompt="You are a code analyst providing concise summaries of code files.",
                                          model_type="fast")
                    chunk_summaries.append(chunk_summary)

                combined_prompt = f"""
I have a {language} file '{file_path}' that was analyzed in {len(chunks)} chunks.
Here are the summaries of each chunk:

{' '.join(f"Chunk {j+1}:\n{summary}\n" for j, summary in enumerate(chunk_summaries))}

Please provide a unified summary of this file that explains:
1. The overall purpose and functionality of this file
2. Key classes, functions, and components
3. How these components interact
4. The file's role in the larger project (if apparent)
5. Any notable patterns, technologies, or techniques used

Keep the summary focused and informative.
"""
                file_summary = call_llm(combined_prompt, "", provider,
                                     system_prompt="You are a code analyst providing integrated file summaries.",
                                     model_type="thinking")
                code_analysis["file_summaries"][file_path] = file_summary

            except Exception as e:
                print(f"\n⚠️  Error analyzing large file {file_path}: {e}")
                continue

        if small_files:
            print(f"\n🔍 Processing {len(small_files)} smaller files in batches...")
            batches = []
            current_batch = []
            current_batch_token_estimate = 0

            for file_path in small_files:
                content = code_contents.get(file_path, "")
                if not content:
                    continue
                ext = os.path.splitext(file_path)[1].lower()
                language = code_extensions.get(ext, "Unknown")
                file_token_estimate = len(content) / chars_per_token
                wrapper_token_estimate = 200

                if current_batch_token_estimate + file_token_estimate + wrapper_token_estimate > batch_token_limit:
                    if current_batch:
                        batches.append(current_batch)
                    current_batch = [(file_path, content, language)]
                    current_batch_token_estimate = file_token_estimate + wrapper_token_estimate
                else:
                    current_batch.append((file_path, content, language))
                    current_batch_token_estimate += file_token_estimate + wrapper_token_estimate

            if current_batch:
                batches.append(current_batch)

            print(f"📚 Created {len(batches)} batches of files for efficient processing")

            for i, batch in enumerate(batches):
                print(f"\r💭 Processing batch {i+1}/{len(batches)} ({len(batch)} files)...", end="")
                batch_files_content = []
                for file_path, content, language in batch:
                    batch_files_content.append(f"""
FILE: {file_path} ({language})
```{language.lower()}
{content}
```
""")

                batch_prompt = f"""
I'm analyzing a batch of {len(batch)} files from a codebase.
Here are the files:

{''.join(batch_files_content)}

For EACH file, provide a separate, concise summary that explains:
1. The overall purpose and functionality of the file
2. Key classes, functions, and components
3. How these components interact
4. The file's role in the larger project (if apparent)
5. Any notable patterns, technologies, or techniques used

Format your response with clear headings for each file:
## FILE: [filename]
[summary]

Keep each file's summary focused and informative.
"""
                try:
                    batch_analysis = call_llm(batch_prompt, "", provider,
                                           system_prompt="You are a code analyst providing summaries of multiple code files.",
                                           model_type="thinking")
                    file_sections = batch_analysis.split("## FILE:")

                    if file_sections and not file_sections[0].strip():
                        file_sections = file_sections[1:]

                    for section in file_sections:
                        if not section.strip():
                            continue
                        section_lines = section.strip().split("\n", 1)
                        if len(section_lines) < 2:
                            continue
                        filename = section_lines[0].strip()
                        summary = section_lines[1].strip()

                        matching_file = None
                        for file_path, _, _ in batch:
                            if os.path.basename(file_path) in filename:
                                matching_file = file_path
                                break
                        if matching_file:
                            code_analysis["file_summaries"][matching_file] = summary

                except Exception as e:
                    print(f"\n⚠️  Error processing batch {i+1}: {e}")
                    print("Falling back to individual file processing for this batch...")
                    for file_path, content, language in batch:
                        try:
                            file_prompt = f"""
Analyze this {language} file '{file_path}':

```{language.lower()}
{content}
```

Provide a concise summary that explains:
1. The overall purpose and functionality of this file
2. Key classes, functions, and components
3. How these components interact
4. The file's role in the larger project (if apparent)
5. Any notable patterns, technologies, or techniques used

Keep the summary focused and informative.
"""
                            file_summary = call_llm(file_prompt, "", provider,
                                                 system_prompt="You are a code analyst providing concise file summaries.",
                                                 model_type="thinking")
                            code_analysis["file_summaries"][file_path] = file_summary
                        except Exception as file_error:
                            print(f"\n⚠️  Error analyzing individual file {file_path}: {file_error}")
                            continue

        print()  # New line after the progress indicator

        print(f"📁 Generating summaries for {len(files_by_directory)} directories...")
        for dir_path, files in files_by_directory.items():
            analyzed_files = [f for f in files if f in code_analysis["file_summaries"]]
            if not analyzed_files:
                continue

            dir_prompt = f"""
I'm analyzing a directory '{dir_path}' with the following files:

{' '.join(f"File: {os.path.basename(f)}\nSummary: {code_analysis['file_summaries'][f]}\n\n" for f in analyzed_files if f in code_analysis["file_summaries"])}

Based on these file summaries, provide a comprehensive overview of this directory that explains:
1. The overall purpose and functionality of this directory/module
2. How the files within it relate to each other
3. The key functionality or service provided by this directory
4. Any design patterns or architectural approaches evident
5. Technologies and techniques used

Focus on how these components fit together as a cohesive unit.
"""

            dir_summary = call_llm(dir_prompt, "", provider,
                                system_prompt="You are a code architect providing module-level summaries.",
                                model_type="thinking")
            code_analysis["directory_summaries"][dir_path] = dir_summary

        if code_analysis["directory_summaries"]:
            print("🏗️ Creating overall project summary...")
            project_prompt = f"""
I've analyzed a software project with the following directories/modules:

{' '.join(f"Directory: {dir_path}\nSummary: {summary}\n\n" for dir_path, summary in code_analysis["directory_summaries"].items())}

Based on these directory summaries, provide a comprehensive overview of the entire project that explains:
1. The overall architecture and how components interact
2. The main technologies, frameworks, and libraries used
3. Key design patterns and architectural approaches
4. The apparent purpose and functionality of the application
5. How data flows through the system
6. Any notable development practices or conventions

Focus on creating a cohesive picture of the entire codebase that would help someone understand how it all fits together.
"""

            code_analysis["project_summary"] = call_llm(project_prompt, "", provider,
                                                    system_prompt="You are a software architect creating high-level project overviews.",
                                                    model_type="thinking")

        print("🧩 Identifying recurring patterns and conventions...")
        patterns_prompt = f"""
Based on the file and directory analyses above, identify recurring patterns and coding conventions in this codebase:

{code_analysis["project_summary"]}

Directory highlights:
{' '.join(f"- {dir_path}: {summary[:100]}...\n" for dir_path, summary in list(code_analysis["directory_summaries"].items())[:5])}

File highlights:
{' '.join(f"- {os.path.basename(file_path)}: {summary[:100]}...\n" for file_path, summary in list(code_analysis["file_summaries"].items())[:5])}

Please identify:
1. Naming conventions (for classes, functions, variables, etc.)
2. Design patterns and architectural patterns used
3. Code organization practices
4. Common techniques or idioms
5. Testing approaches
6. Error handling approaches
7. Common libraries and frameworks used
8. Other recurring patterns or practices

List each pattern with a brief explanation of how it's used in the codebase.
"""
        patterns_analysis = call_llm(patterns_prompt, "", provider,
                                 system_prompt="You are a code quality analyst identifying patterns and conventions in codebases.",
                                 model_type="thinking")

        code_analysis["patterns"] = patterns_analysis
        code_analysis["technologies"] = list(code_analysis["technologies"])

    print("✅ Code analysis complete!")
    return code_analysis


def update_memory_file(file_name, provider="openai"):
    """Update a specific memory bank file with new insights using the LLM."""
    # Use current working directory for memory-bank
    current_dir = os.getcwd()
    memory_dir = os.path.join(current_dir, "memory-bank")
    file_path = os.path.join(memory_dir, f"{file_name}.md")

    if not os.path.exists(memory_dir):
        print("❌ Oops! No memory-bank found. Please run 'llm_planner.py init' first.")
        sys.exit(1)

    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)

    print(f"\n🔄 Updating {file_name}.md with new insights...")

    # Read the current content
    with open(file_path, 'r', encoding='utf-8') as f:
        current_content = f.read()

    # Ask the user for the update information
    print(f"\n📝 What would you like to add or update in {file_name}.md?")
    print("Type your insights below (type 'EXIT' on a new line when finished):")

    update_text = ""
    while True:
        line = input()
        if line.strip() == "EXIT":
            break
        update_text += line + "\n"

    # Generate updated content
    prompt = f"""
You are maintaining the '{file_name}.md' file in a project's memory bank.
The file currently contains:

{current_content}

The user wants to add or update this file with the following information:

{update_text}

Your task:
1. Integrate the new information with the existing content
2. Resolve any contradictions, with preference to the new information
3. Organize the content logically with clear sections
4. Keep the same markdown formatting style
5. Update any outdated information
6. Make sure all information is consistent

Return the COMPLETE updated file content, not just the changes.
"""

    updated_content = call_llm(prompt, "", provider,
                              system_prompt="You are a helpful assistant that maintains documentation for software projects.",
                              model_type="thinking")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"\n✨ {file_name}.md has been successfully updated!")
    print("🔍 The LLM has integrated your insights into the existing content.")


def plan_feature(text_file_path, provider="openai", clarify=False):
    """Generate a plan based on the text file and memory bank context."""
    print("\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Entering plan mode...")
    print("🧠 Gathering the memory bank for context...\n")

    # Use current working directory for memory-bank
    current_dir = os.getcwd()
    memory_dir = os.path.join(current_dir, "memory-bank")
    if not os.path.exists(memory_dir):
        print("❌ Oops! No memory-bank found. Please run 'llm_planner.py init' first.")
        sys.exit(1)

    # Read all markdown files in memory-bank
    memory_contents = []
    for fname in os.listdir(memory_dir):
        if fname.endswith(".md"):
            with open(os.path.join(memory_dir, fname), 'r', encoding='utf-8') as f:
                content = f.read()
                memory_contents.append(f"# {fname}\n{content}")

    combined_memory = "\n\n".join(memory_contents)

    # Read the user-provided instructions from text_file_path
    if not os.path.exists(text_file_path):
        print(f"❌ Error: File '{text_file_path}' not found.")
        sys.exit(1)

    with open(text_file_path, 'r', encoding='utf-8') as tf:
        user_instructions = tf.read()

    # Analyze the text file for code snippets, references to files, etc.
    file_analysis = analyze_text_file(user_instructions)

    # Get project structure for additional context
    project_info = analyze_project_structure()

    # Check for TBD placeholders or other ambiguities
    if clarify:
        updated_instructions = clarify_with_llm(user_instructions, file_analysis, project_info, provider)
        if updated_instructions and updated_instructions != user_instructions:
            user_instructions = updated_instructions
    else:
        clarification_needed = check_for_clarifications(user_instructions)
        if clarification_needed:
            print("🚫 Cannot proceed until clarifications are made. Exiting plan mode.")
            print("💡 Tip: Run with --clarify flag for AI-assisted clarification.")
            sys.exit(0)

    plan_text = generate_plan(user_instructions, combined_memory, file_analysis, project_info, provider)
    final_plan = user_instructions + "\n\n" + "## LLM-Generated Plan:\n" + plan_text

    with open(text_file_path, 'w', encoding='utf-8') as tf:
        tf.write(final_plan)

    print("\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Your plan is ready!")
    print("📝 Please open the TXT file, review the plan, and update items as you complete them.")
    print("💡 Don't forget to record any important patterns in your memory bank!")
    print("🚀 As you execute the plan, use 'llm_planner.py update <file>' to keep your memory bank updated.")


def analyze_text_file(text):
    """Analyze the text file content for code snippets, file references, etc."""
    analysis = {
        "code_snippets": [],
        "file_references": [],
        "command_references": [],
        "potential_dependencies": []
    }

    code_pattern = re.compile(r'```(?:\w+)?\n(.*?)\n```', re.DOTALL)
    code_matches = code_pattern.findall(text)
    if code_matches:
        analysis["code_snippets"] = code_matches

    file_pattern = re.compile(r'(?:^|\s)([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)', re.MULTILINE)
    file_matches = file_pattern.findall(text)
    if file_matches:
        analysis["file_references"] = [f for f in file_matches if not f.endswith('.')]

    cmd_pattern = re.compile(r'`(.*?)`', re.MULTILINE)
    cmd_matches = cmd_pattern.findall(text)
    if cmd_matches:
        analysis["command_references"] = [c for c in cmd_matches if ' ' in c and not c.startswith('http')]

    dep_keywords = ["require", "import", "install", "package", "dependency", "module", "library"]
    for keyword in dep_keywords:
        if keyword in text.lower():
            for line in text.lower().split('\n'):
                if keyword in line:
                    analysis["potential_dependencies"].append(line.strip())

    return analysis


def clarify_with_llm(instructions, file_analysis, project_info, provider="openai"):
    """Use the LLM to generate clarifying questions and handle the interaction."""
    print("🔍 Analyzing your request for any ambiguities or missing details...")

    prompt = f"""
I have a feature request or task description that might need clarification:

{instructions}

Based on the provided task description and the following analysis:
- File references: {file_analysis['file_references']}
- Code snippets: {'Yes' if file_analysis['code_snippets'] else 'No'}
- Project context: This is a {', '.join(project_info['potential_languages'])} project

Please identify 1-3 specific clarifying questions that would help make this task description more precise and actionable.
Focus on:
1. Any ambiguous requirements
2. Missing technical details
3. Scope clarification
4. Implementation preferences
5. Integration points

Return ONLY the numbered questions, nothing else.
"""

    questions = call_llm(prompt, "", provider,
                      system_prompt="You are a helpful assistant that identifies ambiguities in task descriptions.",
                      model_type="thinking")

    if not questions or "no clarification needed" in questions.lower():
        print("✅ Your request seems clear! No clarification needed.")
        return None

    print("\n❓ I have some clarifying questions to make your plan more accurate:")
    print(questions)

    print("\n📝 Please provide answers to these questions (type 'EXIT' on a new line when finished):")
    answers = ""
    while True:
        line = input()
        if line.strip() == "EXIT":
            break
        answers += line + "\n"

    updated_instructions = f"{instructions}\n\n## Clarifications:\n\n{questions}\n\n{answers}"
    return updated_instructions


def check_for_clarifications(text):
    """Check if the input text needs clarification based on simple patterns."""
    if "TBD" in text or "TODO" in text or "???" in text or "TBC" in text:
        print("❓ It looks like there are placeholders in your instructions:")
        if "TBD" in text:
            print("  • Found 'TBD' - Please provide more specific details.")
        if "TODO" in text:
            print("  • Found 'TODO' - Please complete this section before proceeding.")
        if "???" in text:
            print("  • Found '???' - Please clarify these questions.")
        if "TBC" in text:
            print("  • Found 'TBC' - Please confirm these details.")
        return True

    if len(text.strip()) < 50:
        print("📢 Your instructions seem quite brief. This might lead to a less detailed plan.")
        print("Would you like to add more details before proceeding? (y/n)")
        response = input("> ")
        if response.lower() == 'y':
            print("📝 Please update your text file and run the command again.")
            return True

    return False


def generate_plan(instructions, memory_context, file_analysis, project_info, provider="openai"):
    """Generate a comprehensive plan using the LLM with enhanced context."""
    print(f"🤖 Calling LLM ({provider}) to create your master plan...")

    technologies = ", ".join(project_info['potential_languages'] + project_info['potential_frameworks'])
    file_refs = ", ".join(file_analysis['file_references']) if file_analysis['file_references'] else "None"
    code_snippets = "\n\n".join(file_analysis['code_snippets']) if file_analysis['code_snippets'] else "None"

    llm_prompt = f"""
You are a senior developer and technical lead charged with creating a detailed implementation plan.

# TASK DESCRIPTION
{instructions}

# PROJECT CONTEXT
Technologies: {technologies}
Referenced files: {file_refs}
Code snippets:
```
{code_snippets}
```

# MEMORY BANK CONTEXT
{memory_context}

Based on all the information above, create a comprehensive implementation plan that will guide
a junior developer through implementing this feature or task.

Your plan MUST include:
1) A clear breakdown of all implementation steps in the exact order they should be performed
2) Technical details and considerations drawn from the memory bank context
3) Estimated effort for each task (Low/Medium/High)
4) Dependencies between tasks
5) Any potential challenges or gotchas to watch out for
6) Testing strategies for the implementation

Format your response as a markdown checklist with nested items where appropriate.
Each major step should include:
- A descriptive title in **bold**
- The estimated effort
- Detailed sub-steps indented under the main step
- Any specific technical guidance drawn from the memory bank
- Any referenced files or code that will need to be modified

End your plan with a reminder for the developer to update the memory bank with any new patterns or insights discovered during implementation.

Remember that you're writing for a junior developer who might not know all the context, so be explicit and clear in your instructions.
"""

    system_prompt = """You are a senior developer and technical lead with expertise in software architecture and implementation planning.
Your plans are detailed, precise, and actionable, providing clear guidance that even junior developers can follow."""

    return call_llm(llm_prompt, "", provider, system_prompt=system_prompt, model_type="thinking")


def call_llm(prompt, memory_context="", provider="openai",
             system_prompt="You are a helpful planning assistant.", model_type="thinking"):
    """
    Call the LLM based on the selected provider with enhanced error handling.

    Args:
        prompt: The prompt to send to the LLM
        memory_context: Additional context to include
        provider: The LLM provider to use (openai, aws, azure)
        system_prompt: The system prompt to use
        model_type: Either "thinking" for complex analysis or "fast" for simpler operations
    """
    if provider == "openai":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            animation = [
                "🧙 Conjuring smart thoughts...",
                "🔮 Gazing into the crystal ball...",
                "🧠 Neurons firing wildly...",
                "🚀 Preparing for liftoff...",
                "⚡ Channeling digital wisdom..."
            ]
            for i, frame in enumerate(animation):
                print(f"\r{frame}", end="")
            print("\r" + " " * 50 + "\r", end="")

            if model_type == "thinking":
                models_to_try = ["o3-mini", "gpt-3.5-turbo-16k", "gpt-3.5-turbo"]
            else:
                models_to_try = ["gpt-4o-mini", "gpt-3.5-turbo"]

            last_error = None

            for model in models_to_try:
                try:
                    # print(f"Trying with model: {model}...")
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return response.choices[0].message.content.strip()
                except Exception as model_error:
                    last_error = model_error
                    print(f"Error with model {model}: {model_error}")

            raise last_error or Exception("All models failed")

        except Exception as e:
            print(f"❌ Error calling OpenAI API: {e}")
            sys.exit(1)

    elif provider == "aws":
        print("⚠️  AWS Bedrock support is in placeholder mode.")
        return "# AWS Bedrock support\n\nThis is a placeholder for AWS Bedrock integration."

    elif provider == "azure":
        print("⚠️  Azure OpenAI support is in placeholder mode.")
        return "# Azure OpenAI support\n\nThis is a placeholder for Azure OpenAI integration."

    else:
        print(f"❌ Unknown provider: {provider}")
        sys.exit(1)


if __name__ == "__main__":
    main()
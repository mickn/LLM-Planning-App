# LLM Planner

A Python command-line application for planning and documenting tasks with large language models (LLMs).

## Features

- ✨ Terminal-based interface with whimsical output
- 🧠 AI-powered "Memory Bank" generation based on deep code analysis
- 📚 Hierarchical codebase summarization (files → directories → project)
- 📝 Smart plan generation using context from your actual code
- 🔍 AI-assisted clarification for ambiguous requirements
- 🔄 Memory bank updating with LLM assistance
- 🌐 Support for OpenAI, with placeholders for Amazon Bedrock/Anthropic and Azure OpenAI
- 📊 Project structure and pattern analysis

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your API credentials:

```bash
# For OpenAI
export OPENAI_API_KEY=your_api_key_here

# For AWS (optional)
export AWS_ACCESS_KEY_ID=your_id_here
export AWS_SECRET_ACCESS_KEY=your_key_here

# For Azure (optional)
export AZURE_OPENAI_KEY=your_key_here
```

## Commands

### Initialize Memory Bank

Initialize the memory bank with AI-generated content based on deep code analysis:

```bash
python llm_planner.py init
```

The tool will:
1. Analyze your project structure (files, directories, languages, frameworks)
2. **Read and analyze your actual code:**
   - For small codebases (< 150K tokens): Analyze the entire codebase at once for maximum context
   - For larger codebases: Use a hierarchical approach that:
     - First analyzes individual files to understand their purpose and components
     - Automatically chunks large files for better analysis
     - Then summarizes directories to understand how files work together
     - Finally creates a project-level summary that explains the overall architecture
   - Identify recurring patterns and coding conventions used in your codebase
3. Generate intelligent content for the following memory bank files:
   - `projectbrief.md` - AI-generated overview of your project
   - `productContext.md` - Features and requirements based on code analysis
   - `activeContext.md` - Current development focus and tasks
   - `systemPatterns.md` - Detected coding patterns and conventions
   - `techContext.md` - Technical stack and architecture
   - `progress.md` - Progress tracking template

### Create a Plan

Generate a comprehensive plan for implementing a feature:

```bash
python llm_planner.py plan your_feature.txt
```

With interactive clarification (recommended):

```bash
python llm_planner.py plan your_feature.txt --clarify
```

The tool will:
- Read your feature description
- Analyze for code snippets, file references, and commands
- Extract context from your memory bank
- Identify potential ambiguities in your requirements
- Generate clarifying questions (with `--clarify` flag)
- Create a detailed implementation plan with:
  - Step-by-step tasks
  - Effort estimates
  - Dependencies
  - Technical considerations
  - Testing strategies

### Update Memory Bank

Update specific memory bank files with new insights:

```bash
python llm_planner.py update projectbrief
python llm_planner.py update techContext
# etc.
```

The tool will:
- Show the current content
- Prompt you for changes or additions
- Use AI to integrate your changes seamlessly
- Save the updated file

## Example Usage

### Creating a Plan

1. Create a `.txt` file with your feature request:
   ```
   # Add File Upload Feature

   We need to implement a file upload feature with the following requirements:
   - Support uploading images and documents
   - Maximum file size of 10MB
   - Store uploaded files in cloud storage
   - Generate thumbnails for images
   ```

2. Generate a plan with clarification:
   ```bash
   python llm_planner.py plan upload_feature.txt --clarify
   ```

3. Answer any clarifying questions:
   ```
   ❓ I have some clarifying questions to make your plan more accurate:
   1. Which cloud storage provider do you want to use (AWS S3, Google Cloud Storage, Azure Blob Storage)?
   2. What image formats should be supported for thumbnail generation?
   3. Where will these uploads be used in the application (user profiles, content posts, etc.)?

   📝 Please provide answers to these questions:
   > 1. AWS S3
   > 2. JPEG, PNG, and GIF
   > 3. Product catalog images and document attachments
   > EXIT
   ```

4. Review the generated plan in your text file:
   ```
   # Add File Upload Feature
   
   We need to implement a file upload feature with the following requirements:
   - Support uploading images and documents
   - Maximum file size of 10MB
   - Store uploaded files in cloud storage
   - Generate thumbnails for images
   
   ## Clarifications:
   
   1. Which cloud storage provider do you want to use (AWS S3, Google Cloud Storage, Azure Blob Storage)?
   2. What image formats should be supported for thumbnail generation?
   3. Where will these uploads be used in the application (user profiles, content posts, etc.)?
   
   1. AWS S3
   2. JPEG, PNG, and GIF
   3. Product catalog images and document attachments
   
   ## LLM-Generated Plan:
   
   - [ ] **Setup AWS S3 Configuration** (Effort: Medium)
     - Configure AWS SDK in the application
     - Create S3 bucket for file storage
     - Set up proper access permissions
     - Implement configuration file for S3 credentials
   
   - [ ] **Create File Upload API Endpoint** (Effort: Medium)
     - Implement multipart form handling
     - Add file size validation (10MB limit)
     - Implement file type validation for images and documents
     - Add error handling for upload failures
   
   ... etc.
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
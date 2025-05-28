# RepoPush-Automated Project Upload to GitHub

A llm-powered project to automatically upload local projects to your github account with a generated Readme file as well.

## Description
This tool provides an automated solution for uploading local projects to GitHub, generating a Readme file, and managing repository settings. It leverages LLMs like Ollama for efficient content generation and automation.

## Context
A simple llm-powered project to automatically upload local projects to your github account with a generated Readme file as well.

## Relevant Files

### main.py
- GitHubProjectUploader class
  - `setup_github`: Initializes GitHub client
  - `create_temp`: Creates clean workspace in temp directory
  - `get_relevant_files_content`: Extracts important files for README generation
  - `generate_with_ollama`: Generates README using LLM
  - `generate_readme_content`: Generates README with local Ollama model
  - `check_repo_exists`: Checks if repository already exists
  - `upload_project`: Handles project upload workflow

### .env file contents
- GITHUB_TOKEN: Required environment variable for GitHub authentication

## Usage
1. Connect to GitHub via token using `github_token`
2. Upload projects with parameters:
   - Project path
   - Repository name
   - Description (optional)
   - Private repo flag
   - Update existing repo or update it

## Installation
Install dependencies:
```bash
pip install requests python-dotenv


## Example Usage
```python
# Create temporary workspace for project
src_dir = tempfile.mkdtemp()
dest_dir = os.path.join(src_dir, os.path.basename(__file__))
os.makedirs(dest_dir, exist_ok=True)

# Generate README content using LLM
readme_content = GitHubProjectUploader.generate_with_ollama(
    prompt="Generate a README for this local project with proper structure.",
    model="deepseek-r1:1.5b",
    stream=False,
    options={"temperature": 0.3, "max_tokens": 1024}
)

# Upload the updated project
readme_content = open(os.path.join(dest_dir, 'README.md'), 'r').readlines()
```

## Dependencies
- GitHub API (requires API key)
- requests package
- python-dotenv package

## Usage in Development Workflow
1. Connect to GitHub via `github_token`
2. Upload your local project using:
   ```bash
   github_push --api POST \
      http://your-repository-url.git.io \
      --output README.md \
      --private \
      --description "Your description or read the README"
   ```
3. Use automated processes for repetitive tasks like generating READMEs, uploading projects.

## Notes
- Requires GitHub API authentication
- Uses LLMs (deepseek-r1:1.5b) for content generation
- Handles private and public repositories
```

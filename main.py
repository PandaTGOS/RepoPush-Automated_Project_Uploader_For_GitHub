import os
import shutil
import tempfile
from github import Github
from huggingface_hub import InferenceClient
import subprocess
from dotenv import load_dotenv

load_dotenv()

class GitHubProjectUploader:
    def __init__(self):
        self.temp_dir = None
        self.hf_client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.1")
        
    def setup_github(self, token):
        """Initialize GitHub client"""
        self.github = Github(token)
        
    def create_temp_workspace(self, source_path):
        """Create clean workspace in temp directory"""
        self.temp_dir = tempfile.mkdtemp()
        dest_path = os.path.join(self.temp_dir, os.path.basename(source_path))
        
        # Copy without .git directory if exists
        if os.path.exists(os.path.join(source_path, '.git')):
            shutil.copytree(source_path, dest_path, 
                          ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.env'))
        else:
            shutil.copytree(source_path, dest_path)
            
        return dest_path
    
    def get_relevant_files_content(self, project_path):
        """Get content of important files for README generation"""
        relevant_files = []
        
        # Get content of these files if they exist
        for root, _, files in os.walk(project_path):
            for file in files:
                if file in ['.env', '.gitignore'] or file.endswith(('.pyc', '.pkl', '.db', '.log')):
                    continue
                else:
                    try:
                        with open(os.path.join(root, file), 'r') as f:
                            content = f.read()
                            relevant_files.append({
                                'name': file,
                                'path': os.path.join(root, file),
                                'content': content[:2000]
                            })
                    except:
                        continue
        
        return relevant_files
    
    def generate_readme_content(self, project_path, repo_name, description=""):
        """Generate concise README with only essential sections"""
        relevant_files = self.get_relevant_files_content(project_path)
        
        # Format files content for prompt
        files_content = "\n\n".join(
            f"File: {file['name']}\nContent:\n{file['content']}"
            for file in relevant_files
        )
        
        system_prompt = """You are an expert technical writer specializing in GitHub documentation. Create a professional, concise README.md with EXACTLY these 4 sections:
            
            1. **Project Title and Description** 
               - Create a comprehensive description analyzing the code structure and purpose
               - Never copy the user's input description directly - synthesize new insights
               - Highlight the project's core functionality and value proposition
               - Include technical specifics from the actual code files
               
            2. **Key Features**
               - List 3-5 main capabilities with technical specifics
               - Reference actual functions/classes from the code when possible
               - Focus on unique or innovative aspects
               
            3. **Installation and Setup**
               - Provide specific, executable commands
               - Include any environment requirements
               - Mention configuration steps if needed
               
            4. **Basic Usage**
               - Show a practical example of how to use the project
               - Include code snippets if applicable
               - Demonstrate core functionality
            
            **Formatting Rules:**
            - Use clean GitHub-flavored markdown
            - Section headers must be ## level
            - Code blocks must use proper syntax highlighting
            - Keep sentences concise but informative
            - Never include placeholder text - only concrete details
            - Do NOT include any additional sections like License, Contributing etc.
            
            **Quality Requirements:**
            - The description must be entirely original based on code analysis
            - Technical accuracy is paramount
            - Each section should be 3-5 paragraphs or bullet points
            - Maintain professional tone throughout"""
        
        user_prompt = f"""Repository Name: {repo_name}
            User Context (for reference only - do NOT copy): "{description}"
            
            Relevant project files content:
            {files_content}

            Generate ONLY the 4 requested sections with professional technical documentation:"""
        
        response = self.hf_client.text_generation(
            f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}",
            max_new_tokens=2048,  
            temperature=0.6,      
            do_sample=True
        )
        
        # Post-process to ensure proper format
        content = response.strip()
        if not content.startswith("# "):
            content = f"# {repo_name}\n\n" + content
            
        # Ensure we only have the 4 requested sections
        sections = []
        current_section = []
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
            current_section.append(line)
        if current_section:
            sections.append('\n'.join(current_section))
            
        # Take only first 4 sections if more were generated
        if len(sections) > 4:
            sections = sections[:4]
            
        return '\n\n'.join(sections)
    
    def upload_project(self, source_path, repo_name, is_private=False, description=""):
        """Complete project upload workflow"""
        try:
            # Step 1: Create clean workspace
            project_path = self.create_temp_workspace(source_path)
            
            # Step 2: Generate concise README
            readme_content = self.generate_readme_content(project_path, repo_name, description)
            
            # Write README to project
            with open(os.path.join(project_path, 'README.md'), 'w') as f:
                f.write(readme_content)
            
            # Step 3: Setup .gitignore to exclude .env
            gitignore_path = os.path.join(project_path, '.gitignore')
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w') as f:
                    f.write('.env\n')
            elif '.env' not in open(gitignore_path).read():
                with open(gitignore_path, 'a') as f:
                    f.write('\n.env\n')

            # Safety check: remove .env if it somehow exists
            env_path = os.path.join(project_path, '.env')
            if os.path.exists(env_path):
                os.remove(env_path)

            # Step 4: Initialize and push to GitHub
            os.chdir(project_path)
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)

            # Create GitHub repository
            user = self.github.get_user()
            repo = user.create_repo(repo_name, private=is_private, description=description)

            # Add remote and push
            subprocess.run(['git', 'remote', 'add', 'origin', repo.clone_url], check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)

            print(f"Successfully uploaded to: {repo.html_url}")
            return repo

        finally:
            # Clean up
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    uploader = GitHubProjectUploader()
    
    # Get GitHub token - create at https://github.com/settings/tokens
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise EnvironmentError("GITHUB_TOKEN environment variable not set.")
    uploader.setup_github(github_token)
    
    # Upload project
    project_path = input("Enter path to your project: ").strip('"\' ')
    repo_name = input("Enter desired repository name: ")
    private = input("Make private? (y/n): ").lower() == 'y'
    description = input("Enter short description (optional, helps guide README generation): ")
    
    repo = uploader.upload_project(project_path, repo_name, private, description)
    print(f"View your new repository at: {repo.html_url}")
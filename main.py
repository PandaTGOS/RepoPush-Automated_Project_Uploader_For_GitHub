import os
import shutil
import tempfile
from github import Github
import subprocess
import requests
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class GitHubProjectUploader:
    def __init__(self):
        self.temp_dir = None
        print("✅ Using local Ollama deepseek-r1:1.5b model")
        
    def setup_github(self, token):
        """Initialize GitHub client"""
        self.github = Github(token)
        
    def create_temp_workspace(self, source_path):
        """Create clean workspace in temp directory"""
        self.temp_dir = tempfile.mkdtemp()
        dest_path = os.path.join(self.temp_dir, os.path.basename(source_path))
        
        if os.path.exists(os.path.join(source_path, '.git')):
            shutil.copytree(source_path, dest_path, 
                          ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.env'))
        else:
            shutil.copytree(source_path, dest_path)
            
        return dest_path
    
    def get_relevant_files_content(self, project_path):
        """Get content of important files for README generation"""
        relevant_files = []
        exclude_exts = ('.pyc', '.pkl', '.db', '.log', '.DS_Store')
        
        for root, _, files in os.walk(project_path):
            for file in files:
                if file in ['.env', '.gitignore'] or file.endswith(exclude_exts):
                    continue
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        relevant_files.append({
                            'name': file,
                            'path': os.path.join(root, file),
                            'content': content
                        })
                except:
                    continue
        
        return relevant_files
    
    def generate_with_ollama(self, prompt):
        """Generate text using local Ollama API"""
        try:
            # Ollama's local API typically runs on http://localhost:11434
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "deepseek-r1:1.5b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "max_tokens": 1024
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Remove content within <think> tags if present
            response_text = result.get("response", "")
            if "<think>" in response_text:
                start = response_text.find("<think>")
                end = response_text.find("</think>") + len("</think>")
                response_text = response_text[:start] + response_text[end:]
                
            return response_text.strip()
        except Exception as e:
            print(f"Error calling Ollama API: {e}")
            return ""
    
    def generate_readme_content(self, project_path, repo_name, description=""):
        """Generate README using local Ollama model"""
        relevant_files = self.get_relevant_files_content(project_path)
        
        files_content = "\n\n".join(
            f"### {file['name']}\n```\n{file['content']}\n```"
            for file in relevant_files[:5]  # Limit to 5 files to avoid overload
        )
        
        system_prompt = """You are an expert technical professional specializing in writing precise and effective README.md files for GitHub repositories. Your extensive experience enables you to create documentation that is not only informative but also easy to understand for users who may clone the repository. 
Your task is to create a concise GitHub README.md file. Start with a section titled Project Title at the top as a # Header. Ensure you adhere strictly to the following rules: use GitHub Markdown only; avoid placeholders and include only concrete, useful details from the code that would benefit the user; maintain a professional tone; include any necessary information such as the required .env file contents; and refrain from inventing features that do not exist.
Here are the details you need to include in the README.md file:  

Project Title: __________  
Description: __________  
Context: __________  
Relevant Files: __________

Generate ONLY the requested README.md file's contents in markdown format with good amount of details.
"""
        
        user_prompt = f"""Create README for: {repo_name}
Description Context: "{description}"

Relevant Files:
{files_content}

Generate ONLY the requested Readme.md file's contents in markdown"""
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Generate with Ollama
        print("⚡ Generating README with deepseek-r1:1.5b...")
        response = self.generate_with_ollama(full_prompt)
            
        return response
    
    def check_repo_exists(self, repo_name):
        """Check if repository already exists"""
        user = self.github.get_user()
        try:
            repo = user.get_repo(repo_name)
            return repo
        except:
            return None
    
    def upload_project(self, source_path, repo_name, is_private=False, description="", update_existing=False):
        """Complete project upload workflow with support for existing repos"""
        try:
            project_path = self.create_temp_workspace(source_path)
            
            # Generate README
            readme_content = self.generate_readme_content(project_path, repo_name, description)
            with open(os.path.join(project_path, 'README.md'), 'w') as f:
                f.write(readme_content)
            
            # Ensure .gitignore
            gitignore_path = os.path.join(project_path, '.gitignore')
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w') as f:
                    f.write(".env\n__pycache__/\n*.pyc\n")
            
            # Remove .env if exists
            env_path = os.path.join(project_path, '.env')
            if os.path.exists(env_path):
                os.remove(env_path)

            # Git operations
            os.chdir(project_path)
            subprocess.run(['git', 'init', '-b', 'main'], check=True)
            subprocess.run(['git', 'config', 'user.email', 'you@example.com'])  # Temporary config
            subprocess.run(['git', 'config', 'user.name', 'GitHub Uploader'])   # Temporary config
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)

            # Check for existing repo
            existing_repo = self.check_repo_exists(repo_name)
            
            if existing_repo:
                if not update_existing:
                    raise Exception(f"Repository {repo_name} already exists. Use update_existing=True to update it.")
                
                print(f"🔄 Updating existing repository: {repo_name}")
                # Get authenticated URL using the token from environment
                username = self.github.get_user().login
                token = os.getenv("GITHUB_TOKEN") or input("Enter GitHub token: ").strip()
                encoded_token = quote_plus(token)
                repo_url = f"https://{username}:{encoded_token}@github.com/{username}/{repo_name}.git"
                subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)
                subprocess.run(['git', 'push', '--force', 'origin', 'main'], check=True)
                repo = existing_repo
            else:
                # Create new GitHub repo
                user = self.github.get_user()
                repo = user.create_repo(repo_name, private=is_private, description=description)
                
                # Push to GitHub
                subprocess.run(['git', 'remote', 'add', 'origin', repo.clone_url], check=True)
                subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)

            print(f"🚀 Successfully {'updated' if existing_repo else 'uploaded'} to: {repo.html_url}")
            return repo

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)

if __name__ == "__main__":
    print("🌍 GitHub Project Uploader (Local Ollama deepseek-r1:1.5b)")
    uploader = GitHubProjectUploader()
    
    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        github_token = input("Enter GitHub token: ").strip()
    uploader.setup_github(github_token)
    
    # Get project details
    project_path = input("Enter project path: ").strip('"\' ')
    repo_name = input("Enter repository name: ").strip()
    private = input("Private repo? (y/n): ").lower() == 'y'
    description = input("Short description (optional): ").strip()
    
    # Check if repo exists
    existing_repo = uploader.check_repo_exists(repo_name)
    if existing_repo:
        update = input(f"Repository '{repo_name}' already exists. Update it? (y/n): ").lower() == 'y'
        if not update:
            print("Operation cancelled.")
            exit()
    
    # Upload/Update
    repo = uploader.upload_project(
        project_path, 
        repo_name, 
        private, 
        description,
        update_existing=bool(existing_repo))
    print(f"✅ Done! View at: {repo.html_url}")

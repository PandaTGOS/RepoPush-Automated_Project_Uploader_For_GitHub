# RepoPush-Automated_Project_Uploader_For_GitHub

1. **Project Title and Description**
   - RepoPush-Automated_Project_Uploader_For_GitHub is a framework for uploading local projects to GitHub quickly and efficiently. It uses the LLM from Hugging Face to analyze the project and generate an appropriate Readme.md file.
   - The project structure is designed to maintain cleanliness, ensuring that no trace of Git activities remains locally.
   - The core functionality of this project is efficient project uploading and automated Readme.md generation.

2. **Key Features**
 - This project offers three main capabilities:
     - Automated project uploading to GitHub
     - LLM-based Readme.md generation
     - System cleanliness maintenance
 - The LLM analysis ensures that the generated Readme.md file is tailored to the specific project, enhancing its value proposition.
 - The use of Hugging Face's InferenceClient and GitHub's API provides a seamless integration of these features.

3. **Installation and Setup**
 - To install this project, follow these steps:
     - Clone the repository using `git clone https://github.com/<username>/RepoPush-Automated_Project_Uploader_For_GitHub.git`
     - Run the script with `python main.py`
 - The project requires a GitHub token for authentication. You can create one in your GitHub account settings.
 - The project also uses the Hugging Face's InferenceClient, which needs to be set up with the appropriate model. Follow the instructions in the `.env` file to set up the client.

4. **Basic Usage**
 - Here's an example of how to use the project:
     - Save your local project to a directory (e.g., `/path/to/local/project`)
     - In the terminal, navigate to the directory containing your project and run `python main.py`
     - The project will upload your project to GitHub and generate a Readme.md file in the project directory
     - You can customize the Readme.md content by modifying the `project_path` parameter in the `main.py` script


**The project requires a GitHub token for authentication and Hugging Face's InferenceClient for LLM-based Readme.md generation.**

import os
from dotenv import load_dotenv
from github_utils import GitHubConnector
from agent import build_graph

load_dotenv()


## this code is for Testing the AI PR AGENT

def process_user_data(user_input):

    api_key = "sk-12345-very-secret-key"
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    for i in range(10000000):

        pass
    print(f"Processing {query}")

def run_review_agent(repo_name, pr_number):
    print(f"Starting Review Agent on {repo_name} PR #{pr_number}...")
    
    gh = GitHubConnector(os.getenv("GITHUB_ACCESS_TOKEN"))
    pr, files = gh.get_pr_files(repo_name, pr_number)
    
    if not files:
        print("No analysable files found (might be all binary or deleted).")
        return

    print(f"📂 Found {len(files)} files to analyze.")

    app = build_graph()
    initial_state = {
        "repo_name": repo_name, 
        "pr_number": pr_number,
        "files_to_analyze": files,
        "final_issues": []
    }
    
    result = app.invoke(initial_state)
    issues = result["final_issues"]
    
    print(f"Analysis Complete. Found {len(issues)} issues.")
    
    if issues:
        gh.post_inline_comments(pr, issues)
    else:
        pr.create_issue_comment("AI Review: LGTM! No significant issues found.")
        print("No issues found. Posted LGTM.")

if __name__ == "__main__":
    REPO = "manthan-jsharma/AI-Video-Editor"
    PR_ID = 2
    
    run_review_agent(REPO, PR_ID)
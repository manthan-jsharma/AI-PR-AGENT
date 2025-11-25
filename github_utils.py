from github import Github
import os

class GitHubConnector:
    def __init__(self, token):
        self.g = Github(token)

    def get_pr_files(self, repo_name: str, pr_number: int):
        """Fetches files and their patches from a PR."""
        repo = self.g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        files_data = []
        for file in pr.get_files():
            if file.status == "removed" or not file.patch:
                continue
            
            files_data.append({
                "filename": file.filename,
                "patch": file.patch,
                "raw_url": file.raw_url,
                "blob_url": file.blob_url
            })
        return pr, files_data

    def post_inline_comments(self, pr, issues):
      
        body = "## AI Code Reviewer Report\n\n"
        
        files = list(set(i.file_path for i in issues))
        
        for f in files:
            file_issues = [i for i in issues if i.file_path == f]
            body += f"### 📄 `{f}`\n"
            for issue in file_issues:
                icon = "🔴" if issue.severity == "Critical" else "⚠️" if issue.severity == "Medium" else "ℹ️"
                body += f"\n**{icon} Line {issue.line_number} ({issue.issue_type})**\n"
                body += f"{issue.description}\n"
                if issue.suggestion:
                    body += f"```suggestion\n{issue.suggestion}\n```\n"
            body += "---\n"

        pr.create_issue_comment(body)
        print("Review posted successfully!")
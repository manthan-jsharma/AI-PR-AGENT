import streamlit as st
import os
from github_utils import GitHubConnector
from agent import build_graph

try:
    os.environ["GITHUB_ACCESS_TOKEN"] = st.secrets["GITHUB_ACCESS_TOKEN"]
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    from dotenv import load_dotenv
    load_dotenv()


## Note: This specific file is for Streamlit frontend Deploymnt

st.set_page_config(page_title="AI Code Reviewer", page_icon="🤖")

st.title("AI Pull Request Reviewer")
st.markdown("---")

pr_url = st.text_input("Enter Public GitHub PR URL to see AI Reviews and Post them", placeholder="https://github.com/manthan-jsharma/AI-Video-Editor/pull/2")

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "issues" not in st.session_state:
    st.session_state.issues = []
if "pr_obj" not in st.session_state:
    st.session_state.pr_obj = None

if st.button("Run Analysis"):
    if not pr_url:
        st.warning("Please enter a URL first.")
    else:
        try:
            parts = pr_url.strip("/").split("/")
            repo_name = f"{parts[3]}/{parts[4]}"
            pr_number = int(parts[6])
            
            st.info(f"Analyzing {repo_name} #{pr_number}...")
            
            gh = GitHubConnector(os.environ["GITHUB_ACCESS_TOKEN"])
            pr, files = gh.get_pr_files(repo_name, pr_number)
            
            st.session_state.pr_obj = pr
            st.session_state.repo_name = repo_name
            st.session_state.pr_number = pr_number

            if not files:
                st.error("No analyzable files found.")
            else:
                app = build_graph()
                state = {
                    "repo_name": repo_name,
                    "pr_number": pr_number,
                    "files_to_analyze": files,
                    "security_issues": [],
                    "performance_issues": [],
                    "style_issues": [],
                    "final_issues": []
                }
                
                with st.spinner("Consulting AI Agents (Security, Performance, Style)..."):
                    result = app.invoke(state)
                    st.session_state.issues = result["final_issues"]
                    st.session_state.analysis_done = True
                    
        except Exception as e:
            st.error(f"Error: {e}")

if st.session_state.analysis_done:
    issues = st.session_state.issues
    
    st.success(f"Analysis Complete! Found {len(issues)} issues.")
    
    for issue in issues:
        with st.expander(f"{issue.severity} - {issue.issue_type}: {issue.file_path}"):
            st.markdown(f"**Description:** {issue.description}")
            st.markdown(f"**Suggestion:**")
            st.code(issue.suggestion, language="python")

    st.markdown("---")
    
    if issues:
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button(" Post These Comments to GitHub"):
                try:
                    gh = GitHubConnector(os.environ["GITHUB_ACCESS_TOKEN"])
                    gh.post_inline_comments(st.session_state.pr_obj, issues)
                    st.balloons()
                    st.success("✅ Successfully posted comments to GitHub!")
                except Exception as e:
                    st.error(f"Failed to post: {e}")
    else:
        st.info("No issues found. Nothing to post!")
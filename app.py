import streamlit as st
import os
from dotenv import load_dotenv
from github_utils import GitHubConnector
from agent import build_graph
load_dotenv()


## Note: This specific file is for Streamlit frontend Deploymnt

st.set_page_config(page_title="AI Code Reviewer", page_icon="🤖")

st.title("AI Pull Request Reviewer")
st.write("Paste a Public GitHub PR link below to generate an AI review instantly.")

pr_url = st.text_input("GitHub PR URL", placeholder="https://github.com/manthan-jsharma/AI-Video-Editor/pull/1")

if st.button("Run Analysis"):
    if not pr_url:
        st.warning("Please enter a valid URL.")
    else:
        try:
            parts = pr_url.strip("/").split("/")
            repo_name = f"{parts[3]}/{parts[4]}"
            pr_number = int(parts[6])
            
            st.info(f"🔍 Analyzing **{repo_name}** PR **#{pr_number}**...")
            
            gh = GitHubConnector(os.getenv("GITHUB_ACCESS_TOKEN"))
            pr, files = gh.get_pr_files(repo_name, pr_number)
            
            if not files:
                st.error("No analyzable files found in this PR.")
            else:
                app = build_graph()
                state = {
                    "repo_name": repo_name,
                    "pr_number": pr_number,
                    "files_to_analyze": files,
                    "final_issues": []
                }
                
                with st.spinner("Consulting the AI Architects..."):
                    result = app.invoke(state)
                    issues = result["final_issues"]
                
                st.success(f"Analysis Complete! Found {len(issues)} issues.")
                
                if issues:
                    for issue in issues:
                        with st.expander(f"{issue.severity}: {issue.file_path} (Line {issue.line_number})"):
                            st.markdown(f"**Type:** {issue.issue_type}")
                            st.markdown(f"**Issue:** {issue.description}")
                            st.markdown(f"**Suggestion:**")
                            st.code(issue.suggestion, language="python")
                else:
                    st.balloons()
                    st.write("Code looks great! LGTM.")
                    
        except Exception as e:
            st.error(f"Error: {e}")
            st.write("Make sure the URL format is correct and the Repo is Public.")
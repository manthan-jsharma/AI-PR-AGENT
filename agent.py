from typing import List, TypedDict
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from models import PRReviewResult, CodeIssue
from github_utils import GitHubConnector

class AgentState(TypedDict):
    repo_name: str
    pr_number: int
    files_to_analyze: List[dict]
    final_issues: List[CodeIssue]

def analyze_code_node(state: AgentState):
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        google_api_key=os.environ["GOOGLE_API_KEY"]
    )
    
    structured_llm = llm.with_structured_output(PRReviewResult)
    
    all_issues = []
      
    for file_data in state["files_to_analyze"]:
        filename = file_data["filename"]
        patch = file_data["patch"]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Code Reviewer. Review the provided Git Patch. "
                       "Identify critical bugs, security flaws, and performance issues. "
                       "Ignore style nits. Only comment on changed lines (+)."),
            ("human", "File Name: {filename}\n\nGit Patch:\n{patch_content}")
        ])
        
        chain = prompt | structured_llm
        try:
            result = chain.invoke({"filename": filename, "patch_content": patch})            
            if result.issues:
                for issue in result.issues:
                    issue.file_path = filename
                    all_issues.append(issue)
                    
        except Exception as e:
            print(f"Error analyzing {filename}: {e}")

    return {"final_issues": all_issues}

from langgraph.graph import StateGraph, END

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("reviewer", analyze_code_node)
    
    workflow.set_entry_point("reviewer")
    workflow.add_edge("reviewer", END)
    
    return workflow.compile()
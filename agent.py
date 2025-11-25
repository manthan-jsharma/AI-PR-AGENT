from typing import List, TypedDict
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from models import PRReviewResult, CodeIssue
from github_utils import GitHubConnector
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    repo_name: str
    pr_number: int
    files_to_analyze: List[dict]
    security_issues: List[CodeIssue]
    performance_issues: List[CodeIssue]
    style_issues: List[CodeIssue]
    final_issues: List[CodeIssue]

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        google_api_key=os.environ["GOOGLE_API_KEY"]
    )
    
def security_agent_node(state: AgentState):
    print("Security Agent scanning...")
    llm = get_llm()
    structured_llm = llm.with_structured_output(PRReviewResult)
    found_issues = []

    for file_data in state["files_to_analyze"]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Cyber Security Expert. Analyze this diff for: "
                       "SQL Injection, XSS, Hardcoded Secrets, Insecure Dependencies, and PII exposure. "
                       "Ignore performance or style. "
                       "Return an empty list if code is safe."),
            ("human", "File: {filename}\nPatch:\n{patch}")
        ])
        res = (prompt | structured_llm).invoke({"filename": file_data["filename"], "patch": file_data["patch"]})
        if res.issues:
            for i in res.issues:
                i.file_path = file_data["filename"]
                i.issue_type = "Security" 
                found_issues.append(i)
                
    return {"security_issues": found_issues}


def performance_agent_node(state: AgentState):
    print("Performance Agent scanning...")
    llm = get_llm()
    structured_llm = llm.with_structured_output(PRReviewResult)
    found_issues = []

    for file_data in state["files_to_analyze"]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Scalability Engineer. Analyze this diff for: "
                       "N+1 Queries, Expensive Loops, Memory Leaks, and Unoptimized Data Structures. "
                       "Ignore security or style. "
                       "Return an empty list if efficient."),
            ("human", "File: {filename}\nPatch:\n{patch}")
        ])
        res = (prompt | structured_llm).invoke({"filename": file_data["filename"], "patch": file_data["patch"]})
        if res.issues:
            for i in res.issues:
                i.file_path = file_data["filename"]
                i.issue_type = "Performance"
                found_issues.append(i)
                
    return {"performance_issues": found_issues}

def style_agent_node(state: AgentState):
    print("Style/linting Agent scanning...")
    llm = get_llm()
    structured_llm = llm.with_structured_output(PRReviewResult)
    found_issues = []

    for file_data in state["files_to_analyze"]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Senior Python Developer (PEP8 Expert). Analyze this diff for: "
                       "Naming conventions, missing type hints, messy imports, and readability. "
                       "Only report significant issues. "
                       "Return an empty list if clean."),
            ("human", "File: {filename}\nPatch:\n{patch}")
        ])
        res = (prompt | structured_llm).invoke({"filename": file_data["filename"], "patch": file_data["patch"]})
        if res.issues:
            for i in res.issues:
                i.file_path = file_data["filename"]
                i.issue_type = "Best Practice"
                found_issues.append(i)
                
    return {"style_issues": found_issues}    

def aggregator_node(state: AgentState):
    print("Aggregating results...")

    all_issues = state["security_issues"] + state["performance_issues"] + state["style_issues"]
    return {"final_issues": all_issues}

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("security_scan", security_agent_node)
    workflow.add_node("performance_scan", performance_agent_node)
    workflow.add_node("style_scan", style_agent_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.set_entry_point("security_scan")
    workflow.add_edge("security_scan", "performance_scan")
    workflow.add_edge("performance_scan", "style_scan")
    workflow.add_edge("style_scan", "aggregator")
    workflow.add_edge("aggregator", END)
    
    return workflow.compile()
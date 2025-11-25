from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class CodeIssue(BaseModel):
    file_path: str = Field(description="The full path of the file being reviewed")
    line_number: int = Field(description="The specific line number in the NEW file where the issue exists")
    issue_type: Literal["Security", "Performance", "Best Practice", "Bug"]
    severity: Literal["Critical", "Medium", "Low"]
    description: str = Field(description="A concise explanation of the issue")
    suggestion: str = Field(description="Proposed code fix or actionable advice")

class PRReviewResult(BaseModel):
    issues: List[CodeIssue]
    summary: str = Field(description="A high-level summary of the PR quality")
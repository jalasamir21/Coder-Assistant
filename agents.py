import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain_groq import ChatGroq
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

PROVIDER = os.environ.get("LLM_PROVIDER", "groq")

GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODEL = "gemini-2.5-flash"


def get_llm(temperature: float = 0.2):
    if PROVIDER == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        return ChatGroq(model=GROQ_MODEL, temperature=temperature, api_key=api_key)

    if PROVIDER == "gemini":
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL, temperature=temperature, api_key=api_key
        )

    raise RuntimeError(f"Unknown LLM_PROVIDER: {PROVIDER}")


class TaskCheckResult(BaseModel):
    is_complete: bool = Field(
        description="True if the task has enough information to generate "
        "correct, runnable code without guessing (programming language at minimum)."
    )
    missing_questions: List[str] = Field(
        default_factory=list,
        description="Short, specific questions to ask the user, one per "
        "missing piece of information (e.g. programming language, framework, "
        "input/output format, expected behavior). Empty if is_complete is true.",
    )


def check_task_requirements(task: str) -> TaskCheckResult:
    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(TaskCheckResult)
    system = SystemMessage(
        content=(
            "You are a senior software engineer reviewing a code generation "
            "request before writing any code. Decide if it has enough "
            "information to generate correct code without guessing. The "
            "programming language is always required. Other essential "
            "details depend on the task (framework, input/output format, "
            "expected behavior, edge cases). If anything essential is "
            "missing, mark it incomplete and list short, specific questions, "
            "one per missing piece. If the request is already complete, "
            "return an empty list."
        )
    )
    human = HumanMessage(content=task)
    return structured_llm.invoke([system, human])


def call_code_generation_agent(task: str) -> str:
    llm = get_llm(temperature=0.3)
    system = SystemMessage(
        content=(
            "You are a senior software engineer. Given a task description, "
            "write clean, correct, runnable code that fulfills it. "
            "Return only the code, no explanation, no markdown fences."
        )
    )
    human = HumanMessage(content=task)
    response = llm.invoke([system, human])
    return response.content


def _explain_idea(file_content: str, file_name: str) -> str:
    llm = get_llm(temperature=0.2)
    system = SystemMessage(
        content=(
            "You are a senior software engineer explaining code to another "
            "engineer. Give a concise high-level explanation of what this "
            "file does, its overall design, and the main components. "
            "Do not go line by line here."
        )
    )
    human = HumanMessage(content=f"File: {file_name}\n\n{file_content}")
    response = llm.invoke([system, human])
    return response.content


def _add_line_numbers(file_content: str) -> str:
    lines = file_content.splitlines()
    return "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))


def _explain_line_by_line(file_content: str, file_name: str) -> str:
    llm = get_llm(temperature=0.2)
    system = SystemMessage(
        content=(
            "You are a senior software engineer. Explain this file line by "
            "line, or block by block for closely related lines, referencing "
            "the actual line numbers shown. Be precise and reference the "
            "real code, not a paraphrase."
        )
    )
    numbered_content = _add_line_numbers(file_content)
    human = HumanMessage(content=f"File: {file_name}\n\n{numbered_content}")
    response = llm.invoke([system, human])
    return response.content


def call_code_analysis_agent(file_content: str, file_name: str) -> dict:
    return {
        "idea": _explain_idea(file_content, file_name),
        "line_by_line": _explain_line_by_line(file_content, file_name),
    }


def call_debugging_agent(file_content: str, file_name: str, issue: str) -> str:
    llm = get_llm(temperature=0.2)
    system = SystemMessage(
        content=(
            "You are a senior software engineer debugging code. Given a "
            "file and a description of the issue (which may be empty, "
            "meaning you must find the problem yourself), identify what is "
            "wrong or not done correctly, explain why, and provide the "
            "corrected code."
        )
    )
    issue_text = issue.strip() if issue.strip() else "No issue description provided, find it yourself."
    human = HumanMessage(
        content=f"File: {file_name}\n\nIssue: {issue_text}\n\nCode:\n{file_content}"
    )
    response = llm.invoke([system, human])
    return response.content


def call_qa_agent(feature: str, context: dict, question: str) -> str:
    llm = get_llm(temperature=0.2)
    system = SystemMessage(
        content=(
            "You are a senior software engineer answering a follow-up "
            "question about work you already produced. Use the provided "
            "context and stay grounded in it. Be concise."
        )
    )
    human = HumanMessage(
        content=f"Feature: {feature}\n\nContext: {context}\n\nQuestion: {question}"
    )
    response = llm.invoke([system, human])
    return response.content

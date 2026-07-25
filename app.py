import streamlit as st
from streamlit_option_menu import option_menu
from agents import (
    check_task_requirements,
    call_code_generation_agent,
    call_code_analysis_agent,
    call_debugging_agent,
    call_qa_agent,
)
from theme import (
    inject_global_css,
    agent_panel,
    render_page_header,
    pixel_section_header,
    pixel_label,
    PIXEL_FONT,
    ACCENTS,
    SURFACE,
    SURFACE_ALT,
    BORDER,
    TEXT,
    MUTED,
)
from reports import build_generation_report, build_analysis_report, build_debug_report

st.set_page_config(page_title="Code Multiagent Assistant", layout="wide", page_icon="⌘")
inject_global_css()


def init_state():
    defaults = {
        "gen_output": None,
        "gen_chat": [],
        "gen_stage": "input",
        "gen_original_task": None,
        "gen_questions": [],
        "gen_question_index": 0,
        "gen_answers": [],
        "gen_final_task": None,
        "explain_output": None,
        "explain_chat": [],
        "explain_file_content": None,
        "explain_file_name": None,
        "debug_output": None,
        "debug_chat": [],
        "debug_file_content": None,
        "debug_file_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_chat(feature: str, chat_key: str, context: dict, accent: str):
    pixel_label("ASK ABOUT THIS", color=accent, size="12px")
    for role, message in st.session_state[chat_key]:
        with st.chat_message(role):
            st.markdown(message)

    question = st.chat_input("Ask a question", key=f"{chat_key}_input")
    if question:
        st.session_state[chat_key].append(("user", question))
        try:
            answer = call_qa_agent(feature, context, question)
        except RuntimeError as e:
            answer = f"Error: {e}"
        st.session_state[chat_key].append(("assistant", answer))
        st.rerun()


def _build_augmented_task(original_task: str, questions: list, answers: list) -> str:
    lines = [original_task, "", "Additional details:"]
    for question, answer in zip(questions, answers):
        lines.append(f"- {question}: {answer}")
    return "\n".join(lines)


def render_code_generation():
    accent = ACCENTS["generate"]
    pixel_section_header("GENERATE CODE", accent)
    with agent_panel("generate", "CODE GENERATION"):

        if st.session_state.gen_stage == "input":
            task = st.text_area("Describe the task", height=150, key="gen_task")

            if st.button("Generate", key="gen_button", use_container_width=True):
                if task.strip():
                    try:
                        with st.spinner("Checking requirements..."):
                            check = check_task_requirements(task)
                        if check.is_complete:
                            with st.spinner("Generating..."):
                                st.session_state.gen_output = call_code_generation_agent(task)
                            st.session_state.gen_final_task = task
                            st.session_state.gen_chat = []
                            st.session_state.gen_stage = "output"
                        else:
                            st.session_state.gen_original_task = task
                            st.session_state.gen_questions = check.missing_questions
                            st.session_state.gen_answers = []
                            st.session_state.gen_question_index = 0
                            st.session_state.gen_stage = "questions"
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))
                else:
                    st.warning("Enter a task first.")

        elif st.session_state.gen_stage == "questions":
            questions = st.session_state.gen_questions
            index = st.session_state.gen_question_index
            total = len(questions)

            pixel_label(f"QUESTION {index + 1} OF {total}", color=MUTED, size="11px")
            st.progress(index / total if total else 0)
            st.markdown(
                f"<div style='font-size:16px;color:{TEXT};margin:10px 0 14px;'>{questions[index]}</div>",
                unsafe_allow_html=True,
            )

            answer = st.text_input("Your answer", key=f"gen_answer_{index}")
            button_label = "Finish" if index == total - 1 else "Next"

            if st.button(button_label, key=f"gen_next_{index}", use_container_width=True):
                st.session_state.gen_answers.append(answer)

                if index == total - 1:
                    final_task = _build_augmented_task(
                        st.session_state.gen_original_task,
                        questions,
                        st.session_state.gen_answers,
                    )
                    try:
                        with st.spinner("Generating..."):
                            st.session_state.gen_output = call_code_generation_agent(final_task)
                        st.session_state.gen_final_task = final_task
                        st.session_state.gen_chat = []
                        st.session_state.gen_stage = "output"
                    except RuntimeError as e:
                        st.error(str(e))
                else:
                    st.session_state.gen_question_index += 1

                st.rerun()

        elif st.session_state.gen_stage == "output":
            st.code(st.session_state.gen_output, language="python")

            col_reset, col_download = st.columns(2)
            with col_reset:
                if st.button("Start new task", key="gen_reset", use_container_width=True):
                    st.session_state.gen_stage = "input"
                    st.session_state.gen_output = None
                    st.session_state.gen_chat = []
                    st.rerun()
            with col_download:
                pdf_bytes = build_generation_report(
                    st.session_state.gen_final_task, st.session_state.gen_output
                )
                st.download_button(
                    "Download PDF report",
                    data=pdf_bytes,
                    file_name="code_generation_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            render_chat(
                feature="code_generation",
                chat_key="gen_chat",
                context={"output": st.session_state.gen_output},
                accent=accent,
            )


def render_code_explanation():
    accent = ACCENTS["analyze"]
    pixel_section_header("ANALYZE CODE", accent)
    with agent_panel("analyze", "CODE ANALYSIS"):
        uploaded_file = st.file_uploader(
            "Upload a file to explain", type=None, key="explain_upload"
        )

        if uploaded_file is not None:
            st.session_state.explain_file_content = uploaded_file.read().decode(
                "utf-8", errors="ignore"
            )
            st.session_state.explain_file_name = uploaded_file.name

        if st.session_state.explain_file_content:
            st.code(st.session_state.explain_file_content, language="python")

        if st.button("Explain", key="explain_button", use_container_width=True):
            if st.session_state.explain_file_content:
                try:
                    with st.spinner("Analyzing..."):
                        st.session_state.explain_output = call_code_analysis_agent(
                            st.session_state.explain_file_content,
                            st.session_state.explain_file_name,
                        )
                        st.session_state.explain_chat = []
                except RuntimeError as e:
                    st.error(str(e))
            else:
                st.warning("Upload a file first.")

        if st.session_state.explain_output:
            tab_idea, tab_lines = st.tabs(["Idea", "Line by line"])
            with tab_idea:
                st.write(st.session_state.explain_output["idea"])
            with tab_lines:
                st.write(st.session_state.explain_output["line_by_line"])

            pdf_bytes = build_analysis_report(
                st.session_state.explain_file_name,
                st.session_state.explain_output["idea"],
                st.session_state.explain_output["line_by_line"],
            )
            st.download_button(
                "Download PDF report",
                data=pdf_bytes,
                file_name="code_analysis_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            render_chat(
                feature="code_explanation",
                chat_key="explain_chat",
                context={
                    "file_name": st.session_state.explain_file_name,
                    "file_content": st.session_state.explain_file_content,
                    "output": st.session_state.explain_output,
                },
                accent=accent,
            )


def render_debugging():
    accent = ACCENTS["debug"]
    pixel_section_header("DEBUG CODE", accent)
    with agent_panel("debug", "DEBUGGING"):
        uploaded_file = st.file_uploader(
            "Upload a file to debug", type=None, key="debug_upload"
        )

        if uploaded_file is not None:
            st.session_state.debug_file_content = uploaded_file.read().decode(
                "utf-8", errors="ignore"
            )
            st.session_state.debug_file_name = uploaded_file.name

        if st.session_state.debug_file_content:
            st.code(st.session_state.debug_file_content, language="python")

        issue = st.text_area(
            "Describe the issue (or leave blank to let the agent find it)",
            height=100,
            key="debug_issue",
        )

        if st.button("Debug", key="debug_button", use_container_width=True):
            if st.session_state.debug_file_content:
                try:
                    with st.spinner("Debugging..."):
                        st.session_state.debug_output = call_debugging_agent(
                            st.session_state.debug_file_content,
                            st.session_state.debug_file_name,
                            issue,
                        )
                        st.session_state.debug_chat = []
                except RuntimeError as e:
                    st.error(str(e))
            else:
                st.warning("Upload a file first.")

        if st.session_state.debug_output:
            st.write(st.session_state.debug_output["report"])

            sources = st.session_state.debug_output.get("sources", [])
            if sources:
                pixel_label("RETRIEVED FROM STACK OVERFLOW", color=MUTED, size="10px")
                for source in sources:
                    st.markdown(f"- [{source['title']}]({source['link']})")

            pdf_bytes = build_debug_report(
                st.session_state.debug_file_name,
                st.session_state.debug_issue,
                st.session_state.debug_output["report"],
                sources,
            )
            st.download_button(
                "Download PDF report",
                data=pdf_bytes,
                file_name="debug_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            render_chat(
                feature="debugging",
                chat_key="debug_chat",
                context={
                    "file_name": st.session_state.debug_file_name,
                    "file_content": st.session_state.debug_file_content,
                    "issue": issue,
                    "output": st.session_state.debug_output,
                },
                accent=accent,
            )


FEATURE_TO_AGENT_KEY = {"Generate": "generate", "Analyze": "analyze", "Debug": "debug"}


def main():
    init_state()

    active_feature = st.session_state.get("active_feature", "Generate")
    selected_accent = ACCENTS[FEATURE_TO_AGENT_KEY[active_feature]]

    with st.sidebar:
        st.markdown(
            f"<div style='font-family:{PIXEL_FONT};font-size:15px;line-height:1.6;"
            f"color:{TEXT};margin-bottom:16px;'>CODE<br/>ASSISTANT</div>"
            f"<div style='color:{MUTED};font-size:11px;letter-spacing:1px;"
            f"margin-bottom:10px;'>MENU</div>",
            unsafe_allow_html=True,
        )
        feature = option_menu(
            menu_title=None,
            options=["Generate", "Analyze", "Debug"],
            icons=["magic", "search", "bug"],
            default_index=["Generate", "Analyze", "Debug"].index(active_feature),
            styles={
                "container": {"padding": "0", "background-color": SURFACE},
                "icon": {"font-size": "15px"},
                "nav-link": {
                    "font-family": "JetBrains Mono, monospace",
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "6px 0",
                    "padding": "12px 14px",
                    "border-radius": "8px",
                    "border": f"1px solid {BORDER}",
                    "color": TEXT,
                    "background-color": SURFACE_ALT,
                },
                "nav-link-selected": {
                    "background-color": selected_accent + "1A",
                    "color": selected_accent,
                    "border": f"1px solid {selected_accent}",
                },
            },
        )
        st.session_state.active_feature = feature

    render_page_header(
        "CODE ASSISTANT",
        [
            "Every clean solution starts with the right agent.",
            "Generate, analyze, and debug code with AI agents.",
        ],
        selected_accent,
    )

    if feature == "Generate":
        render_code_generation()
    elif feature == "Analyze":
        render_code_explanation()
    elif feature == "Debug":
        render_debugging()


if __name__ == "__main__":
    main()
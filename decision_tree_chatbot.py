import streamlit as st
import pandas as pd
import os
import io

log_file = "root_cause_log.xlsx"

# --- Simple login page ---
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.title("Welcome to the Root Cause Analysis Chatbot")
    role = st.radio("Are you a user or admin?", ["User", "Admin"])
    if role == "User":
        if st.button("Continue as User"):
            st.session_state.role = "user"
            st.rerun()
    else:
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            # Simple hardcoded credentials (replace with secure method in production)
            if username == "admin" and password == "password123":
                st.session_state.role = "admin"
                st.success("Logged in as admin.")
                st.rerun()
            else:
                st.error("Invalid admin credentials.")
    st.stop()

# --- Admin page ---
if st.session_state.role == "admin":
    st.title("Admin Log Controls")
    if st.button("Reset Logs"):
        if os.path.exists(log_file):
            os.remove(log_file)
            st.success("Root cause logs have been reset.")
        else:
            st.info("No log file to reset.")

    uploaded_file = st.file_uploader("Upload a modified log file", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df.to_excel(log_file, index=False)
        st.success("Log file has been updated with the uploaded file.")

    if os.path.exists(log_file):
        df = pd.read_excel(log_file)
        st.write("Current Log Table:")
        st.dataframe(df)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button(
            "Download Full Log",
            data=excel_buffer,
            file_name="root_cause_log.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    if st.button("Logout"):
        st.session_state.role = None
        st.rerun()
    st.stop()

# Define the decision tree as a dictionary (your current logic under 'Change')
decision_tree = {
    "question": "Was this caused by a standard change?",
    "options": {
        "Yes": {
            "root_cause": "Change Success, Incident Occurred",
            "trigger": "Standard Change",
            "explanation": "A standard change was conducted successfully but there was an incident as a result of the change.",
        },
        "No": {
            "question": "Was the change process followed and the change performed as expected including prechecks?",
            "options": {
                "Yes": {
                    "question": "Was the software developed by LSEG?",
                    "options": {
                        "Yes": {
                            "question": "Was the change rolled back?",
                            "options": {
                                "Yes": {
                                    "root_cause": "Software Failure",
                                    "trigger": "Change",
                                    "secondary_root_cause": "Test plan",
                                    "controllable": "Yes",
                                    "explanation": "The change process was completed successfully but there was an incident as a result of the change.",
                                    "question": "Was the problem considered as P1 or P2?",
                                    "options": {
                                        "P1": "Action: P1 ptask - QA what improvements are required on regression/capacity testing",
                                        "P2": "Action: P2 ptask - QA to provide timelines on when the improvements will be available"
                                    }
                                },
                                "No": {
                                    "root_cause": "Change Failure",
                                    "trigger": "Change",
                                    "secondary_root_cause": "Inadequate Execution",
                                    "controllable": "Yes",
                                    "explanation": "The change process was completed successfully but there was an incident as a result of the change. To resolve the incident the change back out instructions were not followed."
                                }
                            }
                        },
                        "No": {
                            "root_cause": "Third Party Software Failure",
                            "trigger": "Change",
                            "secondary_root_cause": "Version of software was the current version",
                            "controllable": "No",
                            "explanation": "The change process was completed successfully but there was an incident as a result of third-party software."
                        }
                    }
                },
                "No": {
                    "question": "Did the change follow the change process?",
                    "options": {
                        "Yes": {
                            "root_cause": "Change Failure",
                            "trigger": "Change",
                            "secondary_root_cause": "Inadequate Pre or Post-change Checks",
                            "explanation": "The change process was followed but there was inadequate preparation or steps in the change that did not behave as expected."
                        },
                        "No": {
                            "root_cause": "Operating Failure",
                            "trigger": "Change",
                            "secondary_root_cause": "Inadequate Execution",
                            "explanation": "A change was made that did not follow the change process. Usually an unauthorised change."
                        }
                    }
                }
            }
        }
    }
}

# Initialize session state
if "current_node" not in st.session_state:
    st.session_state.current_node = "intro"
if "ticket_number" not in st.session_state:
    st.session_state.ticket_number = ""

def chat_bubble(text, is_bot=True):
    if is_bot:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <img src="https://img.icons8.com/fluency/48/chatbot.png" width="30" style="margin-right: 10px;">
                <div style="position: relative; background-color: #f1f0f0; padding: 10px 15px; border-radius: 10px; max-width: 70%; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);">
                    {text}
                    <div style="position: absolute; top: 10px; left: -10px; width: 0; height: 0; border-top: 10px solid transparent; border-bottom: 10px solid transparent; border-right: 10px solid #f1f0f0;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                <div style="position: relative; background-color: #d1e7dd; padding: 10px 15px; border-radius: 10px; max-width: 70%; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);">
                    {text}
                    <div style="position: absolute; top: 10px; right: -10px; width: 0; height: 0; border-top: 10px solid transparent; border-bottom: 10px solid transparent; border-left: 10px solid #d1e7dd;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_chatbot(node):
    if node == "intro":
        chat_bubble("Hello, I am a RCA bot <br> I will help you find your problem's root cause!<br>Please select your problem category.")
        st.markdown("<br>", unsafe_allow_html=True)
        st.session_state.ticket_number = st.text_input("Enter your problem ticket number:")
        if st.button("Change"):
            st.session_state.current_node = decision_tree
            st.rerun()
        return

    if isinstance(node, dict):
        # If node has root cause details and a follow-up question/options, show both as separate bubbles
        if (
            ("root_cause" in node or "trigger" in node or "secondary_root_cause" in node or "controllable" in node or "explanation" in node)
            and "question" in node and "options" in node
        ):
            details = "Here is the summarization of the root cause<br>"
            if node.get("root_cause"):
                details += f"Primary Root Cause : {node['root_cause']}<br>"
            if node.get("trigger"):
                details += f"Trigger : {node['trigger']}<br>"
            if node.get("secondary_root_cause"):
                details += f"Secondary Root Cause : {node['secondary_root_cause']}<br>"
            if node.get("controllable"):
                details += f"Controllable : {node['controllable']}<br>"
            if node.get("explanation"):
                details += f"Explanation : {node['explanation']}"
            chat_bubble(details)
            st.markdown("<br>", unsafe_allow_html=True)
            # Show follow-up action message for P1/P2 question
            actions_question = "Let me give you some follow up actions for this problem"
            if node.get("question") :
                actions_question +=  {node['question']}
            chat_bubble(actions_question)
            st.markdown("<br>", unsafe_allow_html=True)
            # Now show the follow-up question and options
            chat_bubble(node["question"])
            st.markdown("<br>", unsafe_allow_html=True)
            for option, next_node in node["options"].items():
                if st.button(option):
                    st.session_state.current_node = next_node
                    st.rerun()
            if st.button("Restart"):
                st.session_state.current_node = "intro"
                st.session_state.ticket_number = ""
                st.rerun()
            return

        # Show the question/options if no root cause details
        if "question" in node and "options" in node:
            chat_bubble(node["question"])
            st.markdown("<br>", unsafe_allow_html=True)
            for option, next_node in node["options"].items():
                if st.button(option):
                    st.session_state.current_node = next_node
                    st.rerun()
            if st.button("Restart"):
                st.session_state.current_node = "intro"
                st.session_state.ticket_number = ""
                st.rerun()
            return

        # If no options, show the summary/details and log the result
        if "options" not in node:
            details = "Here is the summarization of the root cause<br>"
            if node.get("root_cause"):
                details += f"Root Cause : {node['root_cause']}<br>"
            if node.get("trigger"):
                details += f"Trigger : {node['trigger']}<br>"
            if node.get("secondary_root_cause"):
                details += f"Secondary Root Cause : {node['secondary_root_cause']}<br>"
            if node.get("controllable"):
                details += f"Controllable : {node['controllable']}<br>"
            if node.get("explanation"):
                details += f"Explanation : {node['explanation']}"
            chat_bubble(details)
            st.markdown("<br>", unsafe_allow_html=True)

            # Log the result
            log_file = "root_cause_log.xlsx"
            log_row = {
                "ticket_number": st.session_state.ticket_number,
                "root_cause": node.get("root_cause", ""),
                "trigger": node.get("trigger", ""),
                "secondary_root_cause": node.get("secondary_root_cause", ""),
                "controllable": node.get("controllable", ""),
                "explanation": node.get("explanation", "")
            }
            if os.path.exists(log_file):
                df = pd.read_excel(log_file)
            else:
                df = pd.DataFrame(columns=log_row.keys())
            df = pd.concat([df, pd.DataFrame([log_row])], ignore_index=True)
            df.to_excel(log_file, index=False)
           
            # Prompt to download log for this ticket number
            st.markdown("**Do you want to know what others achieved for the same ticket number?**")
            filtered_df = df[df["ticket_number"] == st.session_state.ticket_number]
            # Write filtered_df to a BytesIO buffer
            excel_buffer = io.BytesIO()
            filtered_df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            st.download_button(
                "Download log for this ticket number",
                data=excel_buffer,
                file_name=f"root_cause_log_{st.session_state.ticket_number}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            if st.button("Restart"):
                st.session_state.current_node = "intro"
                st.session_state.ticket_number = ""
                st.rerun()
            return

    # If node is a string (leaf action)
    chat_bubble(node)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Restart"):
        st.session_state.current_node = "intro"
        st.session_state.ticket_number = ""
        st.rerun()

# Render the chatbot
st.title("Root Cause Analysis Chatbot")
render_chatbot(st.session_state.current_node)
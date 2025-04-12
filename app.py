import streamlit as st
import time
from typing import Dict, Any, List
from crew import FraudDetectionCrew
from crewai.tasks.task_output import TaskOutput # Correct import path
# from flowchart import AgentFlowchart # Not used with current HTML/JS approach
import json
# from streamlit_lottie import st_lottie # Removing Lottie for now, focusing on CSS
import requests
import datetime # For logging timestamps

# --- Configuration ---
AGENT_NAMES = ["Data Ingestion", "Anomaly Detection", "Risk Assessment", "Investigation", "Decision"]
AGENT_ICONS_HTML = [ # Using Font Awesome icons (ensure internet connection or install locally)
    '<i class="fas fa-database fa-2x"></i>',
    '<i class="fas fa-bolt fa-2x"></i>',
    '<i class="fas fa-shield-alt fa-2x"></i>',
    '<i class="fas fa-search fa-2x"></i>',
    '<i class="fas fa-gavel fa-2x"></i>'
]
AGENT_GOALS = [ # For Tooltips
    "Preprocess and structure the raw transaction data.",
    "Identify unusual patterns or outliers in the data.",
    "Evaluate and score the overall risk level.",
    "Deep dive into transaction details for specific fraud indicators.",
    "Make the final determination: Approve, Flag, or Block."
]

# --- Session State Initialization ---
def init_session_state():
    # Default placeholder values for the form
    default_amount = 100.00
    default_location = "New York"
    default_description = "Sample Item"

    defaults = {
        'processing': False,
        'result': None,
        'decision_shown': False,
        'agent_states': ["pending"] * len(AGENT_NAMES),
        'current_callback_agent_index': 0,
        'dev_mode': False,
        'run_log': [], # To store logs for recap
        # Keys for input widgets
        'amount_input': default_amount,
        'location_input': default_location,
        'description_input': default_description
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- UI Setup ---
st.set_page_config(
    page_title="Guardian Crew",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Developer Mode Toggle ---
st.session_state.dev_mode = st.sidebar.toggle("Developer Mode", value=st.session_state.dev_mode, help="Show detailed logs and raw agent outputs.")
st.sidebar.markdown("---")
st.sidebar.info("This AI system analyzes transactions using a sequence of specialized agents.")

# --- Custom CSS ---
# Font Awesome CDN
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

st.markdown("""
<style>
    /* --- Base & Theme --- */
    .stApp {
        background-color: #1a1a1a; /* Darker background */
        color: #e0e0e0;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .stButton>button { /* More prominent button */
        background-color: #e8494f;
        color: #FFFFFF !important; /* Ensure white text */
        padding: 14px 28px;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background-color: #d7373d;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }
    .stTextInput input, .stNumberInput input {
        background-color: #333333;
        border: 1px solid #444444;
        border-radius: 8px;
        padding: 12px;
        color: white;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
         border-color: #e8494f;
         box-shadow: 0 0 0 2px rgba(232, 73, 79, 0.5);
    }

    /* --- Form & Input Area --- */
    .form-container {
        background-color: #262626;
        padding: 28px;
        border-radius: 16px;
        margin-bottom: 30px;
        border: 1px solid #333333;
    }

    /* --- Agent Flow Visualization --- */
    .agent-flow {
        display: flex;
        justify-content: center; /* Center align nodes */
        align-items: center;
        gap: 20px; /* Increased gap */
        padding: 40px 20px; /* More padding */
        margin: 30px 0;
        background: linear-gradient(145deg, #222222, #181818); /* Subtle gradient */
        border-radius: 16px;
        overflow-x: auto;
        border: 1px solid #333333;
    }

    /* --- Agent Node --- */
    .agent-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 25px;
        background-color: #2d2d2d;
        border-radius: 12px;
        min-width: 180px; /* Slightly wider */
        min-height: 180px; /* Taller */
        justify-content: center; /* Center content vertically */
        transition: all 0.4s ease-in-out;
        position: relative; /* For tooltip */
        border: 2px solid #444444; /* Default border */
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .agent-node:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }

    /* --- Tooltip --- */
    .agent-node .tooltiptext {
        visibility: hidden;
        width: 160px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px 10px;
        position: absolute;
        z-index: 1;
        bottom: 115%; /* Position above the node */
        left: 50%;
        margin-left: -80px; /* Center the tooltip */
        opacity: 0;
        transition: opacity 0.3s, visibility 0.3s;
        font-size: 12px;
    }
    .agent-node:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .agent-node .tooltiptext::after { /* Tooltip arrow */
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #555 transparent transparent transparent;
    }


    @keyframes pulse-glow {
        0% { box-shadow: 0 0 5px #FFB800, 0 0 10px #FFB800; }
        50% { box-shadow: 0 0 15px #FFB800, 0 0 25px #FFB800; }
        100% { box-shadow: 0 0 5px #FFB800, 0 0 10px #FFB800; }
    }

    .agent-node.processing {
        background-color: #3a3a3a;
        border-color: #FFB800; /* Yellow glow for processing */
        animation: pulse-glow 2s infinite ease-in-out;
    }

    .agent-node.completed {
        border-color: #4CAF50; /* Green border for completed */
        background-color: #303d30; /* Subtle green background */
    }

    .agent-icon {
        /* font-size: 32px; - Replaced by FA size */
        margin-bottom: 15px; /* More space */
        color: #aaaaaa; /* Default icon color */
        transition: color 0.3s ease;
    }
    .agent-node.processing .agent-icon { color: #FFB800; }
    .agent-node.completed .agent-icon { color: #4CAF50; }

    .agent-name {
        font-size: 15px; /* Slightly larger */
        font-weight: 600; /* Bolder */
        margin-bottom: 10px;
        color: #ffffff;
    }

    .agent-status {
        font-size: 12px;
        padding: 5px 10px;
        border-radius: 6px;
        background-color: #444444;
        min-width: 80px;
        text-align: center;
        font-weight: 500;
        transition: background-color 0.3s, color 0.3s;
    }
    .status-pending { color: #aaaaaa; background-color: #383838;}
    .status-processing { color: #1a1a1a; background-color: #FFB800; font-weight: 700; }
    .status-completed { color: #ffffff; background-color: #4CAF50; }

    /* --- Arrow Styling --- */
    .arrow {
        color: #555555; /* Darker inactive arrow */
        font-size: 28px; /* Larger arrow */
        margin: 0 20px; /* More spacing */
        transition: color 0.5s ease, text-shadow 0.5s ease;
        position: relative; /* Needed for particle positioning */
        align-self: center; /* Vertically center arrow */
        height: 30px; /* Explicit height */
        line-height: 30px; /* Vertically center glyph */
    }

    .arrow.active {
        color: #4CAF50;
        text-shadow: 0 0 12px #4CAF50, 0 0 20px #4CAF50; /* Enhanced glow */
    }

    /* Data Particle Animation */
    @keyframes dataFlow {
        0% { transform: translateX(-15px) scale(0.7); opacity: 0; background-color: #FFB800; } /* Start yellow */
        20% { transform: translateX(0px) scale(1); opacity: 1; }
        80% { transform: translateX(55px) scale(1); opacity: 1; }
        95% { background-color: #4CAF50; } /* Transition to green */
        100% { transform: translateX(70px) scale(0.7); opacity: 0; }
    }

    .data-particle {
        position: absolute;
        width: 12px; /* Larger particle */
        height: 12px;
        background-color: #4CAF50;
        border-radius: 50%;
        top: 50%;
        left: -6px; /* Adjust start based on size */
        transform: translateY(-50%);
        opacity: 0;
        box-shadow: 0 0 8px #4CAF50;
    }

    .arrow.active .data-particle {
        animation: dataFlow 1.2s ease-in-out forwards; /* Slightly longer */
    }

    /* --- Decision Card --- */
    .decision-card {
        background-color: #2d2d2d;
        border-radius: 12px;
        padding: 25px;
        margin-top: 30px;
        border-left: 6px solid #555555; /* Default border */
        transition: all 0.5s ease-in-out;
        opacity: 0; /* Hidden by default, fade in */
        transform: translateY(10px);
    }
    .decision-card.visible {
        opacity: 1;
        transform: translateY(0);
    }
    .decision-card.approved { border-left-color: #4CAF50; }
    .decision-card.flagged { border-left-color: #FFC107; }
    .decision-card.blocked { border-left-color: #F44336; }
    .decision-card.error { border-left-color: #cccccc; }

    .decision-title {
        font-size: 26px;
        font-weight: 600;
        margin-bottom: 15px;
        color: #ffffff;
    }
    .decision-explanation {
        font-size: 16px;
        color: #cccccc;
        line-height: 1.6;
    }
    .decision-card.approved .decision-title { color: #4CAF50; }
    .decision-card.flagged .decision-title { color: #FFC107; }
    .decision-card.blocked .decision-title { color: #F44336; }
    .decision-card.error .decision-title { color: #cccccc; }

    /* --- Agent Insights / Log Panel --- */
    .log-panel {
        background-color: #262626;
        border-radius: 12px;
        padding: 20px;
        margin-top: 30px;
        border: 1px solid #333333;
        max-height: 400px; /* Limit height */
        overflow-y: auto; /* Enable scrolling */
    }
    .log-entry {
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px dashed #444;
        color: #b0b0b0;
        line-height: 1.4;
    }
    .log-entry:last-child {
        border-bottom: none;
    }
    .log-entry strong {
        color: #e0e0e0;
        font-weight: 600;
    }
    .log-entry .timestamp {
        color: #888888;
        margin-right: 10px;
        font-size: 11px;
    }
    .log-entry .raw-output {
        background-color: #333;
        padding: 5px 8px;
        border-radius: 4px;
        margin-top: 5px;
        display: block;
        white-space: pre-wrap; /* Wrap long lines */
        word-wrap: break-word;
        max-height: 100px; /* Limit raw output display */
        overflow-y: auto;
    }

</style>
""", unsafe_allow_html=True)

# --- UI Sections ---

st.title("🛡️ Guardian Crew")
st.markdown('<p class="description">Multi-agent system analyzing transaction risks in real-time.</p>', unsafe_allow_html=True)

# Transaction input form
with st.container():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    # --- Example Data & Pre-fill Buttons ---
    legitimate_example = {
        "amount": 4.75,
        "location": "San Francisco",
        "description": "Coffee Shop"
    }
    fraud_example = {
        "amount": 242424.00,
        "location": "Unknown", # Fraud often obscures location
        "description": "Luxury Watch Transfer"
    }

    col_btn1, col_btn2, _ = st.columns([1,1,2]) # Layout columns for buttons
    with col_btn1:
        if st.button("Load Legitimate Example", key="load_legit_btn", help="Prefill form with a typical transaction."):
            st.session_state.amount_input = legitimate_example["amount"]
            st.session_state.location_input = legitimate_example["location"]
            st.session_state.description_input = legitimate_example["description"]
            st.rerun() # Rerun to immediately show updated values in inputs
    with col_btn2:
        if st.button("Load Fraud Example", key="load_fraud_btn", help="Prefill form with a suspicious transaction."):
            st.session_state.amount_input = fraud_example["amount"]
            st.session_state.location_input = fraud_example["location"]
            st.session_state.description_input = fraud_example["description"]
            st.rerun() # Rerun to immediately show updated values in inputs

    # --- The Form itself ---
    with st.form("transaction_form", clear_on_submit=False):
        st.subheader("Transaction Details") # Changed header slightly

        col1, col2, col3 = st.columns(3)
        with col1:
            # Use key to link to session state, remove value
            st.number_input(
                "Amount (USD)", 
                min_value=0.0, 
                format="%.2f", 
                key='amount_input' 
            )
        with col2:
            st.text_input(
                "Location", 
                key='location_input'
            )
        with col3:
            st.text_input(
                "Description", 
                key='description_input'
            )

        submitted = st.form_submit_button("Analyze Transaction")

    st.markdown('</div>', unsafe_allow_html=True)

# Agent Flow Display
agent_flow_placeholder = st.empty()

def render_agent_flow(states: List[str]):
    html = '<div class="agent-flow" id="agent-flow">'
    for i in range(len(AGENT_NAMES)):
        node_class = "agent-node"
        status_text = states[i].capitalize()
        status_class = f"status-{states[i]}"
        tooltip_text = AGENT_GOALS[i]
        if states[i] == 'processing':
            node_class += " processing"
        elif states[i] == 'completed':
            node_class += " completed"

        html += f'''
            <div class="{node_class}" id="agent-{i}">
                <div class="agent-icon">{AGENT_ICONS_HTML[i]}</div>
                <div class="agent-name">{AGENT_NAMES[i]}</div>
                <div class="agent-status {status_class}" id="status-{i}">{status_text}</div>
                <span class="tooltiptext">{tooltip_text}</span>
            </div>
        '''
        # Render arrow if not the last node
        if i < len(AGENT_NAMES) - 1:
            arrow_class = "arrow"
            # Arrow active state logic (simplified: active if current node is completed)
            if states[i] == 'completed':
                 arrow_class += " active"
            # NOTE: The logic to start the next agent processing is now handled purely in the callback.
            # We only control the *visual* state of the arrow here.
            html += f'<div class="{arrow_class}" id="arrow-{i}">→<div class="data-particle"></div></div>'

    html += '</div>'
    agent_flow_placeholder.markdown(html, unsafe_allow_html=True)

# Initial render
render_agent_flow(st.session_state.agent_states)

# Decision display placeholder
decision_placeholder = st.empty()

def render_decision(result: Dict[str, Any]):
    if not result:
        decision_placeholder.empty()
        return

    # Safely extract decision and explanation
    raw_decision = result.get("decision", "")
    explanation = result.get("explanation", "No explanation provided.")

    # Determine decision category and class
    decision_text = "Error"
    decision_class = "error"
    if isinstance(raw_decision, str):
        decision_upper = raw_decision.upper()
        if "BLOCK" in decision_upper:
            decision_text = "Blocked"
            decision_class = "blocked"
        elif "FLAG" in decision_upper or "REVIEW" in decision_upper or "NEED" in decision_upper:
            decision_text = "Flagged for Review"
            decision_class = "flagged"
        elif "APPROVE" in decision_upper:
            decision_text = "Approved"
            decision_class = "approved"
        elif "ERROR" in decision_upper:
             decision_text = "Error Processing"
             decision_class = "error"
        else: # Handle unexpected decision string
             decision_text = "Unknown"
             decision_class = "error" # Treat as error visually
             explanation = f"Received unclear decision: {raw_decision}. {explanation}"
    else: # Handle non-string decision (e.g., error object)
        decision_text = "Error Processing"
        decision_class = "error"
        explanation = f"An internal error occurred during decision making. Details: {raw_decision}"


    html = f"""
        <div class="decision-card {decision_class} visible" id="decision-card">
            <div class="decision-title" id="decision-title">Decision: {decision_text}</div>
            <div class="decision-explanation" id="decision-explanation">{explanation}</div>
        </div>
    """
    decision_placeholder.markdown(html, unsafe_allow_html=True)

# Render initial/persistent decision
if st.session_state.decision_shown:
    render_decision(st.session_state.result)

# Agent Insights / Log Panel
log_expander = st.expander("🧠 Agent Insights & Run Log", expanded=False)
log_placeholder = log_expander.empty()

def render_log():
    if not st.session_state.run_log:
        log_placeholder.info("Submit a transaction to see agent activity.")
        return

    log_html = '<div class="log-panel">'
    for entry in st.session_state.run_log:
        log_html += f'<div class="log-entry"><span class="timestamp">[{entry["timestamp"]}]</span> <strong>{entry["agent"]}</strong>: {entry["message"]}'
        # Always show raw output if it exists and the message indicates completion
        if entry.get("raw_output") and "completed" in entry.get("message", "").lower():
             # Basic sanitization for HTML display
             sanitized_output = entry["raw_output"].replace('<', '&lt;').replace('>', '&gt;')
             log_html += f'<div class="raw-output"><strong>Output:</strong><br>{sanitized_output}</div>' # Added label
        log_html += '</div>'
    log_html += '</div>'
    log_placeholder.markdown(log_html, unsafe_allow_html=True)

# Initial log render
render_log()

# --- Callback Function ---
def agent_callback(output: TaskOutput):
    # --- DEBUG REMOVED ---
    # print(f"--- Callback Received ---")
    # print(f"Type: {type(output)}")
    # print(f"Value: {output!r}") # Use repr for detailed view
    # print(f"------------------------")
    # --- END DEBUG --- 

    agent_index = st.session_state.current_callback_agent_index
    timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3] # HH:MM:SS.ms

    # Safely get raw output from TaskOutput
    raw_data = getattr(output, 'raw_output', None) # Try standard raw_output
    if raw_data is None:
        raw_data = getattr(output, 'raw', None)     # Try legacy raw
    if raw_data is None:
        raw_data = str(output)                     # Fallback to string representation

    # Log entry structure
    log_entry = {
        "timestamp": timestamp,
        "agent": "Unknown",
        "message": "Task completed.",
        "raw_output": raw_data # Use the safely retrieved data
    }

    if 0 <= agent_index < len(AGENT_NAMES):
        agent_name = AGENT_NAMES[agent_index]
        log_entry["agent"] = agent_name
        print(f"Callback: Agent '{agent_name}' (Index {agent_index}) task finished.")

        try:
            # Update current agent to completed
            st.session_state.agent_states[agent_index] = "completed"
            log_entry["message"] = "Task successfully completed."

            # Set next agent to processing
            next_agent_index = agent_index + 1
            if next_agent_index < len(AGENT_NAMES):
                 st.session_state.agent_states[next_agent_index] = "processing"
                 st.session_state.current_callback_agent_index = next_agent_index # Increment counter
                 st.session_state.run_log.append(log_entry) # Log completion of current
                 # Log start of next agent
                 st.session_state.run_log.append({
                     "timestamp": datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3],
                     "agent": AGENT_NAMES[next_agent_index],
                     "message": "Starting processing..."
                 })
            else:
                 # Last agent finished
                 st.session_state.current_callback_agent_index = agent_index # Keep counter at last index
                 st.session_state.run_log.append(log_entry) # Log completion of last agent

            # Re-render UI components
            render_agent_flow(st.session_state.agent_states)
            render_log() # Update log panel

        except IndexError:
            print(f"Error: Agent index {agent_index} out of bounds.")
            log_entry["message"] = "Error updating state (index out of bounds)."
            st.session_state.run_log.append(log_entry)
            render_log()
        except Exception as e:
            print(f"Error in agent_callback: {e}")
            log_entry["message"] = f"Error during callback: {e}"
            st.session_state.run_log.append(log_entry)
            render_log()
    else:
        print(f"Error: Invalid agent index {agent_index} in callback.")
        log_entry["message"] = f"Callback received for invalid index {agent_index}."
        st.session_state.run_log.append(log_entry)
        render_log()


# --- Process Transaction ---
if submitted and not st.session_state.processing:
    st.session_state.processing = True
    st.session_state.decision_shown = False
    st.session_state.result = None
    st.session_state.current_callback_agent_index = 0 # Reset callback index
    st.session_state.run_log = [] # Clear log for new run
    # Reset states: first is processing, others pending
    st.session_state.agent_states = ["processing"] + ["pending"] * (len(AGENT_NAMES) - 1)

    # Initial log entry
    st.session_state.run_log.append({
        "timestamp": datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3],
        "agent": AGENT_NAMES[0],
        "message": "Starting processing..."
    })

    render_agent_flow(st.session_state.agent_states) # Initial render with first agent processing
    render_decision(None) # Clear old decision
    render_log() # Show initial log entry

    transaction = {
        "amount": st.session_state.amount_input,
        "location": st.session_state.location_input,
        "description": st.session_state.description_input
    }

    # Log the input transaction based on dev mode
    log_input_msg = "Received transaction."
    if st.session_state.dev_mode:
        log_input_msg += f" Details: {json.dumps(transaction)}"

    st.session_state.run_log.insert(0, { # Insert at the beginning
         "timestamp": datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3],
         "agent": "System",
         "message": log_input_msg
    })
    render_log() # Re-render log with input details

    # Initialize crew with the callback
    crew = FraudDetectionCrew(callback=agent_callback)

    # Call crew.kickoff() directly
    spinner_msg = "🤖 AI Agents are analyzing..."
    with st.spinner(spinner_msg):
        try:
            # The callback handles intermediate UI updates
            crew_output = crew.process_transaction(transaction) # Returns dict: {"decision": JSON_STRING, "transaction": ...}

            # Extract and parse the JSON string from the crew output
            raw_result_str = crew_output.get("decision", "{}") # Default to empty JSON

            # --- Enhanced Cleaning/Extraction ---
            final_decision_word = "ERROR"
            final_rationale = "Error processing final decision output."
            json_str_to_parse = None

            if isinstance(raw_result_str, str):
                # Remove potential markdown fences first
                cleaned_str = raw_result_str.strip().strip('```')
                # Find the first '{' and the last '}'
                start_index = cleaned_str.find('{')
                end_index = cleaned_str.rfind('}')
                
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    # Extract the potential JSON substring
                    json_str_to_parse = cleaned_str[start_index : end_index + 1]
                else:
                    # Could not find valid braces, keep original cleaned string for error reporting
                    json_str_to_parse = cleaned_str 
            else:
                 # If not a string, handle as error
                 json_str_to_parse = str(raw_result_str) # Convert non-string for error logging
                 final_rationale = f"Agent output was not a string: {raw_result_str}"

            # --- Attempt Parsing ---
            if json_str_to_parse:
                try:
                    # Attempt to load the EXTRACTED/CLEANED JSON string
                    parsed_result = json.loads(json_str_to_parse) 
                    final_decision_word = parsed_result.get("decision", "ERROR")
                    final_rationale = parsed_result.get("rationale", "Rationale not provided by agent.")
                except json.JSONDecodeError:
                    # Fallback if the extracted string wasn't valid JSON
                    final_rationale = f"Agent output could not be parsed as JSON after cleaning/extraction: {json_str_to_parse}"
                    # Try to extract decision from raw string as a last resort
                    if isinstance(json_str_to_parse, str):
                        decision_upper = json_str_to_parse.upper()
                        if "BLOCK" in decision_upper: final_decision_word = "Block"
                        elif "FLAG" in decision_upper: final_decision_word = "Flag"
                        elif "APPROVE" in decision_upper: final_decision_word = "Approve"
                        else: final_decision_word = "Unknown" # Could not parse decision
                except Exception as parse_exc:
                    final_rationale = f"Error parsing final decision: {parse_exc}"
            # If json_str_to_parse was None or empty initially, the default error values remain

            # Clean up potential extra quotes or whitespace from LLM output for the decision word
            final_decision_word = final_decision_word.strip().strip('\'"')

            # Store the result for rendering
            st.session_state.result = {
                "decision": final_decision_word, 
                "explanation": final_rationale # Store the extracted rationale
            }
            
            # Ensure final state is rendered correctly after kickoff finishes
            # The callback for the *last* agent should have already set its state to 'completed'.
            # If kickoff returns before last callback finishes (unlikely but possible), force completion.
            if st.session_state.agent_states[-1] != "completed":
                 st.session_state.agent_states = ["completed"] * len(AGENT_NAMES)

            st.session_state.run_log.append({
                "timestamp": datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3],
                "agent": "System",
                "message": f"Processing finished. Final Result: {st.session_state.result.get('decision', 'N/A')}"
            })

        except Exception as e: # Keep except block
            st.error(f"An error occurred during crew processing: {e}")
            # Log the error
            st.session_state.run_log.append({
                "timestamp": datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3],
                "agent": "System",
                "message": f"ERROR during processing: {e}"
            })
            # Optionally render an error state
            st.session_state.result = {"decision": "ERROR", "explanation": str(e)}
            st.session_state.agent_states = ["completed"] * len(AGENT_NAMES) # Mark all as completed on error
        finally: # Keep finally block
            st.session_state.processing = False
            st.session_state.decision_shown = True
            # Final UI updates
            render_agent_flow(st.session_state.agent_states)
            render_decision(st.session_state.result)
            render_log() # Ensure final log is shown

            # ADD Download Button Logic here, after final log render
            if st.session_state.run_log: # Only show button if there's a log
                 log_text = "\\n".join([f'[{e["timestamp"]}] {e["agent"]}: {e["message"]}' + (f'\\nRAW: {e["raw_output"]}\\n' if e.get("raw_output") else '') for e in st.session_state.run_log])
                 st.download_button(
                     label="⬇️ Download Log",
                     data=log_text,
                     file_name=f"fraud_analysis_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                     mime="text/plain",
                     key=f"download_log_button_{st.session_state.get('run_id', 0)}" # Use a potentially unique key if needed, though placement should fix it
                 )
            # st.balloons() # Optional: Add some flair on completion 
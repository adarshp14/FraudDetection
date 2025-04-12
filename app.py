import streamlit as st
import time
from typing import Dict, Any
from crew import FraudDetectionCrew
from crewai.tasks.task_output import TaskOutput # Correct import path
# from flowchart import AgentFlowchart # Not used with current HTML/JS approach
import json
from streamlit_lottie import st_lottie
import requests

# Load Lottie animations
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Animation URLs
ANIMATIONS = {
    "analyzing": "https://assets5.lottiefiles.com/packages/lf20_yyjaansa.json",
    "success": "https://assets5.lottiefiles.com/packages/lf20_yNYxCH.json"
}

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'result' not in st.session_state:
    st.session_state.result = None
if 'current_agent' not in st.session_state:
    st.session_state.current_agent = -1 # Initialize to -1 (none active)
if 'decision_shown' not in st.session_state:
    st.session_state.decision_shown = False
if 'agent_states' not in st.session_state:
    st.session_state.agent_states = ["pending"] * 5 # Keep track of each agent's state
if 'current_callback_agent_index' not in st.session_state: # Add callback index
    st.session_state.current_callback_agent_index = 0

# UI Setup
st.set_page_config(
    page_title="AI Fraud Detection System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for animations and glow effects
st.markdown("""
    <style>
        /* Dark theme base */
        .stApp {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }

        /* Agent node styling */
        .agent-node {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 20px;
            background-color: #2D2D2D;
            border-radius: 12px;
            min-width: 160px;
            transition: all 0.3s ease;
            position: relative;
            border: 2px solid transparent; /* Base border */
        }

        .agent-node.processing {
            background-color: #3D3D3D;
            border-color: #FFB800; /* Yellow glow for processing */
            box-shadow: 0 0 8px #FFB800, 0 0 16px #FFB800;
        }

        .agent-node.completed {
            border-color: #4CAF50; /* Green border for completed */
        }

        .agent-icon {
            font-size: 32px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }

        .agent-name {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
        }

        .agent-status {
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 4px;
            background-color: #383838;
            min-width: 60px; /* Ensure consistent width */
            text-align: center;
        }

        /* Arrow styling */
        .arrow {
            color: #888888;
            font-size: 24px;
            margin: 0 15px;
            transition: color 0.3s ease, text-shadow 0.3s ease;
            position: relative; /* Needed for particle positioning */
        }

        .arrow.active {
            color: #4CAF50;
            text-shadow: 0 0 10px #4CAF50;
        }

        /* Data Particle Animation */
        @keyframes dataFlow {
            0% { transform: translateX(-15px) scale(0.8); opacity: 0; }
            20% { transform: translateX(0px) scale(1); opacity: 1; }
            80% { transform: translateX(40px) scale(1); opacity: 1; }
            100% { transform: translateX(55px) scale(0.8); opacity: 0; }
        }

        .data-particle {
            position: absolute;
            width: 10px;
            height: 10px;
            background-color: #4CAF50;
            border-radius: 50%;
            top: 50%;
            left: -5px; /* Start just before the arrow */
            transform: translateY(-50%);
            opacity: 0;
            box-shadow: 0 0 5px #4CAF50;
        }

        .arrow.active .data-particle {
            animation: dataFlow 1s ease-in-out forwards;
        }

        /* Agent flow container */
        .agent-flow {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            padding: 30px;
            margin: 20px 0;
            background-color: #1A1A1A; /* Slightly darker container */
            border-radius: 16px;
            overflow-x: auto;
        }

        /* Decision card */
        .decision-card {
            background-color: #2D2D2D;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            display: none; /* Hidden by default */
        }

        .decision-card.approved {
            border-left: 4px solid #4CAF50;
        }

        .decision-card.flagged {
            border-left: 4px solid #FFC107;
        }

        .decision-card.blocked {
            border-left: 4px solid #F44336;
        }

        .decision-card.visible {
            display: block;
        }

        .decision-title {
            font-size: 24px;
            font-weight: 500;
            margin-bottom: 10px;
        }

        .decision-explanation {
            font-size: 16px;
            color: #BBBBBB;
        }

        /* Status colors */
        .status-pending { color: #888888; }
        .status-processing { color: #FFB800; }
        .status-completed { color: #4CAF50; }

        /* Form styling */
        .form-container {
            background-color: #2D2D2D;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 30px;
        }

        .stTextInput input, .stNumberInput input {
            background-color: #383838;
            border: none;
            border-radius: 8px;
            padding: 12px;
            color: white;
        }

        .stButton>button {
            background-color: transparent;
            border: 2px solid #FF4B4B;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s;
        }

        .stButton>button:hover {
            background-color: #FF4B4B;
            transform: translateY(-2px);
        }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("AI Fraud Detection System")
st.markdown('<p class="description">This system uses multiple AI agents to analyze transactions and detect potential fraud. The flowchart below shows the real-time progress of the analysis.</p>', unsafe_allow_html=True)

# Transaction input form
with st.container():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    with st.form("transaction_form", clear_on_submit=True):
        st.subheader("Enter Transaction Details")

        col1, col2, col3 = st.columns(3)
        with col1:
            amount = st.number_input("Amount (USD)", min_value=0.0, value=0.0)
        with col2:
            location = st.text_input("Location")
        with col3:
            description = st.text_input("Description")

        submitted = st.form_submit_button("⚠️ Run AI Simulation")
    st.markdown('</div>', unsafe_allow_html=True)

# Agent Flow Display
agent_flow_placeholder = st.empty()
agent_names = ["Data Ingestion", "Anomaly Detection", "Risk Assessment", "Investigation", "Decision"]

def render_agent_flow(states):
    html = '<div class="agent-flow" id="agent-flow">'
    icons = ['👤', '🧠', '📊', '🔍', '⚖️']
    # Use the globally defined agent_names
    for i in range(5):
        node_class = "agent-node"
        status_text = states[i].capitalize()
        status_class = f"status-{states[i]}"
        if states[i] == 'processing':
            node_class += " processing"
        elif states[i] == 'completed':
            node_class += " completed"

        html += f'''
            <div class="{node_class}" id="agent-{i}">
                <div class="agent-icon">{icons[i]}</div>
                <div class="agent-name">{agent_names[i]}</div>
                <div class="agent-status {status_class}" id="status-{i}">{status_text}</div>
            </div>
        '''
        if i < 4:
            arrow_class = "arrow"
            # Arrow active ONLY if the CURRENT agent is completed
            if states[i] == 'completed':
                 arrow_class += " active"
                 # Start next agent processing immediately after current completes
                 if states[i+1] == 'pending':
                      st.session_state.agent_states[i+1] = 'processing'
            html += f'<div class="{arrow_class}" id="arrow-{i}">→<div class="data-particle"></div></div>'

    html += '</div>'
    # Use @st.experimental_fragment or similar if available and needed for smooth updates
    agent_flow_placeholder.markdown(html, unsafe_allow_html=True)

# Initial render
render_agent_flow(st.session_state.agent_states)

# Decision display placeholder
decision_placeholder = st.empty()

def render_decision(result):
    if not result:
        decision_placeholder.empty()
        return

    decision = result.get("decision", "ERROR").upper()
    explanation = result.get("explanation", "No explanation provided.")

    decision_class = "approved"
    if "BLOCK" in decision:
        decision_class = "blocked"
    elif "FLAG" in decision or "REVIEW" in decision or "NEED" in decision:
        decision_class = "flagged"

    html = f"""
        <div class="decision-card {decision_class} visible" id="decision-card">
            <div class="decision-title" id="decision-title">Decision: {decision}</div>
            <div class="decision-explanation" id="decision-explanation">{explanation}</div>
        </div>
    """
    decision_placeholder.markdown(html, unsafe_allow_html=True)

# Render initial/persistent decision
if st.session_state.decision_shown:
    render_decision(st.session_state.result)

# Define the callback function
def agent_callback(output: TaskOutput):
    # Use the counter instead of output.agent
    agent_index = st.session_state.current_callback_agent_index
    agent_name = agent_names[agent_index] # Get name for logging
    print(f"Callback: Agent '{agent_name}' (Index {agent_index}) task finished.")

    try:
        # Update current agent to completed
        st.session_state.agent_states[agent_index] = "completed"
        
        # If not the last agent, set the next agent to processing
        next_agent_index = agent_index + 1
        if next_agent_index < len(agent_names):
             st.session_state.agent_states[next_agent_index] = "processing"
             st.session_state.current_callback_agent_index = next_agent_index # Increment counter
        else:
             st.session_state.current_callback_agent_index = agent_index # Keep counter at last index if last agent

        # Re-render the flow immediately
        render_agent_flow(st.session_state.agent_states)
        # Optionally add a small delay for visual effect if needed
        # time.sleep(0.5)
    except IndexError:
        print(f"Error: Agent index {agent_index} out of bounds.")
    except Exception as e:
        print(f"Error in agent_callback: {e}")

# Process Transaction
if submitted and not st.session_state.processing:
    st.session_state.processing = True
    st.session_state.decision_shown = False
    st.session_state.result = None
    st.session_state.current_callback_agent_index = 0 # Reset callback index
    # Reset states: first is processing, others pending
    st.session_state.agent_states = ["processing"] + ["pending"] * 4
    render_agent_flow(st.session_state.agent_states) # Initial render with first agent processing
    render_decision(None) # Clear old decision

    transaction = {
        "amount": amount,
        "location": location,
        "description": description
    }

    # Initialize crew with the callback
    crew = FraudDetectionCrew(callback=agent_callback)

    # Remove the old simulation loop
    # # Function to update state and re-render
    # def update_state(index, new_status):
    #     if 0 <= index < 5:
    #         st.session_state.agent_states[index] = new_status
    #     render_agent_flow(st.session_state.agent_states)
    #     time.sleep(0.1) # Small delay for UI update

    # # Process transaction with visual updates
    # with st.spinner("Processing transaction..."):
    #     agent_indices = range(5)
    #     for i in agent_indices:
    #         # Start processing the current agent
    #         update_state(i, "processing")
    #         time.sleep(1.0) # Simulate processing time

    #         # Complete processing for the current agent
    #         # This will trigger the arrow *before* the next agent starts
    #         update_state(i, "completed")
    #         if i < 4: # Only pause for transfer if not the last agent
    #             time.sleep(1.0) # Simulate data transfer time (arrow glow + particle)
    #         else:
    #             time.sleep(0.1) # Short delay after final agent completes

    # Call crew.kickoff() directly
    with st.spinner("AI Agents are analyzing the transaction..."):
        try:
            # The callback will handle intermediate UI updates
            result = crew.process_transaction(transaction)
            st.session_state.result = result
            # Ensure final state is rendered correctly after kickoff finishes
            st.session_state.agent_states = ["completed"] * 5
            render_agent_flow(st.session_state.agent_states)
            render_decision(result)
            st.session_state.decision_shown = True
        except Exception as e:
            st.error(f"An error occurred during crew processing: {e}")
            # Optionally render an error state
            st.session_state.result = {"decision": "ERROR", "explanation": str(e)}
            # Ensure final state reflects error, maybe mark all as completed or a specific error state
            st.session_state.agent_states = ["completed"] * 5 # Or a different error representation
            render_agent_flow(st.session_state.agent_states)
            render_decision(st.session_state.result)
            st.session_state.decision_shown = True
        finally:
            st.session_state.processing = False

    # Remove the redundant final render calls as they are handled within try/except
    # render_agent_flow(st.session_state.agent_states)
    # render_decision(st.session_state.result) 
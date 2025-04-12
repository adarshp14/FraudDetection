import streamlit as st
import time
from typing import Dict, Any, List
import json

class AgentFlowchart:
    def __init__(self):
        self.agents = [
            {"id": "ingestion", "icon": "👨‍💻", "name": "Data Ingestion"},
            {"id": "anomaly", "icon": "🧠", "name": "Anomaly Detection"},
            {"id": "risk", "icon": "📊", "name": "Risk Assessment"},
            {"id": "investigation", "icon": "🔍", "name": "Investigation"},
            {"id": "decision", "icon": "👨‍⚖️", "name": "Decision"}
        ]
        self.decisions = {
            "APPROVED": {"icon": "✅", "color": "#4CAF50"},
            "BLOCKED": {"icon": "🛑", "color": "#F44336"},
            "FLAGGED": {"icon": "⚠️", "color": "#FFC107"}
        }
        self.current_agent = None
        self.agent_outputs = {}
        self.agent_status = {agent["id"]: "pending" for agent in self.agents}

    def render_flowchart(self):
        st.markdown("""
        <style>
        .flow-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .agent-node {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px;
            margin: 0 10px;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            min-width: 120px;
        }
        .agent-node.active {
            box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            border: 2px solid #4CAF50;
        }
        .agent-node.completed {
            background: #E8F5E9;
        }
        .agent-icon {
            font-size: 24px;
            margin-bottom: 8px;
        }
        .agent-name {
            font-weight: 500;
            text-align: center;
        }
        .agent-status {
            font-size: 12px;
            margin-top: 5px;
            color: #666;
        }
        .arrow {
            font-size: 20px;
            color: #666;
            margin: 0 5px;
        }
        .arrow.active {
            color: #4CAF50;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .decision-card {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            color: white;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)

        # Render the flow container
        st.markdown('<div class="flow-container">', unsafe_allow_html=True)
        
        # Render agent nodes
        for i, agent in enumerate(self.agents):
            status = self.agent_status[agent["id"]]
            is_active = self.current_agent == agent["id"]
            is_completed = status == "completed"
            
            st.markdown(f"""
            <div class="agent-node {'active' if is_active else 'completed' if is_completed else ''}">
                <div class="agent-icon">{agent['icon']}</div>
                <div class="agent-name">{agent['name']}</div>
                <div class="agent-status">{status.upper()}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show arrow between agents
            if i < len(self.agents) - 1:
                st.markdown(f"""
                <div class="arrow {'active' if is_active else ''}">→</div>
                """, unsafe_allow_html=True)
            
            # Show agent output in expander
            if agent["id"] in self.agent_outputs:
                with st.expander(f"View {agent['name']} Output", expanded=False):
                    st.json(self.agent_outputs[agent["id"]])
        
        st.markdown('</div>', unsafe_allow_html=True)

    def update_agent_status(self, agent_id: str, output: Dict[str, Any]):
        self.current_agent = agent_id
        self.agent_outputs[agent_id] = output
        self.agent_status[agent_id] = "processing"
        self.render_flowchart()
        time.sleep(1)  # Animation delay
        self.agent_status[agent_id] = "completed"
        self.render_flowchart()

    def show_decision(self, decision: str):
        if decision in self.decisions:
            decision_info = self.decisions[decision]
            st.markdown(f"""
            <div class="decision-card" style="background-color: {decision_info['color']};">
                <div style="font-size: 24px;">{decision_info['icon']}</div>
                <div>{decision}</div>
            </div>
            """, unsafe_allow_html=True)

    def reset(self):
        self.current_agent = None
        self.agent_outputs = {}
        self.agent_status = {agent["id"]: "pending" for agent in self.agents}
        self.render_flowchart() 
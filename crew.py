from crewai import Agent, Task, Crew
from crewai.tasks.task_output import TaskOutput
from typing import Dict, Any
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from crewai.process import Process

load_dotenv()

class FraudDetectionCrew:
    def __init__(self, callback=None):
        self.callback = callback
        # Initialize Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7,
            convert_system_message_to_human=True,
            api_version="v1beta"
        )

        # Initialize agents using CrewAI's native implementation with Gemini
        self.data_ingestion_agent = Agent(
            role="Data Preprocessor",
            goal="Transform raw transaction data into LLM-friendly format",
            backstory="Expert in data normalization and feature extraction",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            max_iterations=1
        )

        self.anomaly_detection_agent = Agent(
            role="Anomaly Detector",
            goal="Identify unusual patterns in transactions",
            backstory="Specialized in pattern recognition and outlier detection",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            max_iterations=1
        )

        self.risk_assessment_agent = Agent(
            role="Risk Analyst",
            goal="Evaluate and score transaction risk",
            backstory="Experienced in risk modeling and fraud prevention",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            max_iterations=1
        )

        self.investigation_agent = Agent(
            role="Fraud Investigator",
            goal="Analyze transaction details for fraud indicators",
            backstory="Former financial crime investigator with deep domain knowledge",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            max_iterations=1
        )

        self.decision_agent = Agent(
            role="Decision Maker",
            goal="Make final fraud determination",
            backstory="Senior fraud analyst with authority to approve or block transactions",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            max_iterations=1
        )

    def create_tasks(self, transaction: Dict[str, Any]) -> list[Task]:
        return [
            Task(
                description=f"Preprocess transaction data: {transaction}",
                agent=self.data_ingestion_agent,
                expected_output="Preprocessed transaction data in a structured format",
                callback=self.callback
            ),
            Task(
                description="Analyze for anomalies in the preprocessed data",
                agent=self.anomaly_detection_agent,
                expected_output="List of detected anomalies and their severity",
                callback=self.callback
            ),
            Task(
                description="Calculate risk score and provide justification",
                agent=self.risk_assessment_agent,
                expected_output="Risk score (0-100) with detailed justification",
                callback=self.callback
            ),
            Task(
                description="Investigate transaction details for fraud indicators",
                agent=self.investigation_agent,
                expected_output="Detailed investigation report with fraud indicators",
                callback=self.callback
            ),
            Task(
                description="Make final decision (Approve/Flag/Block) with clear rationale",
                agent=self.decision_agent,
                expected_output="Final decision with detailed rationale",
                callback=self.callback
            )
        ]

    def process_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        tasks = self.create_tasks(transaction)
        crew = Crew(
            agents=[
                self.data_ingestion_agent,
                self.anomaly_detection_agent,
                self.risk_assessment_agent,
                self.investigation_agent,
                self.decision_agent
            ],
            tasks=tasks,
            verbose=True,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return {
            "decision": result,
            "transaction": transaction
        } 
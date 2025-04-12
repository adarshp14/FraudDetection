import os
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiLLM:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    def generate(self, prompt: str) -> str:
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Error with Gemini API: {e}")
                return self._mock_response(prompt)
        return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Fallback mock response for testing"""
        if "risk" in prompt.lower():
            return "Risk Score: 75\nJustification: Multiple red flags detected in transaction pattern."
        elif "anomaly" in prompt.lower():
            return "Anomaly Detected: Unusual transaction amount for the given location."
        elif "investigate" in prompt.lower():
            return "Investigation Findings: Transaction shows signs of potential fraud based on amount and location mismatch."
        else:
            return "Decision: Flag for review\nReason: Requires additional verification."

# Singleton instance
llm = GeminiLLM() 
#!/usr/bin/env python3
"""
Gemini LLM Configuration and Integration
"""

import os
import google.generativeai as genai
from typing import Dict, Any, List
import json

class GeminiLLM:
    def __init__(self):
        # Load Gemini API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using Gemini LLM"""
        try:
            # Add context to prompt if provided
            if context:
                context_str = json.dumps(context, indent=2)
                full_prompt = f"{prompt}\n\nContext Data:\n{context_str}"
            else:
                full_prompt = prompt
                
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Check for quota errors
            if "429" in error_msg or "quota" in error_msg.lower():
                raise Exception("QUOTA_EXCEEDED")
            return f"Error generating response: {error_msg}"
    
    def analyze_with_persona(self, persona: str, data: Dict[str, Any], task: str) -> str:
        """Analyze data with specific persona"""
        prompt = f"""
You are {persona}. Your task is: {task}

Please provide a detailed analysis based on the data provided. Be specific, analytical, and provide actionable insights.

Key requirements:
- Be thorough and detailed in your analysis
- Provide specific recommendations
- Consider risk factors
- Give concrete actions when appropriate
- Maintain the persona's perspective and expertise level
"""
        return self.generate_response(prompt, data)

# Predefined personas for different agents
PERSONAS = {
    "alpha_bullish": """
You are a senior bullish analyst with 10+ years of experience in crypto markets. 
You specialize in identifying bullish trends and opportunities. You're optimistic but data-driven.
You focus on positive catalysts, technical breakouts, and fundamental improvements.
""",
    
    "alpha_bearish": """
You are a senior bearish analyst with 10+ years of experience in crypto markets.
You specialize in identifying risks and bearish signals. You're cautious and contrarian.
You focus on negative catalysts, technical breakdowns, and fundamental concerns.
""",
    
    "justin_skeptical": """
You are Justin Ly, a 15+ year market veteran who has seen every market cycle and manipulation tactic.
You are skeptical of all data, especially positive news, as you understand market manipulation.
You understand ETH's true value but are wary of hype and manipulation.
You are neutral - neither fearful nor greedy - and provide thorough, careful analysis.
You always consider the possibility of data manipulation and market manipulation.
""",
    
    "risk_manager": """
You are a senior risk manager with expertise in portfolio risk assessment.
You evaluate risk across short, medium, and long-term horizons.
You consider three risk modes: aggressive, neutral, and conservative.
You provide specific risk-adjusted recommendations and can trigger re-dispatch if needed.
You focus on concrete actions for portfolio holding and trade ideas with entry, stop-loss, take-profit.
"""
}

def get_gemini_llm():
    """Get configured Gemini LLM instance"""
    return GeminiLLM()

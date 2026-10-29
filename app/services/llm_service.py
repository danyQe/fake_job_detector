import os
import json
import logging
import httpx
from typing import Optional, Dict, Any, List

from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with Language Models (LLMs)
    """
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL_NAME
        self.base_url = "https://api.openai.com/v1"
        
    async def generate_text(self, prompt: str, max_tokens: int = 1500) -> Optional[str]:
        """
        Generate text using the OpenAI API
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a professional resume writer."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.7
                    },
                    timeout=60.0  # Longer timeout for resume generation
                )
                
                if response.status_code != 200:
                    logger.error(f"Error from OpenAI API: {response.text}")
                    return None
                
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return None
    
    async def analyze_job_posting(self, job_description: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a job posting to identify key requirements, skills, and potential red flags
        """
        prompt = f"""
        Analyze this job posting for key requirements, skills needed, and potential red flags:
        
        {job_description}
        
        Format your response as a structured JSON object with these keys:
        - required_skills: array of skills explicitly required for the job
        - preferred_skills: array of skills mentioned as nice-to-have
        - experience_level: string (entry, mid, senior) based on years or responsibilities
        - red_flags: array of potential warning signs like unrealistic requirements, vague descriptions, etc.
        - legitimacy_score: number from 0-100 indicating how legitimate this job appears
        - summary: brief summary of the job and key observations
        """
        
        try:
            result = await self.generate_text(prompt)
            if not result:
                return None
            
            # Parse the JSON from the response
            # The response might include text before/after the JSON, so we need to extract it
            try:
                # Try to parse the whole response as JSON
                analysis = json.loads(result)
            except json.JSONDecodeError:
                # If that fails, try to find JSON within the text
                import re
                json_match = re.search(r'(\{.*\})', result, re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        logger.error(f"Could not parse JSON from LLM response")
                        return None
                else:
                    logger.error(f"No JSON found in LLM response")
                    return None
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing job posting: {str(e)}")
            return None 
import os
import json
import logging
from google import genai
from google.genai import types

class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"
    
    def chat_with_context(self, message, context):
        """
        Chat with Gemini AI using provided context
        
        Args:
            message (str): User message
            context (str): Context from scraped website
        
        Returns:
            str: AI response
        """
        try:
            system_prompt = f"""You are a helpful assistant specializing in job-related content analysis. 
            Use the following context to answer questions accurately and helpfully:

            Context:
            {context}

            Instructions:
            - Provide detailed and accurate answers based on the context
            - If information is not available in the context, say so clearly
            - Format your response in a clear, readable manner
            - For job-related queries, be specific about dates, requirements, and application processes
            """
            
            full_prompt = f"{system_prompt}\n\nUser Question: {message}"
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            
            return response.text if response.text else "I couldn't generate a response. Please try again."
            
        except Exception as e:
            logging.error(f"Error in chat_with_context: {str(e)}")
            return f"Error: {str(e)}"
    
    def find_job_opportunities(self, skills, location="remote"):
        """
        Find job opportunities based on skills using Gemini API
        
        Args:
            skills (list): List of user skills
            location (str): Preferred location
        
        Returns:
            list: List of job opportunities
        """
        try:
            skills_str = ", ".join(skills)
            
            prompt = f"""Find current job openings for someone with the following skills: {skills_str}
            Location preference: {location}
            
            Please provide a list of job opportunities in JSON format with the following structure:
            [
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "location": "Location",
                    "description": "Brief job description",
                    "requirements": "Key requirements",
                    "url": "Application URL (if available)",
                    "skills_required": ["skill1", "skill2", "skill3"],
                    "application_deadline": "Deadline if available"
                }}
            ]
            
            Focus on legitimate, current job postings from reputable companies and job boards.
            Limit to 10 most relevant opportunities.
            """
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            if response.text:
                try:
                    # Try to extract JSON from response
                    json_start = response.text.find('[')
                    json_end = response.text.rfind(']') + 1
                    
                    if json_start != -1 and json_end != 0:
                        json_str = response.text[json_start:json_end]
                        jobs = json.loads(json_str)
                        return jobs
                    else:
                        # If no JSON found, parse the response manually
                        return self._parse_job_response(response.text)
                        
                except json.JSONDecodeError:
                    # If JSON parsing fails, return parsed response
                    return self._parse_job_response(response.text)
            
            return []
            
        except Exception as e:
            logging.error(f"Error finding job opportunities: {str(e)}")
            return []
    
    def _parse_job_response(self, response_text):
        """
        Parse job response text when JSON parsing fails
        """
        jobs = []
        lines = response_text.split('\n')
        current_job = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Title:') or line.startswith('**Title'):
                if current_job:
                    jobs.append(current_job)
                current_job = {'title': line.replace('Title:', '').replace('**', '').strip()}
            elif line.startswith('Company:') or line.startswith('**Company'):
                current_job['company'] = line.replace('Company:', '').replace('**', '').strip()
            elif line.startswith('Location:') or line.startswith('**Location'):
                current_job['location'] = line.replace('Location:', '').replace('**', '').strip()
            elif line.startswith('Description:') or line.startswith('**Description'):
                current_job['description'] = line.replace('Description:', '').replace('**', '').strip()
            elif line.startswith('Requirements:') or line.startswith('**Requirements'):
                current_job['requirements'] = line.replace('Requirements:', '').replace('**', '').strip()
            elif line.startswith('URL:') or line.startswith('**URL'):
                current_job['url'] = line.replace('URL:', '').replace('**', '').strip()
        
        if current_job:
            jobs.append(current_job)
        
        return jobs
    
    def analyze_job_compatibility(self, user_skills, job_description):
        """
        Analyze job compatibility and provide preparation suggestions
        
        Args:
            user_skills (list): List of user skills
            job_description (str): Job description content
        
        Returns:
            dict: Analysis results
        """
        try:
            skills_str = ", ".join(user_skills)
            
            prompt = f"""Analyze the compatibility between the user's skills and the job requirements.

            User Skills: {skills_str}

            Job Description:
            {job_description}

            Please provide a comprehensive analysis in JSON format:
            {{
                "compatibility_percentage": 85,
                "matching_skills": ["skill1", "skill2"],
                "missing_skills": ["skill3", "skill4"],
                "preparation_suggestions": [
                    "Learn skill3 through online courses",
                    "Get certified in skill4",
                    "Practice specific projects"
                ],
                "strengths": ["Your strength1", "Your strength2"],
                "recommendations": "Overall recommendations for the user"
            }}
            """
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            if response.text:
                try:
                    # Try to extract JSON
                    json_start = response.text.find('{')
                    json_end = response.text.rfind('}') + 1
                    
                    if json_start != -1 and json_end != 0:
                        json_str = response.text[json_start:json_end]
                        analysis = json.loads(json_str)
                        return analysis
                        
                except json.JSONDecodeError:
                    pass
            
            # Fallback response
            return {
                "compatibility_percentage": 50,
                "matching_skills": [],
                "missing_skills": [],
                "preparation_suggestions": ["Unable to analyze. Please check the job description."],
                "strengths": [],
                "recommendations": "Please try again with a clearer job description."
            }
            
        except Exception as e:
            logging.error(f"Error analyzing job compatibility: {str(e)}")
            return {
                "compatibility_percentage": 0,
                "matching_skills": [],
                "missing_skills": [],
                "preparation_suggestions": [f"Error: {str(e)}"],
                "strengths": [],
                "recommendations": "An error occurred during analysis."
            }
    
    def extract_skills_from_text(self, text):
        """
        Extract skills from resume text using Gemini AI
        
        Args:
            text (str): Resume text content
        
        Returns:
            list: List of extracted skills
        """
        try:
            prompt = f"""Extract all technical and professional skills from this resume text. Look for:
- Programming languages (Python, Java, JavaScript, etc.)
- Frameworks and libraries (React, Django, Angular, etc.)
- Tools and technologies (Git, Docker, AWS, etc.)
- Databases (MySQL, PostgreSQL, MongoDB, etc.)
- Operating Systems (Windows, Linux, macOS, etc.)
- Software and applications
- Certifications and qualifications
- Professional skills and competencies

Resume Text:
{text}

Return ONLY a simple list of skills, one per line, without any formatting or categories. For example:
Python
JavaScript
React
Docker
AWS
Project Management
Communication

Extract only skills that are explicitly mentioned in the resume text."""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            if response.text:
                # Split response by lines and clean up
                skills = []
                lines = response.text.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    # Remove bullet points, numbers, and other formatting
                    line = line.lstrip('•-*123456789. ')
                    
                    if line and len(line) > 1 and len(line) < 50:  # Reasonable skill name length
                        # Skip common non-skill words
                        skip_words = ['skills', 'experience', 'years', 'proficient', 'familiar', 'knowledge']
                        if not any(skip_word in line.lower() for skip_word in skip_words):
                            skills.append(line)
                
                # Remove duplicates and return
                return list(set(skills))
            
            return []
            
        except Exception as e:
            logging.error(f"Error extracting skills: {str(e)}")
            return []

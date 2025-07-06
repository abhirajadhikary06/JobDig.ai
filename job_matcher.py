import logging
from gemini_client import GeminiClient
import os
from exa_py import Exa

class JobMatcher:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.exa_api_key = os.getenv("EXA_API_KEY")
        self.exa_client = Exa(api_key=self.exa_api_key) if self.exa_api_key else None

    def find_jobs_for_skills(self, skills, location="remote"):
        """
        Find actual job opportunities over the internet not dummy job based on user skills
        Args:
            skills (list): List of user skills
            location (str): Preferred location
        Returns:
            list: List of job opportunities
        """
        try:
            gemini_jobs = self.gemini_client.find_job_opportunities(skills, location)
            exa_jobs = []
            if self.exa_client:
                # Build a query string from skills and location
                query = f"{' '.join(skills)} jobs {location}"
                result = self.exa_client.search_and_contents(query, text=True)
                # Parse Exa results for job links and titles
                for item in result.get('results', []):
                    url = item.get('url')
                    title = item.get('title')
                    snippet = item.get('text') or item.get('snippet')
                    if url and title:
                        exa_jobs.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
            # Combine and deduplicate jobs by URL
            all_jobs = {job['url']: job for job in gemini_jobs + exa_jobs if 'url' in job}
            return list(all_jobs.values())
        except Exception as e:
            logging.error(f"Error finding jobs: {str(e)}")
            return []
    
    def calculate_job_compatibility(self, user_skills, job_skills):
        """
        Calculate compatibility percentage between user skills and job requirements
        
        Args:
            user_skills (list): List of user skills
            job_skills (list): List of job required skills
        
        Returns:
            int: Compatibility percentage
        """
        try:
            if not user_skills or not job_skills:
                return 0
            
            # Convert to lowercase for comparison
            user_skills_lower = [skill.lower() for skill in user_skills]
            job_skills_lower = [skill.lower() for skill in job_skills]
            
            # Find matching skills
            matching_skills = set(user_skills_lower) & set(job_skills_lower)
            
            # Calculate compatibility percentage
            compatibility = int((len(matching_skills) / len(job_skills_lower)) * 100)
            
            return min(compatibility, 100)  # Cap at 100%
            
        except Exception as e:
            logging.error(f"Error calculating compatibility: {str(e)}")
            return 0
    
    def get_skill_recommendations(self, user_skills, job_description):
        """
        Get skill recommendations and preparation suggestions
        
        Args:
            user_skills (list): List of user skills
            job_description (str): Job description content
        
        Returns:
            dict: Recommendations and analysis
        """
        try:
            return self.gemini_client.analyze_job_compatibility(user_skills, job_description)
        except Exception as e:
            logging.error(f"Error getting recommendations: {str(e)}")
            return {
                "compatibility_percentage": 0,
                "matching_skills": [],
                "missing_skills": [],
                "preparation_suggestions": [f"Error: {str(e)}"],
                "strengths": [],
                "recommendations": "An error occurred during analysis."
            }

# Global instance
job_matcher = JobMatcher()

def find_jobs_for_skills(skills, location="remote"):
    """
    Wrapper function for finding jobs
    """
    return job_matcher.find_jobs_for_skills(skills, location)

def calculate_job_compatibility(user_skills, job_skills):
    """
    Wrapper function for calculating compatibility
    """
    return job_matcher.calculate_job_compatibility(user_skills, job_skills)

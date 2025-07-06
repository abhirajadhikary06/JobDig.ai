import logging
from gemini_client import GeminiClient

class JobMatcher:
    def __init__(self):
        self.gemini_client = GeminiClient()
    
    def find_jobs_for_skills(self, skills, location="remote"):
        """
        Find job opportunities based on user skills
        
        Args:
            skills (list): List of user skills
            location (str): Preferred location
        
        Returns:
            list: List of job opportunities
        """
        try:
            return self.gemini_client.find_job_opportunities(skills, location)
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
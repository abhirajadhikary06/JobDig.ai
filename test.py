import logging
from dataclasses import dataclass
from datetime import datetime
import random

# Mock Exa class for testing (replace with `from exa_py import Exa` when using real API)
class MockExa:
    def __init__(self, api_key):
        self.api_key = api_key
    
    @dataclass
    class SearchResult:
        title: str
        author: str
        url: str
        text: str
        published_date: str
    
    @dataclass
    class SearchResponse:
        results: list
    
    def search_and_contents(self, query, text=True, num_results=10, start_published_date=None, end_published_date=None):
        # Mock job listings for testing
        mock_jobs = [
            self.SearchResult(
                title="Senior Machine Learning Engineer (MLOps & Web Deployment)",
                author="Aura Intelligence",
                url="https://example.com/job1",
                text="We are seeking a Senior ML Engineer to design, build, and deploy scalable machine learning systems. This role requires strong software engineering practices, experience with Python, Flask, and Docker.",
                published_date="2025-07-01"
            ),
            self.SearchResult(
                title="Python Backend Developer",
                author="TechCorp",
                url="https://example.com/job2",
                text="Looking for a Python developer with expertise in Django and REST APIs to build scalable web applications.",
                published_date="2025-06-28"
            ),
            self.SearchResult(
                title="Data Scientist",
                author="DataWorks",
                url="https://example.com/job3",
                text="Seeking a Data Scientist proficient in Python, pandas, and scikit-learn for advanced analytics projects.",
                published_date="2025-06-30"
            )
        ]
        return self.SearchResponse(results=random.sample(mock_jobs, min(num_results, len(mock_jobs))))

class JobMatcher:
    def __init__(self):
        # Replace with `self.exa = Exa(api_key="your_api_key_here")` for real API usage
        self.exa = MockExa(api_key="7085169d-7202-498f-8152-3c4c7aac11c4")
    
    def find_jobs_for_skills(self, skills, location="remote"):
        """
        Find job opportunities based on user skills using Exa search
        
        Args:
            skills (list): List of user skills
            location (str): Preferred location, can be 'remote', 'onsite', 'hybrid', or specific location
        
        Returns:
            list: List of verified current job opportunities
        """
        try:
            # Chunk skills to avoid overly long queries
            skill_chunks = [skills[i:i + 3] for i in range(0, len(skills), 3)]
            job_listings = []
            
            for chunk in skill_chunks:
                query = f"current open job opportunities requiring {', '.join(chunk)} "
                query += f"location: {location if location in ['remote', 'onsite', 'hybrid'] else f'{location}, remote, onsite, or hybrid'} "
                query += "posted within last 30 days -inurl:(dummy | test | placeholder) site:*.edu | site:*.org | site:*.gov | site:*.jobs | site:*.com"
                
                result = self.exa.search_and_contents(
                    query,
                    text=True,
                    num_results=10,
                    start_published_date="2025-06-06",
                    end_published_date="2025-07-06"
                )
                
                # Parse Exa results
                for item in result.results:
                    job_info = {
                        "title": item.title,
                        "company": item.author or "Unknown Company",
                        "location": location if location in ['remote', 'onsite', 'hybrid'] else f"{location} (or remote/onsite/hybrid)",
                        "url": item.url,
                        "required_skills": chunk,
                        "posting_date": item.published_date or "Recent",
                        "description": item.text[:500] + "..." if len(item.text) > 500 else item.text
                    }
                    job_listings.append(job_info)
            
            # Calculate compatibility for each job
            for job in job_listings:
                job["compatibility_percentage"] = self.calculate_job_compatibility(skills, job["required_skills"])
            
            # Format output similar to sample
            formatted_jobs = []
            for job in job_listings:
                formatted_job = (
                    f"{job['title']}\n"
                    f"{job['company']}\n"
                    f"{job['location']}\n"
                    f"{job['description']}\n\n"
                    f"Key Requirements\n"
                    f"Expertise in {', '.join(job['required_skills'])}...\n"
                    f"Compatibility: {job['compatibility_percentage']}%\n"
                    f"Apply at: {job['url']}\n"
                )
                formatted_jobs.append(formatted_job)
            
            return formatted_jobs
            
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

# Test the JobMatcher
def main():
    # Sample Python-related skills dictionary
    skills_dict = {
        "Python": ["Python", "Flask", "Django", "pandas", "scikit-learn"],
        "Web Development": ["HTML", "CSS", "JavaScript"],
        "DevOps": ["Docker", "Kubernetes"]
    }
    
    # Combine all skills into a single list
    all_skills = []
    for category, skill_list in skills_dict.items():
        all_skills.extend(skill_list)
    
    # Initialize JobMatcher
    job_matcher = JobMatcher()
    
    # Test with different locations
    locations = ["remote", "onsite", "hybrid", "San Francisco"]
    
    for location in locations:
        print(f"\n=== Testing Job Search for Location: {location} ===\n")
        jobs = job_matcher.find_jobs_for_skills(all_skills, location)
        
        if jobs:
            for job in jobs:
                print(job)
                print("-" * 80)
        else:
            print(f"No jobs found for location: {location}\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
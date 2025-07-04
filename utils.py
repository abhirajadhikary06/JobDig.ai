import re
import markdown
from markupsafe import Markup

def allowed_file(filename):
    """
    Check if uploaded file is allowed (PDF only)
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def validate_job_url(url):
    """
    Validate if URL contains job-related keywords
    """
    job_keywords = [
        "job", "jobs", "career", "careers", "position", "positions",
        "vacancy", "vacancies", "opportunity", "opportunities", "listing",
        "listings", "apply", "recruitment", "employment", "internship",
        "internships", "fellowship", "fellowships", "freelance", "freelances",
        "contract", "contracts", "placement", "placements", "trainee", "trainees"
    ]
    
    url_lower = url.lower()
    return any(keyword in url_lower for keyword in job_keywords)

def parse_llm_response(text):
    """
    Parse LLM response and convert markdown to HTML
    """
    try:
        # Convert markdown to HTML
        html = markdown.markdown(text, extensions=['extra', 'codehilite'])
        
        # Additional parsing for better formatting
        # Handle bold text that might not be in markdown format
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Handle headers that might not be in markdown format
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        return html
        
    except Exception as e:
        # If parsing fails, return original text
        return text

def format_skills_list(skills):
    """
    Format skills list for display
    """
    if not skills:
        return "No skills found"
    
    return ", ".join(skills)

def truncate_text(text, max_length=200):
    """
    Truncate text to specified length
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def calculate_compatibility_color(percentage):
    """
    Get color class based on compatibility percentage
    """
    if percentage >= 80:
        return "success"
    elif percentage >= 60:
        return "warning"
    elif percentage >= 40:
        return "info"
    else:
        return "danger"

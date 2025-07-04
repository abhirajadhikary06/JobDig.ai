import os
import re
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import ScrapeOptions, StartScrapeJobParams, CreateSessionParams
from dotenv import load_dotenv

load_dotenv()

class WebScraper:
    def __init__(self):
        self.client = Hyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))
    
    def scrape_website(self, url, scrape_type='content'):
        """
        Scrape website content or links using HyperBrowser API
        
        Args:
            url (str): Website URL to scrape
            scrape_type (str): 'content' for markdown/html or 'links' for links
        
        Returns:
            str: Scraped data
        """
        try:
            # Ensure URL has protocol
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            
            # Determine scraping format based on type
            if scrape_type == 'content':
                formats = ['markdown', 'html']
            else:
                formats = ['links']
            
            # Start scraping
            scrape_result = self.client.scrape.start_and_wait(
                StartScrapeJobParams(
                    url=url,
                    session_options=CreateSessionParams(
                        accept_cookies=True,
                        use_stealth=True,
                        use_proxy=False,
                        solve_captchas=False,
                    ),
                    scrape_options=ScrapeOptions(
                        formats=formats,
                        only_main_content=True,
                        exclude_tags=[],
                        include_tags=[],
                    ),
                )
            )
            
            # Extract data based on type
            if scrape_type == 'content':
                # Try to get markdown first, then html
                content = getattr(scrape_result, "markdown", None)
                if content is None and hasattr(scrape_result, "data"):
                    content = getattr(scrape_result.data, "markdown", None)
                
                if content is None:
                    content = getattr(scrape_result, "html", None)
                    if content is None and hasattr(scrape_result, "data"):
                        content = getattr(scrape_result.data, "html", None)
                
                return content if content else "No content found"
            
            else:  # links
                links = getattr(scrape_result, "links", None)
                if links is None and hasattr(scrape_result, "data"):
                    links = getattr(scrape_result.data, "links", None)
                
                return str(links) if links else "No links found"
                
        except Exception as e:
            raise Exception(f"Error scraping website: {str(e)}")

# Global instance
scraper = WebScraper()

def scrape_website(url, scrape_type='content'):
    """
    Wrapper function for scraping websites
    """
    return scraper.scrape_website(url, scrape_type)

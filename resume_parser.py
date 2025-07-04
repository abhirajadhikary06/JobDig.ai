import os
import PyPDF2
import logging
from gemini_client import GeminiClient

class ResumeParser:
    def __init__(self):
        self.gemini_client = GeminiClient()
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text content from PDF file
        
        Args:
            pdf_path (str): Path to PDF file
        
        Returns:
            str: Extracted text content
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                
                return text.strip()
                
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_skills_from_text(self, text):
        """
        Extract skills from resume text using Gemini AI
        
        Args:
            text (str): Resume text content
        
        Returns:
            list: List of extracted skills
        """
        try:
            return self.gemini_client.extract_skills_from_text(text)
        except Exception as e:
            logging.error(f"Error extracting skills from text: {str(e)}")
            return []
    
    def parse_resume(self, pdf_path):
        """
        Parse resume PDF and extract skills
        
        Args:
            pdf_path (str): Path to PDF file
        
        Returns:
            tuple: (extracted_text, skills_list)
        """
        try:
            # Extract text from PDF
            extracted_text = self.extract_text_from_pdf(pdf_path)
            
            if not extracted_text:
                raise Exception("No text could be extracted from the PDF")
            
            # Extract skills using Gemini AI
            skills = self.extract_skills_from_text(extracted_text)
            
            return extracted_text, skills
            
        except Exception as e:
            logging.error(f"Error parsing resume: {str(e)}")
            raise Exception(f"Failed to parse resume: {str(e)}")

# Global instance
resume_parser = ResumeParser()

def extract_skills_from_resume(pdf_path):
    """
    Wrapper function for extracting skills from resume
    """
    return resume_parser.parse_resume(pdf_path)

import PyPDF2
import re
from typing import Dict, Any, List, Optional
import io

class PDFParser:
    def __init__(self):
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})'
        self.linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9-]+'
        
    def parse_pdf(self, pdf_file: bytes) -> Dict[str, Any]:
        """Parse a PDF resume and extract structured data"""
        try:
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Parse the extracted text
            return self._parse_text(text)
            
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")
    
    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse extracted text and structure the data"""
        # Split text into lines
        lines = text.split('\n')
        
        # Initialize result dictionary
        result = {
            "fullName": "",
            "title": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": []
        }
        
        # Extract contact information
        for line in lines:
            # Look for email
            email_match = re.search(self.email_pattern, line.lower())
            if email_match:
                result["email"] = email_match.group(0)
            
            # Look for phone
            phone_match = re.search(self.phone_pattern, line)
            if phone_match:
                result["phone"] = phone_match.group(0)
            
            # Look for LinkedIn
            linkedin_match = re.search(self.linkedin_pattern, line.lower())
            if linkedin_match:
                result["linkedin"] = linkedin_match.group(0)
        
        # Extract name (usually first line)
        if lines:
            result["fullName"] = lines[0].strip()
        
        # Extract title (usually second line)
        if len(lines) > 1:
            result["title"] = lines[1].strip()
        
        # Extract location (usually after contact info)
        for line in lines:
            if re.search(r'[A-Z][a-zA-Z\s]+,\s*[A-Z]{2}', line):
                result["location"] = line.strip()
                break
        
        # Extract sections
        current_section = None
        section_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if line.upper() in ["PROFESSIONAL SUMMARY", "SUMMARY", "OBJECTIVE"]:
                current_section = "summary"
                section_text = []
            elif line.upper() in ["SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES"]:
                current_section = "skills"
                section_text = []
            elif line.upper() in ["EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE"]:
                current_section = "experience"
                section_text = []
            elif line.upper() in ["EDUCATION", "ACADEMIC BACKGROUND"]:
                current_section = "education"
                section_text = []
            elif line.upper() in ["CERTIFICATIONS", "PROFESSIONAL CERTIFICATIONS"]:
                current_section = "certifications"
                section_text = []
            else:
                if current_section:
                    section_text.append(line)
        
        # Process extracted sections
        if current_section == "summary":
            result["summary"] = " ".join(section_text)
        elif current_section == "skills":
            result["skills"] = self._extract_skills(section_text)
        elif current_section == "experience":
            result["experience"] = self._extract_experience(section_text)
        elif current_section == "education":
            result["education"] = self._extract_education(section_text)
        elif current_section == "certifications":
            result["certifications"] = self._extract_certifications(section_text)
        
        return result
    
    def _extract_skills(self, lines: List[str]) -> List[str]:
        """Extract skills from text lines"""
        skills = []
        for line in lines:
            # Split by common delimiters
            line_skills = re.split(r'[,|•]', line)
            for skill in line_skills:
                skill = skill.strip()
                if skill and len(skill) > 1:  # Avoid single characters
                    skills.append(skill)
        return list(set(skills))  # Remove duplicates
    
    def _extract_experience(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract work experience from text lines"""
        experiences = []
        current_exp = {}
        
        for line in lines:
            # Look for company and title pattern
            if re.match(r'^[A-Z][a-zA-Z\s&]+[-–]\s*[A-Z][a-zA-Z\s&]+$', line):
                if current_exp:
                    experiences.append(current_exp)
                current_exp = {
                    "company": line.split('[-–]')[0].strip(),
                    "title": line.split('[-–]')[1].strip(),
                    "startDate": "",
                    "endDate": "",
                    "current": False,
                    "description": ""
                }
            elif current_exp:
                # Look for date range
                date_match = re.search(r'(\d{1,2}/\d{4}|\w+\s+\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|\w+\s+\d{4}|Present)', line)
                if date_match:
                    current_exp["startDate"] = date_match.group(1)
                    current_exp["endDate"] = date_match.group(2)
                    current_exp["current"] = date_match.group(2).lower() == "present"
                else:
                    current_exp["description"] += line + "\n"
        
        if current_exp:
            experiences.append(current_exp)
        
        return experiences
    
    def _extract_education(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract education from text lines"""
        education = []
        current_edu = {}
        
        for line in lines:
            # Look for institution and degree pattern
            if re.match(r'^[A-Z][a-zA-Z\s&]+[-–]\s*[A-Z][a-zA-Z\s&]+$', line):
                if current_edu:
                    education.append(current_edu)
                current_edu = {
                    "institution": line.split('[-–]')[0].strip(),
                    "degree": line.split('[-–]')[1].strip(),
                    "field": "",
                    "graduationDate": ""
                }
            elif current_edu:
                # Look for graduation date
                date_match = re.search(r'(\d{4})', line)
                if date_match:
                    current_edu["graduationDate"] = date_match.group(1)
                else:
                    current_edu["field"] = line.strip()
        
        if current_edu:
            education.append(current_edu)
        
        return education
    
    def _extract_certifications(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract certifications from text lines"""
        certifications = []
        
        for line in lines:
            # Look for certification pattern
            if re.match(r'^[A-Z][a-zA-Z\s&]+[-–]\s*[A-Z][a-zA-Z\s&]+$', line):
                cert = {
                    "name": line.split('[-–]')[0].strip(),
                    "issuer": line.split('[-–]')[1].strip()
                }
                certifications.append(cert)
        
        return certifications 
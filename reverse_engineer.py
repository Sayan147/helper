"""
Reverse Engineering Engine
Generates Technical Design Document from code
Generates Business Requirement Document from design
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional

# Try to import LLM utilities from the existing codebase
try:
    # Try relative import first
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../new_sdlc/backend'))
    from app.utils.llm import call_llm  # type: ignore
except (ImportError, ModuleNotFoundError):
    # Fallback to a simple mock if LLM utilities are not available
    def call_llm(prompt: str) -> str:
        return f"[LLM Response for: {prompt[:100]}...]"


class ReverseEngineer:
    """Reverse engineers code to create design and requirements documents"""

    def __init__(
        self,
        config: Dict[str, Any],
        breakdown_strategy: Dict[str, Any],
        background: Optional[str] = None,
        executive_summary: Optional[str] = None
    ):
        self.config = config
        self.breakdown_strategy = breakdown_strategy
        self.background = background or ""
        self.executive_summary = executive_summary or ""

    def generate_design(self, parsed_code: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Technical Design Document from parsed code
        
        Args:
            parsed_code: Dictionary of parsed code files
            
        Returns:
            Technical Design Document structure
        """
        # Build prompt for design generation
        code_summary = self._summarize_code(parsed_code)
        
        prompt = f"""You are a technical architect. Analyze the following code and create a comprehensive Technical Design Document.

Background: {self.background}
Executive Summary: {self.executive_summary}
Project Type: {self.config.get('project_type')}

Code Structure:
{code_summary}

Breakdown Strategy:
{self._format_breakdown_strategy()}

Please generate a Technical Design Document with the following structure:
1. Architecture Overview
2. System Components (break down by the strategy provided)
3. Data Flow
4. Interfaces and APIs
5. Technology Stack
6. Design Patterns Used

For each component/section, provide:
- Purpose and responsibility
- Inputs and outputs
- Dependencies
- Implementation details

Format the response as a structured document with clear sections."""

        # Call LLM to generate design
        design_text = call_llm(prompt)
        
        # Parse design into structured format
        design_doc = self._parse_design_response(design_text, parsed_code)
        
        return design_doc

    def generate_requirements(
        self,
        design_doc: Dict[str, Any],
        parsed_code: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Business Requirement Document from design and code
        
        Args:
            design_doc: Technical Design Document
            parsed_code: Original parsed code
            
        Returns:
            Business Requirement Document structure
        """
        design_summary = self._summarize_design(design_doc)
        code_summary = self._summarize_code(parsed_code)
        
        prompt = f"""You are a Business Analyst. Based on the following Technical Design Document and code, create a comprehensive Business Requirement Document.

Background: {self.background}
Executive Summary: {self.executive_summary}

Technical Design:
{design_summary}

Code Implementation:
{code_summary}

Please generate a Business Requirement Document with:

FUNCTIONAL REQUIREMENTS (FR):
- List each functional requirement as FR1, FR2, FR3, etc.
- Each FR should describe what the system should do
- Include acceptance criteria

NON-FUNCTIONAL REQUIREMENTS (NFR):
- List each non-functional requirement as NFR1, NFR2, NFR3, etc.
- Include performance, security, scalability, maintainability, etc.

For each requirement, provide:
- ID (FR1, FR2, NFR1, etc.)
- Title
- Description
- Priority
- Acceptance Criteria

Format the response clearly with FR and NFR sections."""

        # Call LLM to generate requirements
        requirements_text = call_llm(prompt)
        
        # Parse requirements into structured format
        requirements_doc = self._parse_requirements_response(requirements_text)
        
        return requirements_doc

    def _summarize_code(self, parsed_code: Dict[str, Any]) -> str:
        """Create a summary of parsed code"""
        summary_parts = []
        
        for file_path, code_info in parsed_code.items():
            summary_parts.append(f"\nFile: {file_path}")
            summary_parts.append(f"Language: {code_info.get('language', 'unknown')}")
            summary_parts.append(f"Functions: {len(code_info.get('functions', []))}")
            summary_parts.append(f"Classes: {len(code_info.get('classes', []))}")
            
            # Add function signatures
            for func in code_info.get('functions', [])[:5]:  # Limit to first 5
                summary_parts.append(f"  - {func.get('signature', func.get('name', 'unknown'))}")
            
            if len(code_info.get('functions', [])) > 5:
                summary_parts.append(f"  ... and {len(code_info.get('functions', [])) - 5} more functions")
        
        return '\n'.join(summary_parts)

    def _summarize_design(self, design_doc: Dict[str, Any]) -> str:
        """Create a summary of design document"""
        summary_parts = []
        
        for section in design_doc.get('sections', []):
            summary_parts.append(f"\n{section.get('title', 'Section')}")
            summary_parts.append(section.get('description', '')[:200])
        
        return '\n'.join(summary_parts)

    def _format_breakdown_strategy(self) -> str:
        """Format breakdown strategy for prompt"""
        if isinstance(self.breakdown_strategy, dict):
            return json.dumps(self.breakdown_strategy, indent=2)
        return str(self.breakdown_strategy)

    def _parse_design_response(self, design_text: str, parsed_code: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into structured design document"""
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        sections = []
        
        # Try to extract sections from the response
        lines = design_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a section header
            if line.startswith('#') or (line.isupper() and len(line) < 100):
                if current_section:
                    sections.append({
                        'title': current_section,
                        'description': '\n'.join(current_content),
                        'content': '\n'.join(current_content)
                    })
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                'title': current_section,
                'description': '\n'.join(current_content),
                'content': '\n'.join(current_content)
            })
        
        # If no sections found, create a single section
        if not sections:
            sections.append({
                'title': 'Technical Design',
                'description': design_text[:500],
                'content': design_text
            })
        
        return {
            'sections': sections,
            'raw_text': design_text
        }

    def _parse_requirements_response(self, requirements_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured requirements document"""
        functional_requirements = []
        non_functional_requirements = []
        
        lines = requirements_text.split('\n')
        current_section = None
        current_req = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            if 'FUNCTIONAL REQUIREMENT' in line.upper() or line.upper().startswith('FR'):
                current_section = 'FR'
                # Try to extract FR number
                import re
                match = re.search(r'FR(\d+)', line, re.IGNORECASE)
                if match:
                    fr_id = f"FR{match.group(1)}"
                    if current_req:
                        functional_requirements.append(current_req)
                    current_req = {
                        'id': fr_id,
                        'title': line,
                        'description': '',
                        'content': ''
                    }
            elif 'NON-FUNCTIONAL REQUIREMENT' in line.upper() or line.upper().startswith('NFR'):
                current_section = 'NFR'
                import re
                match = re.search(r'NFR(\d+)', line, re.IGNORECASE)
                if match:
                    nfr_id = f"NFR{match.group(1)}"
                    if current_req:
                        non_functional_requirements.append(current_req)
                    current_req = {
                        'id': nfr_id,
                        'title': line,
                        'description': '',
                        'content': ''
                    }
            elif current_req:
                if current_req.get('description'):
                    current_req['content'] += '\n' + line
                else:
                    current_req['description'] = line
                    current_req['content'] = line
        
        # Add last requirement
        if current_req:
            if current_section == 'FR':
                functional_requirements.append(current_req)
            else:
                non_functional_requirements.append(current_req)
        
        # If parsing failed, create default requirements
        if not functional_requirements and not non_functional_requirements:
            functional_requirements.append({
                'id': 'FR1',
                'title': 'Functional Requirement 1',
                'description': requirements_text[:200],
                'content': requirements_text
            })
        
        return {
            'functional_requirements': functional_requirements,
            'non_functional_requirements': non_functional_requirements,
            'raw_text': requirements_text
        }

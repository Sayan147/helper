"""
Knowledge Base Builder
Creates nested JSON knowledge base with UUIDs and relationships
Uses LLM to determine relationships between sections
"""

import uuid
from typing import Dict, List, Any, Optional
from core.llm_client import get_llm_client
from core.settings import settings


class KnowledgeBaseBuilder:
    """Builds knowledge base with UUIDs and relationships"""
    
    def __init__(self):
        """Initialize knowledge base builder with LLM client"""
        try:
            self.llm_client = get_llm_client()
        except Exception as e:
            print(f"Warning: Could not initialize LLM client: {e}")
            print("Relationship building will be limited. Please set AWS credentials.")
            self.llm_client = None

    def build(
        self,
        context: Dict[str, Any],
        requirements: Dict[str, Any],
        design: Dict[str, Any],
        code: Dict[str, Any],
        test_cases: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Build knowledge base structure with UUIDs and relationships
        
        Args:
            context: Context information (background, executive summary, etc.)
            requirements: Requirements document (FRs and NFRs)
            design: Design document sections
            code: Parsed code sections
            test_cases: Test cases for code sections
            
        Returns:
            Nested JSON knowledge base structure
        """
        kb = {
            'Context': {'sections': []},
            'Requirements': {'FR': [], 'NFR': []},
            'Design': {'sections': []},
            'Code': {'sections': []},
            'Test Case': {'sections': []},
            'Relationship': {
                'Req2Des': [],
                'Req2Code': [],
                'Des2Code': [],
                'Code2TC': [],
                'Req2TC': []
            }
        }
        
        # Build Context sections
        context_sections = self._build_context_sections(context)
        kb['Context']['sections'] = context_sections
        
        # Build Requirements sections
        fr_sections = self._build_fr_sections(requirements.get('functional_requirements', []))
        nfr_sections = self._build_nfr_sections(requirements.get('non_functional_requirements', []))
        kb['Requirements']['FR'] = fr_sections
        kb['Requirements']['NFR'] = nfr_sections
        
        # Build Design sections
        design_sections = self._build_design_sections(design.get('sections', []))
        kb['Design']['sections'] = design_sections
        
        # Build Code sections
        code_sections = self._build_code_sections(code)
        kb['Code']['sections'] = code_sections
        
        # Build Test Case sections
        test_case_sections = self._build_test_case_sections(test_cases)
        kb['Test Case']['sections'] = test_case_sections
        
        # Build Relationships
        relationships = self._build_relationships(
            fr_sections,
            nfr_sections,
            design_sections,
            code_sections,
            test_case_sections
        )
        kb['Relationship'] = relationships
        
        return kb

    def _build_context_sections(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build context sections with UUIDs"""
        sections = []
        
        if context.get('background'):
            sections.append({
                'id': str(uuid.uuid4()),
                'type': 'background',
                'content': context['background'],
                'title': 'Background'
            })
        
        if context.get('executive_summary'):
            sections.append({
                'id': str(uuid.uuid4()),
                'type': 'executive_summary',
                'content': context['executive_summary'],
                'title': 'Executive Summary'
            })
        
        if context.get('project_type'):
            sections.append({
                'id': str(uuid.uuid4()),
                'type': 'project_type',
                'content': context['project_type'],
                'title': 'Project Type'
            })
        
        return sections

    def _build_fr_sections(self, functional_requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build Functional Requirement sections with UUIDs"""
        sections = []
        
        for fr in functional_requirements:
            section = {
                'id': str(uuid.uuid4()),
                'fr_id': fr.get('id', ''),
                'title': fr.get('title', ''),
                'description': fr.get('description', ''),
                'content': fr.get('content', ''),
                'priority': fr.get('priority', 'Medium'),
                'acceptance_criteria': fr.get('acceptance_criteria', '')
            }
            sections.append(section)
        
        return sections

    def _build_nfr_sections(self, non_functional_requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build Non-Functional Requirement sections with UUIDs"""
        sections = []
        
        for nfr in non_functional_requirements:
            section = {
                'id': str(uuid.uuid4()),
                'nfr_id': nfr.get('id', ''),
                'title': nfr.get('title', ''),
                'description': nfr.get('description', ''),
                'content': nfr.get('content', ''),
                'category': nfr.get('category', 'Performance'),
                'acceptance_criteria': nfr.get('acceptance_criteria', '')
            }
            sections.append(section)
        
        return sections

    def _build_design_sections(self, design_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build Design sections with UUIDs"""
        sections = []
        
        for idx, design_section in enumerate(design_sections):
            section = {
                'id': str(uuid.uuid4()),
                'des_id': f"DES{idx + 1}",
                'title': design_section.get('title', f'Design Section {idx + 1}'),
                'description': design_section.get('description', ''),
                'content': design_section.get('content', '')
            }
            sections.append(section)
        
        return sections

    def _build_code_sections(self, code: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build Code sections with UUIDs"""
        sections = []
        code_idx = 1
        
        for file_path, code_info in code.items():
            # Add file-level section
            file_section = {
                'id': str(uuid.uuid4()),
                'code_id': f"CODE{code_idx}",
                'file_path': file_path,
                'language': code_info.get('language', 'unknown'),
                'type': 'file',
                'content': code_info.get('source_code', '')[:500],  # First 500 chars
                'line_count': code_info.get('line_count', 0)
            }
            sections.append(file_section)
            code_idx += 1
            
            # Add function sections
            for func in code_info.get('functions', []):
                func_section = {
                    'id': str(uuid.uuid4()),
                    'code_id': f"CODE{code_idx}",
                    'file_path': file_path,
                    'name': func.get('name', ''),
                    'signature': func.get('signature', ''),
                    'type': 'function',
                    'content': func.get('code', ''),
                    'start_line': func.get('start_line', 0),
                    'end_line': func.get('end_line', 0),
                    'docstring': func.get('docstring', '')
                }
                sections.append(func_section)
                code_idx += 1
            
            # Add class sections
            for cls in code_info.get('classes', []):
                class_section = {
                    'id': str(uuid.uuid4()),
                    'code_id': f"CODE{code_idx}",
                    'file_path': file_path,
                    'name': cls.get('name', ''),
                    'type': 'class',
                    'content': cls.get('code', ''),
                    'start_line': cls.get('start_line', 0),
                    'end_line': cls.get('end_line', 0),
                    'docstring': cls.get('docstring', ''),
                    'methods': [m.get('name', '') for m in cls.get('methods', [])]
                }
                sections.append(class_section)
                code_idx += 1
        
        return sections

    def _build_test_case_sections(self, test_cases: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Build Test Case sections with UUIDs"""
        sections = []
        tc_idx = 1
        
        for file_path, tests in test_cases.items():
            for test in tests:
                section = {
                    'id': str(uuid.uuid4()),
                    'tc_id': test.get('id', f"TC{tc_idx}"),
                    'component': test.get('component', ''),
                    'name': test.get('name', ''),
                    'description': test.get('description', ''),
                    'input_data': test.get('input_data', ''),
                    'expected_output': test.get('expected_output', ''),
                    'test_steps': test.get('test_steps', []),
                    'content': test.get('content', ''),
                    'file_path': file_path
                }
                sections.append(section)
                tc_idx += 1
        
        return sections

    def _build_relationships(
        self,
        fr_sections: List[Dict[str, Any]],
        nfr_sections: List[Dict[str, Any]],
        design_sections: List[Dict[str, Any]],
        code_sections: List[Dict[str, Any]],
        test_case_sections: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build relationships between all components using LLM
        LLM analyzes pairs of sections to determine if they're related
        """
        relationships = {
            'Req2Des': [],
            'Req2Code': [],
            'Des2Code': [],
            'Code2TC': [],
            'Req2TC': []
        }
        
        if not self.llm_client:
            print("Warning: LLM client not available. Using fallback heuristics for relationships.")
            return self._build_relationships_fallback(
                fr_sections, nfr_sections, design_sections, code_sections, test_case_sections
            )
        
        print("Building relationships using LLM...")
        
        # Req2Des: Map requirements to design sections
        print("  Analyzing Requirement -> Design relationships...")
        for fr in fr_sections:
            for design in design_sections:
                if self._are_sections_related_llm(
                    section1=fr,
                    section2=design,
                    relationship_type="Requirement to Design",
                    expected_relation="The requirement is implemented by this design section"
                ):
                    relationships['Req2Des'].append({
                        'requirement_id': fr['id'],
                        'requirement_type': 'FR',
                        'design_id': design['id'],
                        'relationship_type': 'implements'
                    })
        
        for nfr in nfr_sections:
            for design in design_sections:
                if self._are_sections_related_llm(
                    section1=nfr,
                    section2=design,
                    relationship_type="Non-Functional Requirement to Design",
                    expected_relation="The NFR constrains or influences this design section"
                ):
                    relationships['Req2Des'].append({
                        'requirement_id': nfr['id'],
                        'requirement_type': 'NFR',
                        'design_id': design['id'],
                        'relationship_type': 'constrains'
                    })
        
        # Req2Code: Map requirements to code sections
        print("  Analyzing Requirement -> Code relationships...")
        for fr in fr_sections:
            for code in code_sections:
                if code.get('type') in ['function', 'class']:
                    if self._are_sections_related_llm(
                        section1=fr,
                        section2=code,
                        relationship_type="Requirement to Code",
                        expected_relation="The requirement is implemented by this code section"
                    ):
                        relationships['Req2Code'].append({
                            'requirement_id': fr['id'],
                            'requirement_type': 'FR',
                            'code_id': code['id'],
                            'relationship_type': 'implements'
                        })
        
        # Des2Code: Map design sections to code sections
        print("  Analyzing Design -> Code relationships...")
        for design in design_sections:
            for code in code_sections:
                if code.get('type') in ['function', 'class']:
                    if self._are_sections_related_llm(
                        section1=design,
                        section2=code,
                        relationship_type="Design to Code",
                        expected_relation="The design section is realized by this code section"
                    ):
                        relationships['Des2Code'].append({
                            'design_id': design['id'],
                            'code_id': code['id'],
                            'relationship_type': 'realized_by'
                        })
        
        # Code2TC: Map code sections to test cases
        print("  Analyzing Code -> Test Case relationships...")
        for code in code_sections:
            if code.get('type') in ['function', 'class']:
                for tc in test_case_sections:
                    if self._are_sections_related_llm(
                        section1=code,
                        section2=tc,
                        relationship_type="Code to Test Case",
                        expected_relation="The test case tests this code section"
                    ):
                        relationships['Code2TC'].append({
                            'code_id': code['id'],
                            'test_case_id': tc['id'],
                            'relationship_type': 'tested_by'
                        })
        
        # Req2TC: Map requirements to test cases
        print("  Analyzing Requirement -> Test Case relationships...")
        for fr in fr_sections:
            for tc in test_case_sections:
                if self._are_sections_related_llm(
                    section1=fr,
                    section2=tc,
                    relationship_type="Requirement to Test Case",
                    expected_relation="The test case validates this requirement"
                ):
                    relationships['Req2TC'].append({
                        'requirement_id': fr['id'],
                        'requirement_type': 'FR',
                        'test_case_id': tc['id'],
                        'relationship_type': 'validated_by'
                    })
        
        print(f"  Relationships built: {sum(len(v) for v in relationships.values())} total")
        return relationships
    
    def _are_sections_related_llm(
        self,
        section1: Dict[str, Any],
        section2: Dict[str, Any],
        relationship_type: str,
        expected_relation: str
    ) -> bool:
        """
        Use LLM to determine if two sections are related
        
        Args:
            section1: First section
            section2: Second section
            relationship_type: Type of relationship being checked
            expected_relation: Description of expected relationship
            
        Returns:
            True if sections are related, False otherwise
        """
        # Prepare section summaries for LLM
        section1_summary = self._prepare_section_summary(section1)
        section2_summary = self._prepare_section_summary(section2)
        
        prompt = f"""You are analyzing relationships between sections in a software project knowledge base.

Relationship Type: {relationship_type}
Expected Relationship: {expected_relation}

Section 1:
{section1_summary}

Section 2:
{section2_summary}

Based on the content and context of these two sections, determine if they are related in the context of the expected relationship.

Respond with ONLY one word: "YES" if they are related, or "NO" if they are not related.
Do not provide any explanation, just "YES" or "NO"."""
        
        try:
            response = self.llm_client.invoke(
                prompt=prompt,
                temperature=settings.RELATIONSHIP_LLM_TEMPERATURE,
                max_tokens=settings.RELATIONSHIP_LLM_MAX_TOKENS
            )
            
            # Parse response
            response_clean = response.strip().upper()
            return response_clean.startswith("YES")
        
        except Exception as e:
            print(f"    Warning: LLM error for relationship check: {e}")
            # Fallback: return False to avoid false positives
            return False
    
    def _prepare_section_summary(self, section: Dict[str, Any]) -> str:
        """Prepare a concise summary of a section for LLM analysis"""
        parts = []
        
        # Add title/name
        if section.get('title'):
            parts.append(f"Title: {section['title']}")
        elif section.get('name'):
            parts.append(f"Name: {section['name']}")
        elif section.get('fr_id'):
            parts.append(f"ID: {section['fr_id']}")
        elif section.get('nfr_id'):
            parts.append(f"ID: {section['nfr_id']}")
        elif section.get('des_id'):
            parts.append(f"ID: {section['des_id']}")
        elif section.get('code_id'):
            parts.append(f"ID: {section['code_id']}")
        elif section.get('tc_id'):
            parts.append(f"ID: {section['tc_id']}")
        
        # Add description
        if section.get('description'):
            desc = section['description'][:500]  # Limit length
            parts.append(f"Description: {desc}")
        
        # Add content (truncated)
        if section.get('content'):
            content = section['content'][:800]  # Limit length
            parts.append(f"Content: {content}")
        
        # Add signature for code sections
        if section.get('signature'):
            parts.append(f"Signature: {section['signature']}")
        
        # Add type
        if section.get('type'):
            parts.append(f"Type: {section['type']}")
        
        return "\n".join(parts)
    
    def _build_relationships_fallback(
        self,
        fr_sections: List[Dict[str, Any]],
        nfr_sections: List[Dict[str, Any]],
        design_sections: List[Dict[str, Any]],
        code_sections: List[Dict[str, Any]],
        test_case_sections: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fallback relationship building using simple heuristics when LLM is not available"""
        relationships = {
            'Req2Des': [],
            'Req2Code': [],
            'Des2Code': [],
            'Code2TC': [],
            'Req2TC': []
        }
        
        # Simple fallback: map first requirement to first design
        if fr_sections and design_sections:
            relationships['Req2Des'].append({
                'requirement_id': fr_sections[0]['id'],
                'requirement_type': 'FR',
                'design_id': design_sections[0]['id'],
                'relationship_type': 'implements'
            })
        
        # Map code to test cases by name matching
        for code in code_sections:
            if code.get('type') in ['function', 'class']:
                code_name = code.get('name', '')
                for tc in test_case_sections:
                    if code_name and code_name.lower() in tc.get('component', '').lower():
                        relationships['Code2TC'].append({
                            'code_id': code['id'],
                            'test_case_id': tc['id'],
                            'relationship_type': 'tested_by'
                        })
        
        return relationships

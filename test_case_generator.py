"""
Test Case Generator
Generates test cases for code sections
"""

import os
import sys
from typing import Dict, List, Any

# Try to import LLM utilities from the existing codebase
try:
    # Try relative import first
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../new_sdlc/backend'))
    from app.utils.llm import call_llm  # type: ignore
except (ImportError, ModuleNotFoundError):
    # Fallback to a simple mock if LLM utilities are not available
    def call_llm(prompt: str) -> str:
        return f"[LLM Response for: {prompt[:100]}...]"


class TestCaseGenerator:
    """Generates test cases for code sections"""

    def generate_test_cases(
        self,
        parsed_code: Dict[str, Any],
        design_doc: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate test cases for each code section
        
        Args:
            parsed_code: Dictionary of parsed code files
            design_doc: Technical Design Document
            
        Returns:
            Dictionary mapping code section IDs to test cases
        """
        test_cases = {}
        
        for file_path, code_info in parsed_code.items():
            file_test_cases = []
            
            # Generate test cases for functions
            for func in code_info.get('functions', []):
                func_tests = self._generate_function_test_cases(func, design_doc)
                file_test_cases.extend(func_tests)
            
            # Generate test cases for classes
            for cls in code_info.get('classes', []):
                class_tests = self._generate_class_test_cases(cls, design_doc)
                file_test_cases.extend(class_tests)
            
            if file_test_cases:
                test_cases[file_path] = file_test_cases
        
        return test_cases

    def _generate_function_test_cases(
        self,
        func: Dict[str, Any],
        design_doc: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate test cases for a function"""
        func_name = func.get('name', 'unknown')
        func_signature = func.get('signature', '')
        func_code = func.get('code', '')
        func_docstring = func.get('docstring', '')
        
        prompt = f"""Generate comprehensive test cases for the following function.

Function Name: {func_name}
Signature: {func_signature}
Docstring: {func_docstring}
Code:
{func_code[:1000]}  # Limited to first 1000 chars

Please generate test cases covering:
1. Happy path scenarios
2. Edge cases
3. Error handling
4. Boundary conditions
5. Input validation

For each test case, provide:
- Test case ID (TC1, TC2, etc.)
- Test case name
- Description
- Input data
- Expected output
- Test steps

Format as a structured list of test cases."""

        test_cases_text = call_llm(prompt)
        test_cases = self._parse_test_cases(test_cases_text, func_name)
        
        return test_cases

    def _generate_class_test_cases(
        self,
        cls: Dict[str, Any],
        design_doc: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate test cases for a class"""
        class_name = cls.get('name', 'unknown')
        class_code = cls.get('code', '')
        class_docstring = cls.get('docstring', '')
        methods = cls.get('methods', [])
        
        methods_summary = '\n'.join([f"  - {m.get('name', 'unknown')}" for m in methods])
        
        prompt = f"""Generate comprehensive test cases for the following class.

Class Name: {class_name}
Docstring: {class_docstring}
Methods:
{methods_summary}

Code:
{class_code[:1500]}  # Limited to first 1500 chars

Please generate test cases covering:
1. Class instantiation
2. Method behaviors
3. State management
4. Error handling
5. Integration between methods

For each test case, provide:
- Test case ID (TC1, TC2, etc.)
- Test case name
- Description
- Input data
- Expected output
- Test steps

Format as a structured list of test cases."""

        test_cases_text = call_llm(prompt)
        test_cases = self._parse_test_cases(test_cases_text, class_name)
        
        return test_cases

    def _parse_test_cases(
        self,
        test_cases_text: str,
        component_name: str
    ) -> List[Dict[str, Any]]:
        """Parse LLM response into structured test cases"""
        test_cases = []
        
        lines = test_cases_text.split('\n')
        current_test = None
        current_field = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for test case ID
            import re
            match = re.search(r'TC(\d+)', line, re.IGNORECASE)
            if match:
                if current_test:
                    test_cases.append(current_test)
                tc_id = f"TC{match.group(1)}"
                current_test = {
                    'id': tc_id,
                    'component': component_name,
                    'name': '',
                    'description': '',
                    'input_data': '',
                    'expected_output': '',
                    'test_steps': [],
                    'content': line
                }
                current_field = None
            elif current_test:
                # Check for field headers
                if 'name' in line.lower() and ':' in line:
                    current_test['name'] = line.split(':', 1)[1].strip()
                    current_field = 'name'
                elif 'description' in line.lower() and ':' in line:
                    current_test['description'] = line.split(':', 1)[1].strip()
                    current_field = 'description'
                elif 'input' in line.lower() and ':' in line:
                    current_test['input_data'] = line.split(':', 1)[1].strip()
                    current_field = 'input'
                elif 'expected' in line.lower() and ':' in line:
                    current_test['expected_output'] = line.split(':', 1)[1].strip()
                    current_field = 'expected'
                elif 'step' in line.lower():
                    current_field = 'steps'
                elif current_field == 'steps' and (line.startswith('-') or line[0].isdigit()):
                    current_test['test_steps'].append(line.lstrip('- ').lstrip('0123456789. '))
                elif current_field:
                    # Append to current field
                    if current_field == 'description':
                        current_test['description'] += ' ' + line
                    elif current_field == 'input':
                        current_test['input_data'] += ' ' + line
                    elif current_field == 'expected':
                        current_test['expected_output'] += ' ' + line
                else:
                    current_test['content'] += '\n' + line
        
        # Add last test case
        if current_test:
            test_cases.append(current_test)
        
        # If parsing failed, create a default test case
        if not test_cases:
            test_cases.append({
                'id': 'TC1',
                'component': component_name,
                'name': f'Test {component_name}',
                'description': test_cases_text[:200],
                'input_data': 'N/A',
                'expected_output': 'N/A',
                'test_steps': [],
                'content': test_cases_text
            })
        
        return test_cases

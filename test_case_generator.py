"""
Test Case Generator
Generates test cases for code sections
"""

from typing import Dict, List, Any
from core.llm_client import get_llm_client
from core.settings import settings


class TestCaseGenerator:
    """Generates test cases for code sections"""
    
    def __init__(self):
        """Initialize test case generator with LLM client"""
        try:
            self.llm_client = get_llm_client()
        except Exception as e:
            print(f"Warning: Could not initialize LLM client: {e}")
            print("Test case generation will be limited. Please set AWS Bedrock credentials.")
            self.llm_client = None

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
        total_test_cases = 0
        max_total = settings.MAX_TOTAL_TEST_CASES
        
        for file_path, code_info in parsed_code.items():
            file_test_cases = []
            
            # Generate test cases for functions (limited)
            for func in code_info.get('functions', []):
                if total_test_cases >= max_total:
                    print(f"  Reached maximum test case limit ({max_total}). Skipping remaining components.")
                    break
                
                func_tests = self._generate_function_test_cases(func, design_doc)
                # Limit test cases per function
                func_tests = func_tests[:settings.MAX_TEST_CASES_PER_FUNCTION]
                file_test_cases.extend(func_tests)
                total_test_cases += len(func_tests)
            
            if total_test_cases >= max_total:
                break
            
            # Generate test cases for classes (limited)
            for cls in code_info.get('classes', []):
                if total_test_cases >= max_total:
                    print(f"  Reached maximum test case limit ({max_total}). Skipping remaining components.")
                    break
                
                class_tests = self._generate_class_test_cases(cls, design_doc)
                # Limit test cases per class
                class_tests = class_tests[:settings.MAX_TEST_CASES_PER_CLASS]
                file_test_cases.extend(class_tests)
                total_test_cases += len(class_tests)
            
            if file_test_cases:
                test_cases[file_path] = file_test_cases
            
            if total_test_cases >= max_total:
                break
        
        print(f"  Generated {total_test_cases} test cases (limit: {max_total})")
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
        
        max_tests = settings.MAX_TEST_CASES_PER_FUNCTION
        
        prompt = f"""Generate test cases for the following function. Generate EXACTLY {max_tests} test cases (no more, no less).

Function Name: {func_name}
Signature: {func_signature}
Docstring: {func_docstring}
Code:
{func_code[:1000]}  # Limited to first 1000 chars

Generate EXACTLY {max_tests} test cases covering the most important scenarios:
1. Primary happy path scenario (most common use case)
2. One edge case or boundary condition
3. One error handling scenario (if applicable)

For each test case, provide:
- Test case ID (TC1, TC2, TC3, etc.)
- Test case name
- Description
- Input data
- Expected output
- Test steps

IMPORTANT: Generate exactly {max_tests} test cases. Do not generate more than {max_tests} test cases."""

        if not self.llm_client:
            test_cases_text = "[LLM not available - Test case generation requires AWS Bedrock credentials]"
        else:
            test_cases_text = self.llm_client.invoke(prompt)
        test_cases = self._parse_test_cases(test_cases_text, func_name, max_tests=max_tests)
        
        # Ensure we don't exceed the limit
        return test_cases[:max_tests]

    def _generate_class_test_cases(
        self,
        cls: Dict[str, Any],
        design_doc: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate test cases for a class (limited to MAX_TEST_CASES_PER_CLASS)"""
        class_name = cls.get('name', 'unknown')
        class_code = cls.get('code', '')
        class_docstring = cls.get('docstring', '')
        methods = cls.get('methods', [])
        
        methods_summary = '\n'.join([f"  - {m.get('name', 'unknown')}" for m in methods])
        
        max_tests = settings.MAX_TEST_CASES_PER_CLASS
        
        prompt = f"""Generate test cases for the following class. Generate EXACTLY {max_tests} test cases (no more, no less).

Class Name: {class_name}
Docstring: {class_docstring}
Methods:
{methods_summary}

Code:
{class_code[:1500]}  # Limited to first 1500 chars

Generate EXACTLY {max_tests} test cases covering the most important scenarios:
1. Class instantiation (if applicable)
2. Key method behaviors (focus on most important methods)
3. One error handling scenario (if applicable)

For each test case, provide:
- Test case ID (TC1, TC2, TC3, etc.)
- Test case name
- Description
- Input data
- Expected output
- Test steps

IMPORTANT: Generate exactly {max_tests} test cases. Do not generate more than {max_tests} test cases."""

        if not self.llm_client:
            test_cases_text = "[LLM not available - Test case generation requires AWS Bedrock credentials]"
        else:
            test_cases_text = self.llm_client.invoke(prompt)
        test_cases = self._parse_test_cases(test_cases_text, class_name, max_tests=max_tests)
        
        # Ensure we don't exceed the limit
        return test_cases[:max_tests]

    def _parse_test_cases(
        self,
        test_cases_text: str,
        component_name: str,
        max_tests: int = None
    ) -> List[Dict[str, Any]]:
        """Parse LLM response into structured test cases"""
        test_cases = []
        
        lines = test_cases_text.split('\n')
        current_test = None
        current_field = None
        
        # Use provided max_tests or default to function limit
        if max_tests is None:
            max_tests = settings.MAX_TEST_CASES_PER_FUNCTION
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for test case ID
            import re
            match = re.search(r'TC(\d+)', line, re.IGNORECASE)
            if match:
                # Stop if we've reached the limit
                if len(test_cases) >= max_tests:
                    break
                    
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
        
        # Add last test case (if within limit)
        if current_test and len(test_cases) < max_tests:
            test_cases.append(current_test)
        
        # Limit to max_tests (in case LLM generated more)
        test_cases = test_cases[:max_tests]
        
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

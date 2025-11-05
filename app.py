import os
import json
import sys
import requests



# CONFIGURATION CONSTANTS

OLLAMA_HOST = "http://host.docker.internal:11434"
MODEL_NAME = "phi4-mini"
REQUEST_TIMEOUT = 60  # seconds
MAX_RETRIES = 1



# PROMPT TEMPLATES

INITIAL_PROMPT_TEMPLATE = """{query}

Write a Python function that solves this problem. Your function should be errorproof and syntactically correct. 
Return ONLY the function code, nothing else. 
The function should accept one parameter and return a string result. 
Be sure to avoid any extra text beyond the relevant python code in your response."""

RETRY_PROMPT_TEMPLATE = """{query}

The previous code failed with this error: {error}

Previous code was:
{previous_code}

Write a corrected Python function. Return ONLY the function code, nothing else.
The function should accept one parameter and return a string result."""


class LLMCodeTester:
    """Main class for testing LLM-generated code against test cases"""
    
    def __init__(self, ollama_host=OLLAMA_HOST, model_name=MODEL_NAME):
        """Initialize the LLM Code Tester with Ollama connection"""
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.api_url = f"{ollama_host}/api/generate"
    
    def check_ollama_health(self):
        """Verify Ollama is accessible before starting tests"""
        try:
            health_url = f"{self.ollama_host}/api/tags"
            response = requests.get(health_url, timeout=5)
            response.raise_for_status()
            print("Ollama connection verified successfully\n")
            return True
        except Exception as e:
            print(f"ERROR: Cannot connect to Ollama at {self.ollama_host}")
            print(f"Details: {e}")
            print("Please ensure Ollama is running on your host machine.\n")
            return False
    
    def call_ollama_api(self, prompt):
        """Send a request to Ollama API and return the generated response"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.Timeout:
            print(f"ERROR: Request to Ollama timed out after {REQUEST_TIMEOUT} seconds")
            return None
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to call Ollama API: {e}")
            return None
    
    def extract_python_code(self, llm_response):
        """Extract Python code from LLM response (handles markdown formatting)"""
        if not llm_response:
            return ""
        
        # Try to find code between ```python and ```
        if "```python" in llm_response:
            start_marker = "```python"
            start = llm_response.find(start_marker) + len(start_marker)
            end = llm_response.find("```", start)
            if end != -1:
                return llm_response[start:end].strip()
        
        # Try to find code between ``` and ```
        if "```" in llm_response:
            start = llm_response.find("```") + 3
            end = llm_response.find("```", start)
            if end != -1:
                return llm_response[start:end].strip()
        
        # Assume entire response is code
        return llm_response.strip()
    
    def execute_code_safely(self, code, test_input):
        """Execute generated code in isolated namespace and return result"""
        try:
            execution_namespace = {}
            exec(code, execution_namespace)
            
            # Find the first callable function defined in the code
            target_function = None
            for name, obj in execution_namespace.items():
                if callable(obj) and not name.startswith('__'):
                    target_function = obj
                    break
            
            if target_function is None:
                return None, "No callable function found in generated code"
            
            # Execute function with test input
            result = target_function(test_input)
            return str(result), None
            
        except Exception as e:
            return None, str(e)
    
    def generate_and_test_code(self, query, test_input):
        """Generate code from LLM and test it, with retry on failure"""
        # Initial attempt
        prompt = INITIAL_PROMPT_TEMPLATE.format(query=query)
        llm_response = self.call_ollama_api(prompt)
        
        if llm_response is None:
            return None, None, "Failed to get response from LLM"
        
        generated_code = self.extract_python_code(llm_response)
        self._print_generated_code(generated_code, attempt=1)
        
        # Test execution
        result, error = self.execute_code_safely(generated_code, test_input)
        
        # Retry if failed
        if error and MAX_RETRIES > 0:
            print(f"\nExecution Error: {error}")
            print("Retrying with error feedback...\n")
            
            retry_prompt = RETRY_PROMPT_TEMPLATE.format(
                query=query,
                error=error,
                previous_code=generated_code
            )
            
            llm_response = self.call_ollama_api(retry_prompt)
            if llm_response is None:
                return generated_code, None, "Failed to get response from LLM on retry"
            
            generated_code = self.extract_python_code(llm_response)
            self._print_generated_code(generated_code, attempt=2)
            
            result, error = self.execute_code_safely(generated_code, test_input)
        
        return generated_code, result, error
    
    def _print_generated_code(self, code, attempt=1):
        """Pretty print the generated code"""
        attempt_text = f" (Attempt {attempt})" if attempt > 1 else ""
        print(f"\nGenerated Code{attempt_text}:")
        print("-" * 80)
        print(code)
        print("-" * 80)
    
    def process_single_problem(self, problem_name, problem_data):
        """Process and validate a single test case"""
        query = problem_data.get("query")
        test_input = problem_data.get("test_input")
        expected_output = problem_data.get("test_output")
        
        # Validate problem data
        if not all([query, test_input is not None, expected_output is not None]):
            print(f"ERROR: Invalid problem data for {problem_name}\n")
            return
        
        # Print test case info
        self._print_test_header(problem_name, query, test_input, expected_output)
        
        # Generate and test code
        code, actual_output, error = self.generate_and_test_code(query, test_input)
        
        # Print results
        self._print_test_results(actual_output, expected_output, error)
    
    def _print_test_header(self, problem_name, query, test_input, expected_output):
        """Print formatted test case header"""
        print(f"\n{'='*80}")
        print(f"Testing Problem: {problem_name}")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Test Input: {test_input}")
        print(f"Expected Output: {expected_output}")
        print(f"\n{'='*80}")
        print("Calling LLM to generate code...")
    
    def _print_test_results(self, actual_output, expected_output, error):
        """Print formatted test results"""
        if error:
            print(f"\nFinal Error: {error}")
            print("Result: FAILED (Could not execute code)\n")
        elif actual_output == str(expected_output):
            print(f"\nActual Output: {actual_output}")
            print("Result: PASSED ✓\n")
        else:
            print(f"\nActual Output: {actual_output}")
            print(f"Expected Output: {expected_output}")
            print("Result: FAILED (Output mismatch)\n")
    
    def process_json_file(self, file_path):
        """Load and process a JSON file (supports both single and multiple problem formats)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Detect format and process accordingly
            if self._is_single_problem_format(data):
                problem_name = os.path.basename(file_path).replace('.json', '')
                self.process_single_problem(problem_name, data)
            else:
                self._process_multiple_problems(data)
        
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {file_path}: {e}\n")
        except Exception as e:
            print(f"ERROR: Failed to process {file_path}: {e}\n")
    
    def _is_single_problem_format(self, data):
        """Check if JSON follows single problem format"""
        required_keys = {"query", "test_input", "test_output"}
        return required_keys.issubset(data.keys())
    
    def _process_multiple_problems(self, data):
        """Process multiple problems from a single JSON file"""
        for problem_key, problem_data in data.items():
            if isinstance(problem_data, dict):
                self.process_single_problem(problem_key, problem_data)
    
    def run(self, test_cases_directory):
        """Main entry point - discover and process all JSON test files"""
        # Print startup info
        self._print_startup_info(test_cases_directory)
        
        # Verify Ollama connectivity
        if not self.check_ollama_health():
            sys.exit(1)
        
        # Discover JSON files
        json_files = self._discover_json_files(test_cases_directory)
        
        if not json_files:
            print(f"WARNING: No JSON files found in {test_cases_directory}\n")
            return
        
        print(f"Found {len(json_files)} JSON file(s)\n")
        
        # Process each file
        for json_file in sorted(json_files):
            file_path = os.path.join(test_cases_directory, json_file)
            self.process_json_file(file_path)
        
        # Print completion message
        self._print_completion_message()
    
    def _print_startup_info(self, test_cases_directory):
        """Print application startup information"""
        print(f"\nStarting LLM Code Tester")
        print(f"Test Cases Directory: {test_cases_directory}")
        print(f"Using Model: {self.model_name}")
        print(f"Ollama Host: {self.ollama_host}")
    
    def _discover_json_files(self, directory):
        """Find all JSON files in the specified directory"""
        try:
            all_files = os.listdir(directory)
            return [f for f in all_files if f.endswith('.json')]
        except Exception as e:
            print(f"ERROR: Cannot read directory {directory}: {e}")
            return []
    
    def _print_completion_message(self):
        """Print test completion message"""
        print(f"{'='*80}")
        print("All tests completed!")
        print(f"{'='*80}\n")


def main():
    """Application entry point"""
    if len(sys.argv) != 2:
        print("Usage: python app.py <test_cases_directory>")
        print("Example: python app.py /test_cases")
        sys.exit(1)
    
    test_cases_directory = sys.argv[1]
    
    if not os.path.exists(test_cases_directory):
        print(f"ERROR: Directory not found: {test_cases_directory}")
        sys.exit(1)
    
    if not os.path.isdir(test_cases_directory):
        print(f"ERROR: Path is not a directory: {test_cases_directory}")
        sys.exit(1)
    
    # Initialize and run tester
    tester = LLMCodeTester()
    tester.run(test_cases_directory)


if __name__ == "__main__":
    main()
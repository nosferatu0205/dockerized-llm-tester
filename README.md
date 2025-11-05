### Prereqs

Docker ≥ 20.10
Ollama running on host

# Model: phi4-mini

ollama pull phi4-mini
ollama list

### Build and run

git clone <repo-url>
cd dockerized-llm-tester
docker build -t dockerized-llm-tester .
docker run --rm -v /path/to/test_cases:/test_cases dockerized-llm-tester /test_cases

### Test Case example

{
"query": "Check if number is even or odd. Return 'YES' if even, 'NO' if odd",
"test_input": 4,
"test_output": "YES"
}

### Config (app.py)

OLLAMA_HOST = "http://host.docker.internal:11434"
MODEL_NAME = "phi4-mini"

### Project tree

app.py
Dockerfile
test_cases/

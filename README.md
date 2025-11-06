# Prereqs

Docker ≥ 20.10
Ollama running on host

### Model: phi4-mini

ollama pull phi4-mini
ollama list

### Build and Run

**Option 1: Build from Source**
```bash
# Clone repository
git clone https://github.com/nosferatu0205/dockerized-llm-tester.git
cd dockerized-llm-tester

# Build Docker image
docker build -t dockerized-llm-tester .

# Run with your test cases
docker run --rm -v /path/to/test_cases:/test_cases dockerized-llm-tester /test_cases
```

**Option 2: Pull from Docker Hub (No Build Required)**
```bash
# Pull pre-built image
docker pull nosferatu0205/dockerized-llm-tester:latest

# Run with your test cases
docker run --rm -v /path/to/test_cases:/test_cases nosferatu0205/dockerized-llm-tester:latest /test_cases
```

**Windows PowerShell Example:**
```powershell
docker run --rm -v "C:\Users\YourName\test_cases:/test_cases" nosferatu0205/dockerized-llm-tester:latest /test_cases
```

**Linux/Mac Example:**
```bash
docker run --rm -v ~/test_cases:/test_cases nosferatu0205/dockerized-llm-tester:latest /test_cases
```

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

### Pulling from docker:

docker pull nosferatu0205/dockerized-llm-tester:latest

Sample output for single - query objects
<img width="1920" height="755" alt="{2E25248B-F876-47F0-858B-82FC8C5B8BDD}" src="https://github.com/user-attachments/assets/e016faea-a2d4-4e4b-9846-a6df4b6d5aa1" />
<img width="1920" height="493" alt="{97F62CDC-1B83-4126-A141-753D6FCC101B}" src="https://github.com/user-attachments/assets/9a438442-8f41-4944-acb0-2d9db5f305fd" />
<img width="1918" height="477" alt="{9B743D80-EF2A-40A5-86E9-B012E8014B9D}" src="https://github.com/user-attachments/assets/7ab91ad9-2764-4ef3-9c77-9fabc892954a" />

Sample output for json object with multiple queries
<img width="1920" height="875" alt="{79E66E3A-086E-475C-99D9-3863929A43F9}" src="https://github.com/user-attachments/assets/510b8595-0dc9-415d-90b6-769b108ddc89" />



# CivicAI — Smart Civic Issue Assistant

CivicAI is an open-source web application that helps people turn everyday civic problems into structured reports. A citizen describes an issue such as a pothole, overflowing waste, water leak, broken streetlight, or drainage problem. The app uses **Gemma 4 through a local Ollama server** to summarize the report, estimate urgency, and recommend a responsible public department.

If the local model is unavailable, CivicAI switches to a transparent rule-based fallback so the demo remains usable.

## Features

- Plain-language civic issue reporting
- AI-assisted category, urgency, department, summary, and next-step suggestions
- Local Gemma inference through Ollama — no hosted AI API key required
- Rule-based fallback when the model server is unavailable
- SQLite community log and basic report statistics
- Responsive interface for desktop and mobile
- Clear notice that AI suggestions need human review

## Technology

- Python and Flask
- HTML, CSS, JavaScript
- SQLite
- Ollama local inference
- Google Gemma 4 model

## Run locally

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install and start Ollama

Install Ollama from https://ollama.com and start the Ollama service. Then check the Ollama model library for the current Gemma 4 model tag supported by your installation, pull that model, and set the same tag in `GEMMA_MODEL`.

Example:

```bash
ollama pull gemma4
```

If your Ollama library uses a size-specific tag, use that exact tag instead:

```powershell
$env:GEMMA_MODEL="your-installed-gemma4-tag"
```

macOS / Linux:

```bash
export GEMMA_MODEL="your-installed-gemma4-tag"
```

The app defaults to `gemma4`. You can also set `OLLAMA_URL` if your local Ollama server is not at `http://localhost:11434`.

### 4. Start CivicAI

```bash
python app.py
```

Open http://127.0.0.1:5000

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Web application |
| GET | `/api/health` | App and Ollama status |
| POST | `/api/analyze` | Analyze a civic issue description |
| POST | `/api/complaints` | Save an analyzed report |
| GET | `/api/complaints` | List recent saved reports |
| GET | `/api/stats` | Basic report statistics |

Example request:

```bash
curl -X POST http://127.0.0.1:5000/api/analyze \\
  -H "Content-Type: application/json" \\
  -d '{"description":"A large pothole near the public park is creating a danger for two-wheelers."}'
```

## Responsible-use notes

- CivicAI is a prototype, not an official government complaint portal.
- It does not submit reports to a municipality or guarantee that a problem will be fixed.
- Do not enter personal information, exact home addresses, or sensitive details.
- AI urgency and department recommendations are suggestions, not official decisions.
- For emergencies, contact the appropriate local emergency service directly.

## Hackathon prize fit

**Best Use of Gemma 4:** Gemma 4 is the primary language model used to interpret citizen descriptions and generate structured triage suggestions. It returns a category, urgency level, responsible department, neutral summary, and suggested next action.

**Best Open-Source AI Project:** CivicAI combines an open-source Flask application with a locally runnable Gemma model. The project can be inspected, modified, and run locally without depending on a paid hosted AI API.

## Project links

- GitHub: add your repository URL after creating the repository.
- Live demo: add after deployment.
- Demo video: add after recording.

## License

MIT. See [LICENSE](LICENSE).

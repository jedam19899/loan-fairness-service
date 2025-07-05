# FastAPI Loan Fairness Service

A robust microservice for assessing loan fairness metrics, built with FastAPI. This service applies statistical and machine-learning techniques to evaluate loan applications for fairness and bias, ensuring transparent and equitable lending decisions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Architecture & Design](#architecture--design)
4. [Prerequisites](#prerequisites)
5. [Installation & Setup](#installation--setup)
6. [Configuration](#configuration)
7. [Running the Service](#running-the-service)
8. [API Endpoints](#api-endpoints)
9. [Usage Examples](#usage-examples)
10. [Testing](#testing)
11. [Deployment & Demo](#deployment--demo)
12. [Contributing](#contributing)
13. [Roadmap](#roadmap)
14. [License](#license)
15. [Contact & Support](#contact--support)

---

## Project Overview

The **FastAPI Loan Fairness Service** is designed to:

* Analyze loan applications for potential bias across demographic groups.
* Generate fairness metrics (e.g., demographic parity, equalized odds).
* Provide an interactive documentation UI for testing and exploration.

This tool empowers lenders, regulators, and developers to embed fairness evaluations into their loan pipelines, promoting transparent and ethical lending practices.

---

## Features

* **Bias Detection:** Computes key fairness metrics (demographic parity, disparate impact, equal opportunity).
* **Modular Pipeline:** Easily swap or extend fairness algorithms and data-processing steps.
* **Interactive Swagger UI:** Auto-generated API docs at `/docs`.
* **Ngrok Integration:** Seamlessly expose local development to the internet for demos.
* **Environment-driven Config:** All secrets and endpoints managed via environment variables.

---

## Architecture & Design

```text
Client --> FastAPI App --> Fairness Engine --> Results
                         \
                          --> Database (optional)
```

* **FastAPI App:** Entry point exposing RESTful endpoints.
* **Fairness Engine:** Core logic computing metrics.
* **Database Layer (optional):** Persist application data and analysis results.

Key directories:

```
├── app
│   ├── main.py          # FastAPI application instance
│   ├── api              # Routers & endpoint definitions
│   ├── core             # Configuration & settings
│   ├── models           # Pydantic models & schemas
│   ├── services         # Business logic & fairness computations
│   └── utils            # Helper functions
├── tests                # Pytest test suite
├── .env.example         # Sample environment variables
├── requirements.txt     # Python dependencies
└── Dockerfile           # Containerization
```

---

## Prerequisites

* **Python 3.10+**
* **Ngrok v3** (for public tunneling)
* **(Optional)** Docker & Docker Compose

---

## Installation & Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/jedam19899/loan-fairness-service.git
   cd loan-fairness-service
   ```
2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Copy environment file**

   ```bash
   cp .env.example .env
   ```

---

## Configuration

Edit the `.env` file with your own values:

```env
# Ngrok
NGROK_AUTHTOKEN=your_ngrok_token_here
NGROK_REGION=us

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/loans

# App settings
API_VERSION=v1
```

---

## Running the Service

1. **Start FastAPI**

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
2. **Expose via Ngrok**

   ```bash
   ngrok http 8000
   ```
3. **Access API docs**

   * Local: `http://127.0.0.1:8000/docs`
   * Public: `https://<your-ngrok-id>.ngrok.io/docs`

---

## API Endpoints

| Method | Path         | Description                               |
| ------ | ------------ | ----------------------------------------- |
| POST   | `/v1/assess` | Submit loan application JSON for analysis |
| GET    | `/v1/health` | Health check endpoint                     |

### Request Schema: `/v1/assess`

```json
{
  "applicant": {
    "age": 35,
    "income": 75000,
    "credit_score": 680,
    "ethnicity": "groupA"
    // ... other fields
  }
}
```

### Response Schema

```json
{
  "fairness_metrics": {
    "demographic_parity": 0.92,
    "equal_opportunity_difference": 0.05,
    // ... more metrics
  },
  "analysis_timestamp": "2025-07-04T22:00:00Z"
}
```

---

## Usage Examples

### cURL

```bash
curl -X POST https://<ngrok-id>.ngrok.io/v1/assess \
     -H "Content-Type: application/json" \
     -d '{"applicant": {"age": 42, "income": 55000, "credit_score": 710, "ethnicity": "groupB"}}'
```

### Python

```python
import requests

url = "https://<ngrok-id>.ngrok.io/v1/assess"
payload = {"applicant": {"age": 30, "income": 60000, "credit_score": 700, "ethnicity": "groupA"}}

response = requests.post(url, json=payload)
print(response.json())
```

---

## Testing

Run the test suite with:

```bash
pytest --cov=app
```

---

## Deployment & Demo

* **Docker**

  ```bash
  docker build -t loan-fairness-service .
  docker run -p 8000:8000 loan-fairness-service
  ```

* Use ngrok to expose Docker container: `ngrok http 8000`

* **GitHub Actions**

  * CI pipeline runs tests on each PR.
  * Auto-deploy to staging on merges to `main` (configure secrets in GitHub).

---

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repo
2. **Create a feature branch**: `git checkout -b feature/YourFeature`
3. **Commit your changes**: `git commit -m "Add YourFeature"`
4. **Push to branch**: `git push origin feature/YourFeature`
5. **Open a Pull Request**

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Roadmap

* [ ] Add authentication & RBAC
* [ ] Persist results in database
* [ ] Web UI for visualizing fairness metrics
* [ ] Support batch processing

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact & Support

* **Maintainer:** jedam19899 (GitHub)
* **Issues:** [Open a new issue](https://github.com/jedam19899/loan-fairness-service/issues)
* **Email:** [j.dampare@yahoo.com](mailto:j.dampare@yahoo.com)

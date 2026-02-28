# SheCan - Backend API

SheCan is a specialized fertility preservation guidance system designed specifically for female cancer patients. The backend provides the analytical engine for risk assessment, technique recommendation, and cost estimation.

## Tech Stack

- Python 3.9+
- FastAPI (Web Framework)
- Pydantic (Data Validation)
- Uvicorn (ASGI Server)
- Python-dotenv (Environment Management)

## Core Implementation Details

The backend implements complex clinical logic across several modules:

- Fertility Risk Engine: Uses a multi-factor algorithm incorporating age-based logistic curves, AMH-level scoring, cancer gonadotoxicity profiles, and medical history interaction terms to determine fertility risk.
- Preservation Strategy: Recommends techniques (Oocyte/Embryo/Ovarian Tissue Cryopreservation) based on patient age, treatment urgency, and partner status.
- Cost Analysis: Calculates detailed financial breakdowns using city-specific multipliers (Kochi, Trivandrum, etc.) and patient-specific variables like storage duration and expected stimulation cycles.
- Information Services: Serves a curated database of specialized fertility centers and comprehensive FAQs focused on oncofertility.

## API Endpoints

- POST /api/fertility-risk: Comprehensive risk and clinical analysis.
- POST /api/preservation-technique: Personalized technique recommendation and cost breakdown.
- GET /api/faqs: Structured information on fertility preservation.
- GET /api/centers: Database of specialized fertility preservation centers.
- GET /api/centers/{city}: Filtered list of centers by city.

## Setup and Installation

Follow these steps to run the backend locally:

1. Navigate to the backend directory:
   cd backend

2. Create a virtual environment:
   python -m venv venv

3. Activate the virtual environment:
   venv\Scripts\activate

4. Install the required dependencies:
   pip install -r requirements.txt

5. Start the development server:
   uvicorn main:app --reload

The API will be available at http://127.0.0.1:8000. Access the interactive documentation at http://127.0.0.1:8000/docs.

## License

This project is licensed under the MIT License.

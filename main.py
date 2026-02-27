from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import FertilityRiskInput, TechniqueInput
from calculators import calculate_risk_score, suggest_technique_and_cost
from data import get_faq_data, get_center_data, get_all_center_data

app = FastAPI(
    title="SheCan API",
    description="Fertility preservation guidance system for cancer patients",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "SheCan API is running", "version": "1.0.0"}


@app.post("/api/fertility-risk")
async def fertility_risk(data: FertilityRiskInput):
    try:
        result = calculate_risk_score(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/preservation-technique")
async def preservation_technique(data: TechniqueInput):
    try:
        result = suggest_technique_and_cost(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/faqs")
async def faqs():
    return get_faq_data()


@app.get("/api/centers")
async def all_centers():
    return get_all_center_data()


@app.get("/api/centers/{city}")
async def centers_by_city(city: str):
    result = get_center_data(city)
    if not result["centers"]:
        raise HTTPException(
            status_code=404,
            detail=f"No centers found for city: {city}. Available: kochi, trivandrum",
        )
    return result
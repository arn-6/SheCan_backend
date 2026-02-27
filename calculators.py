import math
from models import FertilityRiskInput, TechniqueInput


# ──────────────────────────────────────────────
#  FERTILITY RISK SCORE CALCULATOR
# ──────────────────────────────────────────────

CANCER_PROFILES = {
    "blood_cancer": {
        "base_score": 23,
        "gonadotoxicity": "High",
        "typical_agents": "Alkylating agents (Cyclophosphamide, Busulfan), TBI",
        "ovarian_failure_probability": 0.80,
        "treatment_delay_tolerance_days": 14,
    },
    "breast_cancer": {
        "base_score": 18,
        "gonadotoxicity": "Moderate-High",
        "typical_agents": "AC-T (Doxorubicin, Cyclophosphamide, Taxol)",
        "ovarian_failure_probability": 0.60,
        "treatment_delay_tolerance_days": 21,
    },
    "ovarian_cancer": {
        "base_score": 25,
        "gonadotoxicity": "Very High",
        "typical_agents": "Platinum-based (Carboplatin/Cisplatin) + Surgery",
        "ovarian_failure_probability": 0.92,
        "treatment_delay_tolerance_days": 10,
    },
    "cervical_cancer": {
        "base_score": 16,
        "gonadotoxicity": "Moderate",
        "typical_agents": "Cisplatin + Pelvic Radiation",
        "ovarian_failure_probability": 0.55,
        "treatment_delay_tolerance_days": 21,
    },
    "bone_cancer": {
        "base_score": 19,
        "gonadotoxicity": "High",
        "typical_agents": "High-dose Methotrexate, Doxorubicin, Cisplatin",
        "ovarian_failure_probability": 0.70,
        "treatment_delay_tolerance_days": 14,
    },
    "brain_cancer": {
        "base_score": 15,
        "gonadotoxicity": "Moderate",
        "typical_agents": "Temozolomide, Cranial Radiation",
        "ovarian_failure_probability": 0.45,
        "treatment_delay_tolerance_days": 28,
    },
    "thyroid_cancer": {
        "base_score": 8,
        "gonadotoxicity": "Low",
        "typical_agents": "Radioactive Iodine (I-131)",
        "ovarian_failure_probability": 0.15,
        "treatment_delay_tolerance_days": 42,
    },
    "lung_cancer": {
        "base_score": 17,
        "gonadotoxicity": "Moderate-High",
        "typical_agents": "Platinum doublet chemotherapy",
        "ovarian_failure_probability": 0.55,
        "treatment_delay_tolerance_days": 14,
    },
    "colon_cancer": {
        "base_score": 14,
        "gonadotoxicity": "Moderate",
        "typical_agents": "FOLFOX (5-FU, Leucovorin, Oxaliplatin)",
        "ovarian_failure_probability": 0.40,
        "treatment_delay_tolerance_days": 21,
    },
    "skin_cancer": {
        "base_score": 6,
        "gonadotoxicity": "Low",
        "typical_agents": "Immunotherapy (Pembrolizumab), Surgery",
        "ovarian_failure_probability": 0.10,
        "treatment_delay_tolerance_days": 42,
    },
    "kidney_cancer": {
        "base_score": 13,
        "gonadotoxicity": "Low-Moderate",
        "typical_agents": "Targeted therapy (Sunitinib), Immunotherapy",
        "ovarian_failure_probability": 0.30,
        "treatment_delay_tolerance_days": 28,
    },
    "other": {
        "base_score": 12,
        "gonadotoxicity": "Variable",
        "typical_agents": "Depends on specific diagnosis",
        "ovarian_failure_probability": 0.35,
        "treatment_delay_tolerance_days": 21,
    },
}

STAGE_PROFILES = {
    "stage_1": {"score": 5, "intensity_factor": 0.30, "label": "Stage I - Localized"},
    "stage_2": {"score": 10, "intensity_factor": 0.55, "label": "Stage II - Regional"},
    "stage_3": {"score": 16, "intensity_factor": 0.80, "label": "Stage III - Advanced"},
    "stage_4": {"score": 20, "intensity_factor": 1.00, "label": "Stage IV - Metastatic"},
}

CONDITION_WEIGHTS = {
    "endometriosis": 3.5,
    "pcos": 1.5,
    "previous_chemotherapy": 5.0,
    "previous_radiation": 4.5,
    "autoimmune_disorder": 3.0,
    "diabetes": 2.0,
    "thyroid_disorder": 2.0,
    "genetic_disorder": 3.0,
    "premature_ovarian_insufficiency": 5.0,
    "uterine_fibroids": 2.0,
    "none": 0,
}


def _compute_age_score(age: int) -> tuple:
    """
    Non-linear age scoring using a modified logistic curve.
    Reflects accelerated ovarian reserve decline after 32.
    Returns (score_0_to_25, fertility_potential_0_to_1)
    """
    # Logistic-style formula:  score = 25 / (1 + e^(-0.18*(age-35)))
    raw = 25.0 / (1.0 + math.exp(-0.18 * (age - 35)))
    score = round(min(25.0, max(1.0, raw)), 2)

    # Fertility potential decays with age (simplified Faddy-Gosden model)
    # At birth ~1M follicles, declining exponentially
    # We normalize to 0-1 scale for practical use
    potential = max(0.02, 1.0 - (1.0 / (1.0 + math.exp(-0.22 * (age - 38)))))
    return score, round(potential, 4)


def _compute_amh_score(amh: float) -> tuple:
    """
    AMH scoring using inverse relationship.
    AMH (ng/mL): >4=Excellent, 2-4=Good, 1-2=Low-Normal, 0.5-1=Low, <0.5=Very Low
    """
    if amh >= 5.0:
        score, reserve = 1, "Excellent"
    elif amh >= 3.5:
        score = 2 + (5.0 - amh) * 1.33
        reserve = "Very Good"
    elif amh >= 2.5:
        score = 4 + (3.5 - amh) * 3.0
        reserve = "Good"
    elif amh >= 1.5:
        score = 7 + (2.5 - amh) * 2.0
        reserve = "Normal"
    elif amh >= 1.0:
        score = 9 + (1.5 - amh) * 4.0
        reserve = "Low-Normal"
    elif amh >= 0.5:
        score = 11 + (1.0 - amh) * 4.0
        reserve = "Low"
    elif amh >= 0.2:
        score = 13 + (0.5 - amh) * 3.33
        reserve = "Very Low"
    else:
        score, reserve = 15, "Critically Low"

    return round(min(15, max(0, score)), 2), reserve


def _compute_period_score(regularity: str) -> tuple:
    mapping = {
        "regular": (1, "Normal ovulatory function likely"),
        "irregular": (3, "Possible anovulation or hormonal imbalance"),
        "absent": (5, "Amenorrhea — may indicate ovarian suppression"),
        "unknown": (3, "Assessment needed"),
    }
    return mapping.get(regularity, (3, "Assessment needed"))


def _compute_conditions_score(conditions: list) -> tuple:
    total = 0.0
    details = []
    for c in conditions:
        weight = CONDITION_WEIGHTS.get(c, 1.0)
        total += weight
        details.append({"condition": c.replace("_", " ").title(), "impact": weight})
    capped = min(10.0, total)
    return round(capped, 2), details


def _compute_lifestyle_modifier(bmi: float, smoking: bool) -> float:
    """Adds 0-3 bonus risk points for lifestyle factors."""
    mod = 0.0
    if bmi < 18.5 or bmi > 30:
        mod += 1.5
    elif bmi > 27:
        mod += 0.5
    if smoking:
        mod += 1.5
    return round(mod, 2)


def _compute_interaction_terms(
    age_score, cancer_score, stage_score, amh_score
) -> float:
    """
    Cross-factor interaction effects:
    - Age × Cancer gonadotoxicity synergy
    - AMH × Age compounding depletion
    - Stage × Cancer treatment escalation
    """
    # Normalize each to 0-1
    a = age_score / 25.0
    c = cancer_score / 25.0
    s = stage_score / 20.0
    m = amh_score / 15.0

    interaction = (
        (a * c) * 3.0       # age-cancer synergy
        + (m * a) * 2.5     # amh-age compounding
        + (s * c) * 1.5     # stage-cancer escalation
    )
    return round(min(7.0, interaction), 2)


def _estimate_eggs_per_cycle(age: int, amh: float) -> int:
    """Estimates expected oocyte yield per stimulation cycle."""
    if age < 25:
        base = 18
    elif age < 30:
        base = 14
    elif age < 33:
        base = 11
    elif age < 35:
        base = 9
    elif age < 38:
        base = 6
    elif age < 40:
        base = 4
    else:
        base = 2

    amh_multiplier = min(1.6, max(0.25, amh / 2.5))
    return max(1, round(base * amh_multiplier))


def _recommended_eggs(age: int) -> int:
    """ASRM/ESHRE-aligned recommendation for eggs to bank."""
    if age < 30:
        return 15
    elif age < 35:
        return 20
    elif age < 38:
        return 25
    elif age < 40:
        return 30
    return 40


def _success_rate_per_egg(age: int) -> float:
    """Live birth rate per thawed oocyte (approximate)."""
    if age < 30:
        return 0.08
    elif age < 35:
        return 0.06
    elif age < 38:
        return 0.045
    elif age < 40:
        return 0.03
    return 0.015


def calculate_risk_score(data: FertilityRiskInput) -> dict:
    # ── Individual component scores ──
    age_score, fertility_potential = _compute_age_score(data.age)
    cancer_profile = CANCER_PROFILES.get(data.cancer_type, CANCER_PROFILES["other"])
    cancer_score = cancer_profile["base_score"]
    stage_profile = STAGE_PROFILES.get(data.cancer_stage, STAGE_PROFILES["stage_2"])
    stage_score = stage_profile["score"]
    amh_score, ovarian_reserve = _compute_amh_score(data.amh_level)
    period_score, period_note = _compute_period_score(data.period_regularity)
    conditions_score, condition_details = _compute_conditions_score(
        data.medical_conditions
    )
    lifestyle_mod = _compute_lifestyle_modifier(data.bmi, data.smoking)

    # ── Interaction terms ──
    interaction = _compute_interaction_terms(
        age_score, cancer_score, stage_score, amh_score
    )

    # ── Total raw score ──
    raw_total = (
        age_score
        + cancer_score
        + stage_score
        + amh_score
        + conditions_score
        + period_score
        + lifestyle_mod
        + interaction
    )

    # ── Normalize to 0-100 ──
    max_possible = 25 + 25 + 20 + 15 + 10 + 5 + 3 + 7  # 110
    final_score = round(min(100, (raw_total / max_possible) * 100), 1)

    # ── Risk classification ──
    if final_score <= 25:
        risk_level, urgency, color = (
            "Low",
            "Monitor — regular follow-up recommended",
            "#10B981",
        )
        time_window = "3-6 months available before treatment"
        needs_immediate = False
    elif final_score <= 50:
        risk_level, urgency, color = (
            "Moderate",
            "Consider preservation — consult specialist in 2-4 weeks",
            "#F59E0B",
        )
        time_window = "1-3 months recommended window"
        needs_immediate = False
    elif final_score <= 75:
        risk_level, urgency, color = (
            "High",
            "Preservation strongly recommended — act within 1-2 weeks",
            "#F97316",
        )
        time_window = "2-4 weeks optimal window"
        needs_immediate = True
    else:
        risk_level, urgency, color = (
            "Critical",
            "Immediate action required — emergency fertility consultation",
            "#EF4444",
        )
        time_window = "Immediate — within days"
        needs_immediate = True

    # ── Post-treatment fertility analysis ──
    ovarian_failure_prob = cancer_profile["ovarian_failure_probability"]
    treatment_intensity = stage_profile["intensity_factor"]
    treatment_impact = ovarian_failure_prob * treatment_intensity

    # Post-treatment natural conception probability
    base_conception = fertility_potential * 100
    post_treatment_conception = round(
        max(0, base_conception * (1 - treatment_impact)), 1
    )

    # Egg freezing analysis
    eggs_per_cycle = _estimate_eggs_per_cycle(data.age, data.amh_level)
    recommended = _recommended_eggs(data.age)
    cycles_needed = max(1, math.ceil(recommended / max(1, eggs_per_cycle)))
    rate = _success_rate_per_egg(data.age)

    # Cumulative live birth probability  = 1 - (1-rate)^n
    cumulative_success = round((1 - (1 - rate) ** recommended) * 100, 1)

    # Time required for preservation (days)
    days_per_cycle = 14  # typical stimulation
    total_days = days_per_cycle * cycles_needed + 5  # +5 for assessment
    delay_tolerance = cancer_profile["treatment_delay_tolerance_days"]
    feasible = total_days <= delay_tolerance * cycles_needed

    # ── Build recommendations ──
    recommendations = []
    if needs_immediate:
        recommendations.append(
            "⚠️ Urgent: Schedule an emergency fertility preservation consultation immediately."
        )
    if cancer_profile["gonadotoxicity"] in ("High", "Very High"):
        recommendations.append(
            "Your treatment involves highly gonadotoxic agents. Fertility preservation is strongly advised before starting treatment."
        )
    if data.amh_level < 1.0:
        recommendations.append(
            "Your AMH level indicates low ovarian reserve. Discuss aggressive stimulation protocols with your RE."
        )
    if data.age >= 35:
        recommendations.append(
            "Age-related fertility decline accelerates after 35. Multiple cycles may be needed to bank sufficient eggs."
        )
    if data.period_regularity == "absent":
        recommendations.append(
            "Absent periods may indicate existing ovarian suppression. Urgent hormonal evaluation recommended."
        )
    if not recommendations:
        recommendations.append(
            "Your current risk profile suggests monitoring is adequate, but discuss options with your oncologist."
        )
    recommendations.append(
        "Always consult both your oncologist and reproductive endocrinologist for personalized guidance."
    )

    return {
        "total_score": final_score,
        "risk_level": risk_level,
        "urgency": urgency,
        "color": color,
        "time_window": time_window,
        "needs_immediate_preservation": needs_immediate,
        "score_breakdown": {
            "age_score": {"value": age_score, "max": 25, "label": "Age Factor"},
            "cancer_score": {
                "value": cancer_score,
                "max": 25,
                "label": "Cancer Gonadotoxicity",
            },
            "stage_score": {
                "value": stage_score,
                "max": 20,
                "label": "Cancer Stage",
            },
            "amh_score": {"value": amh_score, "max": 15, "label": "AMH / Ovarian Reserve"},
            "conditions_score": {
                "value": conditions_score,
                "max": 10,
                "label": "Medical History",
            },
            "period_score": {
                "value": period_score,
                "max": 5,
                "label": "Menstrual Regularity",
            },
            "lifestyle_modifier": {
                "value": lifestyle_mod,
                "max": 3,
                "label": "Lifestyle Factors",
            },
            "interaction_effects": {
                "value": interaction,
                "max": 7,
                "label": "Compound Risk Effects",
            },
        },
        "clinical_analysis": {
            "ovarian_reserve_status": ovarian_reserve,
            "gonadotoxicity_level": cancer_profile["gonadotoxicity"],
            "treatment_agents": cancer_profile["typical_agents"],
            "ovarian_failure_risk": f"{round(ovarian_failure_prob * 100)}%",
            "treatment_intensity": f"{round(treatment_intensity * 100)}%",
            "post_treatment_natural_conception": f"{post_treatment_conception}%",
            "fertility_potential_index": f"{round(fertility_potential * 100, 1)}%",
            "period_assessment": period_note,
        },
        "preservation_planning": {
            "recommended_eggs_to_freeze": recommended,
            "estimated_eggs_per_cycle": eggs_per_cycle,
            "estimated_cycles_needed": cycles_needed,
            "days_needed_for_preservation": total_days,
            "treatment_delay_tolerance_days": delay_tolerance,
            "preservation_feasible_before_treatment": feasible,
            "cumulative_success_rate": f"{cumulative_success}%",
            "success_rate_per_egg": f"{round(rate * 100, 2)}%",
        },
        "recommendations": recommendations,
        "condition_details": condition_details,
    }


# ──────────────────────────────────────────────
#  TECHNIQUE & COST CALCULATOR
# ──────────────────────────────────────────────

TECHNIQUE_BASE_COSTS = {
    "oocyte_cryopreservation": {
        "name": "Oocyte Cryopreservation (Egg Freezing)",
        "description": "Mature eggs are retrieved after hormonal stimulation and frozen using vitrification for future use.",
        "components": {
            "Initial Consultation & Assessment": 6000,
            "Hormonal Stimulation Medications": 48000,
            "Monitoring (Ultrasound + Blood)": 14000,
            "Egg Retrieval Procedure": 35000,
            "Anesthesia": 8000,
            "Laboratory Processing": 18000,
            "Vitrification (Freezing)": 22000,
        },
        "annual_storage": 12000,
        "success_rate": "30-40% per cycle (age-dependent)",
    },
    "embryo_cryopreservation": {
        "name": "Embryo Cryopreservation",
        "description": "Eggs are fertilized with partner/donor sperm and resulting embryos are frozen. Highest success rates.",
        "components": {
            "Initial Consultation & Assessment": 7000,
            "Hormonal Stimulation Medications": 52000,
            "Monitoring (Ultrasound + Blood)": 16000,
            "Egg Retrieval Procedure": 38000,
            "Anesthesia": 9000,
            "Sperm Processing": 6000,
            "ICSI Fertilization": 28000,
            "Embryo Culture (5-6 days)": 15000,
            "Vitrification (Freezing)": 28000,
        },
        "annual_storage": 15000,
        "success_rate": "40-50% per transfer (age-dependent)",
    },
    "ovarian_tissue_cryopreservation": {
        "name": "Ovarian Tissue Cryopreservation",
        "description": "A strip of ovarian cortex is surgically removed and frozen. Can be re-implanted later. Suitable when stimulation is not possible.",
        "components": {
            "Pre-surgical Assessment": 12000,
            "Laparoscopic Surgery": 75000,
            "Anesthesia (General)": 15000,
            "Tissue Processing & Sectioning": 30000,
            "Cryopreservation": 35000,
            "Hospitalization (1-2 days)": 20000,
        },
        "annual_storage": 18000,
        "success_rate": "Reported live birth rate ~30% post-transplant",
    },
    "ivm": {
        "name": "In Vitro Maturation (IVM)",
        "description": "Immature eggs are collected without full hormonal stimulation and matured in the lab. Ideal for hormone-sensitive cancers.",
        "components": {
            "Initial Consultation": 5000,
            "Minimal Stimulation Medications": 15000,
            "Monitoring": 10000,
            "Egg Retrieval": 30000,
            "Anesthesia": 7000,
            "In Vitro Maturation Culture": 25000,
            "Vitrification": 20000,
        },
        "annual_storage": 12000,
        "success_rate": "20-30% (lower than conventional IVF)",
    },
}

CITY_MULTIPLIERS = {
    "kochi": {"multiplier": 1.12, "label": "Kochi"},
    "trivandrum": {"multiplier": 1.00, "label": "Thiruvananthapuram"},
    "bangalore": {"multiplier": 1.28, "label": "Bengaluru"},
    "chennai": {"multiplier": 1.20, "label": "Chennai"},
    "mumbai": {"multiplier": 1.42, "label": "Mumbai"},
    "delhi": {"multiplier": 1.38, "label": "Delhi"},
}


def _age_cycle_multiplier(age: int) -> tuple:
    """Returns (cost_multiplier, expected_cycles) based on age."""
    if age < 28:
        return 1.00, 1
    elif age < 32:
        return 1.05, 1
    elif age < 35:
        return 1.18, 1
    elif age < 38:
        return 1.35, 2
    elif age < 40:
        return 1.55, 2
    else:
        return 1.85, 3


def _cancer_urgency_multiplier(cancer_type: str) -> float:
    """Emergency protocols cost more."""
    profile = CANCER_PROFILES.get(cancer_type, CANCER_PROFILES["other"])
    tolerance = profile["treatment_delay_tolerance_days"]
    if tolerance <= 14:
        return 1.15  # rush protocol
    elif tolerance <= 21:
        return 1.08
    return 1.00


def _select_technique(data: TechniqueInput) -> list:
    """Rule-based technique selection returning ranked list."""
    techniques = []

    if data.age < 16:
        techniques.append(
            {
                "technique": "ovarian_tissue_cryopreservation",
                "reason": "Prepubertal/young patient — ovarian tissue cryo is the only option without hormonal stimulation.",
                "rank": 1,
            }
        )
        return techniques

    if data.needs_immediate_treatment:
        techniques.append(
            {
                "technique": "ovarian_tissue_cryopreservation",
                "reason": "Immediate treatment needed — no time for ovarian stimulation. Tissue can be retrieved via laparoscopy quickly.",
                "rank": 1,
            }
        )
        if data.cancer_type == "breast_cancer":
            techniques.append(
                {
                    "technique": "ivm",
                    "reason": "IVM avoids high estrogen levels, suitable for hormone-sensitive breast cancer.",
                    "rank": 2,
                }
            )
        return techniques

    # Standard selection logic
    if data.cancer_type == "breast_cancer":
        techniques.append(
            {
                "technique": "oocyte_cryopreservation",
                "reason": "Egg freezing with letrozole-based protocol to minimize estrogen exposure.",
                "rank": 1,
            }
        )
        techniques.append(
            {
                "technique": "ivm",
                "reason": "Alternative: IVM avoids hormonal stimulation entirely for hormone-sensitive cancers.",
                "rank": 2,
            }
        )
    elif data.cancer_type == "ovarian_cancer":
        techniques.append(
            {
                "technique": "ovarian_tissue_cryopreservation",
                "reason": "Ovarian tissue preservation before surgery. Only unaffected tissue is cryopreserved.",
                "rank": 1,
            }
        )
        techniques.append(
            {
                "technique": "oocyte_cryopreservation",
                "reason": "If time permits, egg freezing from the unaffected ovary.",
                "rank": 2,
            }
        )
    elif data.has_partner:
        techniques.append(
            {
                "technique": "embryo_cryopreservation",
                "reason": "With a partner available, embryo freezing offers the highest success rates.",
                "rank": 1,
            }
        )
        techniques.append(
            {
                "technique": "oocyte_cryopreservation",
                "reason": "Egg freezing as backup — preserves reproductive autonomy.",
                "rank": 2,
            }
        )
    else:
        techniques.append(
            {
                "technique": "oocyte_cryopreservation",
                "reason": "Gold standard for fertility preservation in single women. Well-established success rates.",
                "rank": 1,
            }
        )
        if data.age >= 35:
            techniques.append(
                {
                    "technique": "ovarian_tissue_cryopreservation",
                    "reason": "Additional option: tissue cryo can complement egg freezing for older patients.",
                    "rank": 2,
                }
            )

    return techniques


def _calculate_technique_cost(
    technique_key: str, data: TechniqueInput
) -> dict:
    """Heavy cost calculation with full breakdown."""
    tech = TECHNIQUE_BASE_COSTS[technique_key]
    city_info = CITY_MULTIPLIERS.get(
        data.city.lower(), {"multiplier": 1.15, "label": data.city}
    )
    city_mult = city_info["multiplier"]
    age_mult, expected_cycles = _age_cycle_multiplier(data.age)
    urgency_mult = _cancer_urgency_multiplier(data.cancer_type)

    # Apply multipliers to each component
    detailed_breakdown = {}
    procedure_total = 0

    for component, base_cost in tech["components"].items():
        adjusted = round(base_cost * city_mult * age_mult * urgency_mult)
        detailed_breakdown[component] = {
            "base_cost": base_cost,
            "adjusted_cost": adjusted,
            "multiplier_applied": round(city_mult * age_mult * urgency_mult, 3),
        }
        procedure_total += adjusted

    # Storage costs
    annual_storage = round(tech["annual_storage"] * city_mult)
    total_storage = annual_storage * data.storage_years

    # Additional cycles (if applicable)
    additional_cycle_cost = 0
    if expected_cycles > 1 and technique_key != "ovarian_tissue_cryopreservation":
        # Only medication + monitoring + retrieval repeat
        repeatable = [
            "Hormonal Stimulation Medications",
            "Minimal Stimulation Medications",
            "Monitoring (Ultrasound + Blood)",
            "Monitoring",
            "Egg Retrieval Procedure",
            "Egg Retrieval",
            "Anesthesia",
        ]
        per_extra_cycle = 0
        for comp, base in tech["components"].items():
            if comp in repeatable:
                per_extra_cycle += round(base * city_mult * urgency_mult)

        extra_cycles = expected_cycles - 1
        additional_cycle_cost = per_extra_cycle * extra_cycles
        detailed_breakdown["Additional Cycles"] = {
            "extra_cycles": extra_cycles,
            "cost_per_cycle": per_extra_cycle,
            "total": additional_cycle_cost,
        }

    # Grand total
    grand_total = procedure_total + total_storage + additional_cycle_cost

    # GST (18% on services)
    gst = round(grand_total * 0.05)  # medical services often 5%
    grand_total_with_tax = grand_total + gst

    return {
        "technique_key": technique_key,
        "technique_name": tech["name"],
        "description": tech["description"],
        "success_rate": tech["success_rate"],
        "detailed_breakdown": detailed_breakdown,
        "procedure_cost": procedure_total,
        "annual_storage_cost": annual_storage,
        "storage_years": data.storage_years,
        "total_storage_cost": total_storage,
        "additional_cycles_cost": additional_cycle_cost,
        "expected_cycles": expected_cycles,
        "subtotal": grand_total,
        "gst_5_percent": gst,
        "grand_total": grand_total_with_tax,
        "cost_range": {
            "minimum": round(grand_total_with_tax * 0.85),
            "maximum": round(grand_total_with_tax * 1.18),
        },
        "multipliers_used": {
            "city": {"name": city_info["label"], "factor": city_mult},
            "age": {"age": data.age, "factor": age_mult},
            "urgency": {"cancer": data.cancer_type, "factor": urgency_mult},
        },
    }


def suggest_technique_and_cost(data: TechniqueInput) -> dict:
    ranked_techniques = _select_technique(data)

    results = []
    for t in ranked_techniques:
        cost_data = _calculate_technique_cost(t["technique"], data)
        results.append({**t, "cost_analysis": cost_data})

    return {
        "patient_profile": {
            "age": data.age,
            "cancer_type": data.cancer_type,
            "cancer_stage": data.cancer_stage,
            "city": data.city,
            "has_partner": data.has_partner,
            "needs_immediate_treatment": data.needs_immediate_treatment,
            "storage_years": data.storage_years,
        },
        "recommended_techniques": results,
        "total_options": len(results),
    }
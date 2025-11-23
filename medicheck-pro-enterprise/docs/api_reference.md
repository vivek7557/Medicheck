# MediCheck Pro Enterprise API Reference

## Overview

This document provides a comprehensive reference for the MediCheck Pro Enterprise API, which enables interaction with the multi-agent medical assistant system.

## Authentication

All API requests require authentication using an API key. Include your API key in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

## Base URL

The base URL for all API endpoints is:
```
https://api.medicheck-pro-enterprise.com/v1
```

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `400`: Bad Request - The request was invalid
- `401`: Unauthorized - Authentication failed
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - The requested resource doesn't exist
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Something went wrong on our end

All error responses include a JSON object with error details:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

## Endpoints

### 1. Patient Interaction

#### Start New Consultation
```
POST /consultations
```

Initiates a new patient consultation session.

**Request Body:**
```json
{
  "patient_id": "string (optional)",
  "initial_query": "string",
  "patient_context": {
    "age": 35,
    "gender": "M|F|O",
    "allergies": ["penicillin", "nuts"],
    "current_medications": ["metformin", "lisinopril"],
    "medical_conditions": ["diabetes", "hypertension"]
  }
}
```

**Response:**
```json
{
  "consultation_id": "string",
  "session_token": "string",
  "initial_response": "string",
  "agent_assigned": "string",
  "timestamp": "ISO 8601 datetime"
}
```

#### Continue Consultation
```
POST /consultations/{consultation_id}/messages
```

Sends a message to continue an existing consultation.

**Request Body:**
```json
{
  "message": "string",
  "message_type": "query|symptom_report|followup|clarification"
}
```

**Response:**
```json
{
  "message_id": "string",
  "response": "string",
  "agent_responded": "string",
  "next_steps": ["string"],
  "confidence_level": 0.0 - 1.0,
  "timestamp": "ISO 8601 datetime"
}
```

#### Get Consultation History
```
GET /consultations/{consultation_id}
```

Retrieves the complete history of a consultation.

**Response:**
```json
{
  "consultation_id": "string",
  "status": "active|completed|transferred",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime",
  "messages": [
    {
      "message_id": "string",
      "sender": "patient|agent|system",
      "content": "string",
      "timestamp": "ISO 8601 datetime",
      "agent_type": "string"
    }
  ],
  "summary": "string",
  "recommended_followup": "string"
}
```

### 2. Triage Services

#### Emergency Assessment
```
POST /triage/emergency
```

Performs emergency assessment based on symptoms.

**Request Body:**
```json
{
  "symptoms": ["chest pain", "shortness of breath"],
  "severity_indicators": ["severe", "sudden onset"],
  "patient_age": 65,
  "patient_gender": "M|F|O",
  "vital_signs": {
    "heart_rate": 120,
    "blood_pressure_systolic": 180,
    "blood_pressure_diastolic": 110,
    "temperature": 99.5
  }
}
```

**Response:**
```json
{
  "triage_level": "immediate|urgent|semi_urgent|non_urgent",
  "risk_level": "critical|high|moderate|low",
  "recommended_action": "string",
  "estimated_wait_time": "integer minutes",
  "red_flags": ["string"],
  "confidence": 0.0 - 1.0
}
```

#### Symptom Analysis
```
POST /triage/symptoms
```

Analyzes reported symptoms for initial assessment.

**Request Body:**
```json
{
  "symptoms": ["headache", "nausea", "sensitivity_to_light"],
  "duration_days": 3,
  "severity": "mild|moderate|severe",
  "onset": "gradual|sudden",
  "exacerbating_factors": ["bright_light", "movement"],
  "relieving_factors": ["rest", "dark_room"],
  "associated_symptoms": ["dizziness", "vomiting"]
}
```

**Response:**
```json
{
  "possible_conditions": [
    {
      "condition": "string",
      "probability": 0.0 - 1.0,
      "description": "string",
      "commonality": "very_common|common|uncommon|rare"
    }
  ],
  "recommended_care_setting": "home|clinic|emergency",
  "red_flags": ["string"],
  "when_to_seek_care": "immediately|within_24_hours|monitor_symptoms",
  "confidence": 0.0 - 1.0
}
```

### 3. Diagnostic Services

#### Condition Assessment
```
POST /diagnosis/assess
```

Performs detailed condition assessment.

**Request Body:**
```json
{
  "symptoms": ["string"],
  "physical_findings": ["string"],
  "medical_history": {
    "conditions": ["diabetes", "hypertension"],
    "surgeries": ["appendectomy"],
    "allergies": ["penicillin"],
    "medications": ["metformin"]
  },
  "demographics": {
    "age": 45,
    "gender": "M|F|O",
    "ethnicity": "string"
  },
  "lab_results": [
    {
      "test_name": "string",
      "result": "string",
      "unit": "string",
      "reference_range": "string",
      "abnormal": true|false
    }
  ]
}
```

**Response:**
```json
{
  "primary_diagnosis": {
    "condition": "string",
    "icd_code": "string",
    "confidence": 0.0 - 1.0,
    "supporting_evidence": ["string"]
  },
  "differential_diagnosis": [
    {
      "condition": "string",
      "icd_code": "string",
      "probability": 0.0 - 1.0,
      "key_differentiators": ["string"]
    }
  ],
  "recommended_tests": [
    {
      "test_name": "string",
      "urgency": "immediate|soon|routine",
      "rationale": "string"
    }
  ],
  "risk_factors": ["string"],
  "confidence": 0.0 - 1.0
}
```

### 4. Treatment Services

#### Treatment Recommendations
```
POST /treatment/recommend
```

Provides treatment recommendations for a condition.

**Request Body:**
```json
{
  "condition": "string",
  "patient_profile": {
    "age": 45,
    "gender": "M|F|O",
    "weight_kg": 70,
    "height_cm": 175,
    "allergies": ["penicillin"],
    "current_medications": ["metformin", "lisinopril"],
    "comorbidities": ["diabetes", "hypertension"]
  },
  "severity": "mild|moderate|severe",
  "treatment_goals": ["symptom_relief", "disease_management", "prevention"]
}
```

**Response:**
```json
{
  "treatment_plan": {
    "medications": [
      {
        "name": "string",
        "dosage": "string",
        "frequency": "string",
        "duration": "string",
        "instructions": "string",
        "warnings": ["string"]
      }
    ],
    "lifestyle_modifications": ["string"],
    "monitoring_requirements": ["string"],
    "followup_schedule": "string"
  },
  "alternative_options": [
    {
      "option": "string",
      "pros": ["string"],
      "cons": ["string"],
      "suitability_score": 0.0 - 1.0
    }
  ],
  "drug_interactions": [
    {
      "medication1": "string",
      "medication2": "string",
      "severity": "mild|moderate|severe",
      "description": "string"
    }
  ],
  "contraindications": ["string"],
  "confidence": 0.0 - 1.0
}
```

#### Drug Interaction Check
```
POST /treatment/interaction-check
```

Checks for potential drug interactions.

**Request Body:**
```json
{
  "medications": [
    {
      "name": "string",
      "dosage": "string",
      "frequency": "string"
    }
  ],
  "patient_profile": {
    "age": 45,
    "gender": "M|F|O",
    "allergies": ["penicillin"],
    "current_medications": ["metformin", "lisinopril"],
    "comorbidities": ["diabetes", "hypertension"]
  }
}
```

**Response:**
```json
{
  "interactions_found": [
    {
      "medication1": "string",
      "medication2": "string",
      "severity": "mild|moderate|severe",
      "mechanism": "string",
      "clinical_significance": "string",
      "management_recommendation": "string"
    }
  ],
  "safe_combinations": true|false,
  "alternative_recommendations": ["string"]
}
```

### 5. Research Services

#### Medical Literature Search
```
POST /research/search
```

Searches medical literature for evidence-based information.

**Request Body:**
```json
{
  "query": "string",
  "filters": {
    "publication_date_range": {
      "start": "YYYY-MM-DD",
      "end": "YYYY-MM-DD"
    },
    "study_type": ["randomized_controlled_trial", "meta_analysis", "case_study"],
    "age_group": "pediatric|adult|geriatric",
    "specialty": "string"
  },
  "max_results": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "string",
      "abstract": "string",
      "authors": ["string"],
      "journal": "string",
      "publication_date": "YYYY-MM-DD",
      "doi": "string",
      "pmid": "string",
      "relevance_score": 0.0 - 1.0,
      "study_type": "string",
      "sample_size": "integer",
      "key_findings": ["string"],
      "limitations": ["string"]
    }
  ],
  "total_results": "integer",
  "search_metadata": {
    "search_time_ms": "integer",
    "database_searched": "string"
  }
}
```

### 6. System Status

#### Health Check
```
GET /health
```

Checks the health status of the system.

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "ISO 8601 datetime",
  "services": {
    "agents": "healthy|degraded|unhealthy",
    "database": "healthy|degraded|unhealthy",
    "vector_store": "healthy|degraded|unhealthy",
    "external_apis": "healthy|degraded|unhealthy"
  }
}
```

#### System Metrics
```
GET /metrics
```

Retrieves system performance metrics.

**Response:**
```json
{
  "timestamp": "ISO 8601 datetime",
  "active_consultations": "integer",
  "requests_per_minute": "float",
  "average_response_time_ms": "float",
  "agent_utilization": {
    "triage": "float 0-1",
    "diagnosis": "float 0-1",
    "treatment": "float 0-1"
  },
  "system_resources": {
    "cpu_usage": "float 0-1",
    "memory_usage": "float 0-1",
    "disk_usage": "float 0-1"
  }
}
```

## Rate Limits

The API implements rate limiting to ensure service availability:

- **Standard Tier**: 100 requests per minute per API key
- **Professional Tier**: 500 requests per minute per API key
- **Enterprise Tier**: 1000 requests per minute per API key

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

## Webhook Events

The API can send webhook notifications for certain events. Configure webhook endpoints in your dashboard.

### Supported Events

- `consultation.created`: New consultation started
- `consultation.completed`: Consultation finished
- `triage.completed`: Triage assessment completed
- `diagnosis.completed`: Diagnosis completed
- `treatment.recommended`: Treatment plan provided

### Webhook Payload

```json
{
  "event_id": "string",
  "event_type": "string",
  "timestamp": "ISO 8601 datetime",
  "data": {
    // Event-specific data
  },
  "attempt": 1
}
```

## SDKs and Libraries

Official SDKs are available for:

- Python: `pip install medicheck-pro-sdk`
- JavaScript: `npm install @medicheck/pro-sdk`
- Java: `medicheck-pro-sdk` via Maven Central

## Support

For API support, contact our team at:
- Email: api-support@medicheck-pro.com
- Documentation: https://docs.medicheck-pro.com
- Status Page: https://status.medicheck-pro.com
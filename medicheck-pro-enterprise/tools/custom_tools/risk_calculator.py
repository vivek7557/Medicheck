from typing import Dict, Any, List
import asyncio
from datetime import datetime


class RiskCalculatorTool:
    """
    Custom tool for calculating various medical risks (cardiovascular, diabetes, etc.).
    """
    
    def __init__(self):
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate medical risks based on patient data.
        """
        patient_data = input_data.get("patient_data", {})
        
        # Calculate various risk scores
        cardiovascular_risk = await self.calculate_cardiovascular_risk(patient_data)
        diabetes_risk = await self.calculate_diabetes_risk(patient_data)
        fall_risk = await self.calculate_fall_risk(patient_data)
        
        return {
            "cardiovascular_risk": cardiovascular_risk,
            "diabetes_risk": diabetes_risk,
            "fall_risk": fall_risk,
            "overall_risk_assessment": self._combine_risks(cardiovascular_risk, diabetes_risk, fall_risk)
        }
    
    async def calculate_cardiovascular_risk(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate cardiovascular risk using standard algorithms (e.g., ASCVD risk calculator).
        """
        age = patient_data.get("age", 50)
        gender = patient_data.get("gender", "male")
        systolic_bp = patient_data.get("systolic_bp", 120)
        cholesterol = patient_data.get("cholesterol", 200)
        hdl_cholesterol = patient_data.get("hdl_cholesterol", 50)
        smoker = patient_data.get("smoker", False)
        diabetic = patient_data.get("diabetic", False)
        
        # Simplified ASCVD risk calculation (in reality, this would use more complex algorithms)
        risk_score = 0
        
        # Basic risk factors
        if age > 55:
            risk_score += 2
        if systolic_bp > 140:
            risk_score += 2
        if cholesterol > 240:
            risk_score += 1
        if hdl_cholesterol < 40:
            risk_score += 1
        if smoker:
            risk_score += 2
        if diabetic:
            risk_score += 2
        if gender.lower() == "female":
            risk_score -= 1  # Women generally have lower baseline risk
        
        # Convert to percentage risk
        risk_percentage = min(99, max(0, risk_score * 5))
        
        return {
            "score": risk_score,
            "percentage_risk": f"{risk_percentage}%",
            "risk_level": self._get_risk_level(risk_percentage),
            "factors": {
                "age": age,
                "gender": gender,
                "systolic_bp": systolic_bp,
                "cholesterol": cholesterol,
                "hdl_cholesterol": hdl_cholesterol,
                "smoker": smoker,
                "diabetic": diabetic
            }
        }
    
    async def calculate_diabetes_risk(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate diabetes risk based on patient factors.
        """
        age = patient_data.get("age", 50)
        bmi = patient_data.get("bmi", 25)
        family_history = patient_data.get("family_history_diabetes", False)
        gestational_diabetes = patient_data.get("gestational_diabetes", False)
        pcod = patient_data.get("pcod", False)  # Polycystic ovarian disease
        ethnicity_high_risk = patient_data.get("ethnicity_high_risk", False)
        hypertension = patient_data.get("hypertension", False)
        hdl_low = patient_data.get("hdl_low", False)
        triglycerides_high = patient_data.get("triglycerides_high", False)
        
        risk_score = 0
        
        if age >= 45:
            risk_score += 1
        if bmi >= 25:
            risk_score += 1
        if family_history:
            risk_score += 1
        if gestational_diabetes:
            risk_score += 1
        if pcod:
            risk_score += 1
        if ethnicity_high_risk:
            risk_score += 1
        if hypertension:
            risk_score += 1
        if hdl_low:
            risk_score += 1
        if triglycerides_high:
            risk_score += 1
        
        risk_percentage = min(99, max(0, risk_score * 8))
        
        return {
            "score": risk_score,
            "percentage_risk": f"{risk_percentage}%",
            "risk_level": self._get_risk_level(risk_percentage),
            "factors": {
                "age": age,
                "bmi": bmi,
                "family_history": family_history,
                "gestational_diabetes": gestational_diabetes,
                "pcod": pcod,
                "ethnicity_high_risk": ethnicity_high_risk,
                "hypertension": hypertension,
                "hdl_low": hdl_low,
                "triglycerides_high": triglycerides_high
            }
        }
    
    async def calculate_fall_risk(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate fall risk for elderly patients.
        """
        age = patient_data.get("age", 65)
        history_falls = patient_data.get("history_falls", 0)
        gait_unstable = patient_data.get("gait_unstable", False)
        vision_problems = patient_data.get("vision_problems", False)
        cognitive_impairment = patient_data.get("cognitive_impairment", False)
        medications_count = patient_data.get("medications_count", 0)
        orthostatic_hypotension = patient_data.get("orthostatic_hypotension", False)
        
        risk_score = 0
        
        if age > 65:
            risk_score += 1
        if history_falls > 0:
            risk_score += 2
        if gait_unstable:
            risk_score += 2
        if vision_problems:
            risk_score += 1
        if cognitive_impairment:
            risk_score += 1
        if medications_count > 4:
            risk_score += 1
        if orthostatic_hypotension:
            risk_score += 2
        
        risk_percentage = min(99, max(0, risk_score * 7))
        
        return {
            "score": risk_score,
            "percentage_risk": f"{risk_percentage}%",
            "risk_level": self._get_risk_level(risk_percentage),
            "factors": {
                "age": age,
                "history_falls": history_falls,
                "gait_unstable": gait_unstable,
                "vision_problems": vision_problems,
                "cognitive_impairment": cognitive_impairment,
                "medications_count": medications_count,
                "orthostatic_hypotension": orthostatic_hypotension
            }
        }
    
    def _get_risk_level(self, risk_percentage: float) -> str:
        """
        Convert risk percentage to risk level.
        """
        risk_percentage = float(risk_percentage.replace('%', ''))
        
        if risk_percentage < 10:
            return "Low"
        elif risk_percentage < 20:
            return "Moderate"
        elif risk_percentage < 30:
            return "High"
        else:
            return "Very High"
    
    def _combine_risks(self, cv_risk: Dict[str, Any], dm_risk: Dict[str, Any], fall_risk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine different risk assessments into an overall assessment.
        """
        # Calculate average risk score
        cv_score = float(cv_risk["percentage_risk"].replace('%', ''))
        dm_score = float(dm_risk["percentage_risk"].replace('%', ''))
        fall_score = float(fall_risk["percentage_risk"].replace('%', ''))
        
        avg_risk = (cv_score + dm_score + fall_score) / 3
        
        return {
            "average_risk": f"{avg_risk:.1f}%",
            "highest_risk": max(cv_score, dm_score, fall_score),
            "risk_priority": self._determine_priority(cv_risk, dm_risk, fall_risk),
            "recommendations": self._generate_recommendations(cv_risk, dm_risk, fall_risk)
        }
    
    def _determine_priority(self, cv_risk: Dict[str, Any], dm_risk: Dict[str, Any], fall_risk: Dict[str, Any]) -> str:
        """
        Determine which risk should be prioritized.
        """
        risks = {
            "Cardiovascular": float(cv_risk["percentage_risk"].replace('%', '')),
            "Diabetes": float(dm_risk["percentage_risk"].replace('%', '')),
            "Fall": float(fall_risk["percentage_risk"].replace('%', ''))
        }
        
        return max(risks, key=risks.get)
    
    def _generate_recommendations(self, cv_risk: Dict[str, Any], dm_risk: Dict[str, Any], fall_risk: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on risk levels.
        """
        recommendations = []
        
        cv_risk_level = cv_risk["risk_level"]
        dm_risk_level = dm_risk["risk_level"]
        fall_risk_level = fall_risk["risk_level"]
        
        if cv_risk_level in ["High", "Very High"]:
            recommendations.append("Consider statin therapy for cardiovascular risk reduction")
            recommendations.append("Lifestyle modifications: diet and exercise")
            recommendations.append("Regular blood pressure monitoring")
        
        if dm_risk_level in ["High", "Very High"]:
            recommendations.append("Screening for diabetes or pre-diabetes")
            recommendations.append("Weight management and dietary counseling")
            recommendations.append("Regular glucose monitoring")
        
        if fall_risk_level in ["High", "Very High"]:
            recommendations.append("Fall risk assessment and prevention program")
            recommendations.append("Home safety evaluation")
            recommendations.append("Strength and balance training")
        
        return recommendations
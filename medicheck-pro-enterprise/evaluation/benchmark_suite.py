"""
Benchmark Suite for Medical Assistant
Comprehensive benchmarking for medical AI agents
"""
import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid
import statistics
from enum import Enum


class BenchmarkCategory(Enum):
    TRIAGE = "triage"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    RESEARCH = "research"
    CONVERSATION = "conversation"


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test"""
    test_id: str
    benchmark_name: str
    category: BenchmarkCategory
    agent_id: str
    score: float
    max_score: float
    execution_time: float
    details: Dict[str, Any]
    timestamp: datetime


class MedicalBenchmarkSuite:
    """Comprehensive benchmark suite for medical agents"""
    
    def __init__(self):
        self.benchmarks: Dict[str, Callable] = {}
        self.results: List[BenchmarkResult] = []
        self._setup_default_benchmarks()
    
    def _setup_default_benchmarks(self):
        """Setup default medical benchmarks"""
        # Triage benchmarks
        self.register_benchmark(
            "emergency_triage_basic",
            BenchmarkCategory.TRIAGE,
            self._emergency_triage_basic
        )
        self.register_benchmark(
            "symptom_severity_assessment",
            BenchmarkCategory.TRIAGE,
            self._symptom_severity_assessment
        )
        
        # Diagnosis benchmarks
        self.register_benchmark(
            "common_condition_diagnosis",
            BenchmarkCategory.DIAGNOSIS,
            self._common_condition_diagnosis
        )
        self.register_benchmark(
            "rare_disease_identification",
            BenchmarkCategory.DIAGNOSIS,
            self._rare_disease_identification
        )
        
        # Treatment benchmarks
        self.register_benchmark(
            "drug_interaction_check",
            BenchmarkCategory.TREATMENT,
            self._drug_interaction_check
        )
        self.register_benchmark(
            "treatment_recommendation",
            BenchmarkCategory.TREATMENT,
            self._treatment_recommendation
        )
        
        # Research benchmarks
        self.register_benchmark(
            "medical_literature_search",
            BenchmarkCategory.RESEARCH,
            self._medical_literature_search
        )
        
        # Conversation benchmarks
        self.register_benchmark(
            "patient_communication",
            BenchmarkCategory.CONVERSATION,
            self._patient_communication
        )
    
    def register_benchmark(self, name: str, category: BenchmarkCategory, func: Callable):
        """Register a new benchmark function"""
        self.benchmarks[name] = {
            'function': func,
            'category': category
        }
    
    async def run_benchmark(self, 
                           benchmark_name: str, 
                           agent_func: Callable, 
                           agent_id: str,
                           **kwargs) -> BenchmarkResult:
        """Run a single benchmark test"""
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Benchmark {benchmark_name} not found")
        
        benchmark_info = self.benchmarks[benchmark_name]
        start_time = time.time()
        
        try:
            # Execute the benchmark
            result = await benchmark_info['function'](agent_func, **kwargs)
            
            execution_time = time.time() - start_time
            
            # Create benchmark result
            benchmark_result = BenchmarkResult(
                test_id=str(uuid.uuid4()),
                benchmark_name=benchmark_name,
                category=benchmark_info['category'],
                agent_id=agent_id,
                score=result.get('score', 0.0),
                max_score=result.get('max_score', 1.0),
                execution_time=execution_time,
                details=result.get('details', {}),
                timestamp=datetime.now()
            )
            
            # Store the result
            self.results.append(benchmark_result)
            
            return benchmark_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Create error result
            error_result = BenchmarkResult(
                test_id=str(uuid.uuid4()),
                benchmark_name=benchmark_name,
                category=benchmark_info['category'],
                agent_id=agent_id,
                score=0.0,
                max_score=1.0,
                execution_time=execution_time,
                details={'error': str(e)},
                timestamp=datetime.now()
            )
            
            self.results.append(error_result)
            return error_result
    
    async def run_comprehensive_benchmark(self, agent_func: Callable, agent_id: str) -> Dict[str, Any]:
        """Run all benchmarks for an agent"""
        start_time = time.time()
        
        category_results = {}
        all_results = []
        
        for name, info in self.benchmarks.items():
            result = await self.run_benchmark(name, agent_func, agent_id)
            all_results.append(result)
            
            # Group by category
            category = info['category'].value
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(result)
        
        # Calculate category averages
        category_averages = {}
        for category, results in category_results.items():
            scores = [r.score for r in results]
            category_averages[category] = {
                'average_score': statistics.mean(scores) if scores else 0.0,
                'median_score': statistics.median(scores) if scores else 0.0,
                'min_score': min(scores) if scores else 0.0,
                'max_score': max(scores) if scores else 0.0,
                'std_deviation': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                'total_tests': len(scores)
            }
        
        # Calculate overall metrics
        all_scores = [r.score for r in all_results]
        overall_metrics = {
            'average_score': statistics.mean(all_scores) if all_scores else 0.0,
            'median_score': statistics.median(all_scores) if all_scores else 0.0,
            'overall_ranking': self._calculate_ranking(agent_id),
            'total_tests_run': len(all_scores),
            'total_execution_time': time.time() - start_time
        }
        
        return {
            'agent_id': agent_id,
            'timestamp': datetime.now().isoformat(),
            'category_results': category_averages,
            'overall_metrics': overall_metrics,
            'individual_results': [
                {
                    'test_id': r.test_id,
                    'benchmark_name': r.benchmark_name,
                    'category': r.category.value,
                    'score': r.score,
                    'execution_time': r.execution_time
                } for r in all_results
            ]
        }
    
    def _calculate_ranking(self, agent_id: str) -> int:
        """Calculate ranking for an agent based on performance"""
        agent_results = [r for r in self.results if r.agent_id == agent_id]
        if not agent_results:
            return -1  # Not ranked if no results
        
        avg_score = statistics.mean([r.score for r in agent_results])
        
        # Get all unique agent average scores and rank this agent
        all_agent_scores = {}
        for result in self.results:
            if result.agent_id not in all_agent_scores:
                agent_agent_results = [r for r in self.results if r.agent_id == result.agent_id]
                all_agent_scores[result.agent_id] = statistics.mean([r.score for r in agent_agent_results])
        
        sorted_scores = sorted(all_agent_scores.values(), reverse=True)
        agent_rank = sorted_scores.index(avg_score) + 1
        
        return agent_rank
    
    async def _emergency_triage_basic(self, agent_func: Callable, **kwargs) -> Dict[str, Any]:
        """Benchmark for basic emergency triage capabilities"""
        test_cases = [
            {
                "input": "Patient has severe chest pain, difficulty breathing, and appears pale. What is the triage level?",
                "expected_output": "immediate/emergent",
                "severity_weight": 1.0
            },
            {
                "input": "Patient has minor cut on finger with minimal bleeding. What is the triage level?",
                "expected_output": "non-urgent",
                "severity_weight": 0.3
            },
            {
                "input": "Patient has high fever (103°F) and chills. What is the triage level?",
                "expected_output": "urgent",
                "severity_weight": 0.7
            }
        ]
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                response = await agent_func(case["input"])
                
                # Simple keyword matching for triage level
                response_lower = response.lower()
                expected_lower = case["expected_output"].lower()
                
                if expected_lower in response_lower or any(word in response_lower for word in expected_lower.split('/')):
                    correct += 1
            except:
                pass  # Count as incorrect if agent fails
        
        score = correct / total if total > 0 else 0.0
        max_score = 1.0
        
        return {
            'score': score,
            'max_score': max_score,
            'details': {
                'correct_cases': correct,
                'total_cases': total,
                'test_cases': test_cases
            }
        }
    
    async def _symptom_severity_assessment(self, agent_func: Callable, **kwargs) -> Dict[str, Any]:
        """Benchmark for symptom severity assessment"""
        test_cases = [
            {
                "input": "Patient reports headache, mild fever (100°F), and fatigue. How would you rate the severity?",
                "expected_keywords": ["mild", "low", "minor"],
                "severity_weight": 0.4
            },
            {
                "input": "Patient reports severe abdominal pain, vomiting, and inability to keep food down for 2 days. How would you rate the severity?",
                "expected_keywords": ["severe", "high", "urgent", "serious"],
                "severity_weight": 1.0
            },
            {
                "input": "Patient reports occasional joint stiffness in the morning. How would you rate the severity?",
                "expected_keywords": ["mild", "low", "minor"],
                "severity_weight": 0.3
            }
        ]
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                response = await agent_func(case["input"])
                
                # Check if response contains expected keywords
                response_lower = response.lower()
                if any(keyword in response_lower for keyword in case["expected_keywords"]):
                    correct += 1
            except:
                pass  # Count as incorrect if agent fails
        
        score = correct / total if total > 0 else 0.0
        max_score = 1.0
        
        return {
            'score': score,
            'max_score': max_score,
            'details': {
                'correct_cases': correct,
                'total_cases': total,
                'test_cases': test_cases
            }
        }
    
    async def _common_condition_diagnosis(self, agent_func: Callable, **kwargs) -> Dict[str, Any]:
        """Benchmark for common condition diagnosis"""
        test_cases = [
            {
                "input": "Patient has runny nose, sneezing, mild sore throat, and low-grade fever. What condition might this be?",
                "expected_conditions": ["cold", "common cold", "upper respiratory infection"],
                "condition_weight": 0.6
            },
            {
                "input": "Patient has high fever, body aches, fatigue, and sudden onset of symptoms during flu season. What condition might this be?",
                "expected_conditions": ["flu", "influenza"],
                "condition_weight": 0.8
            },
            {
                "input": "Patient has persistent cough, fever, and difficulty breathing. What condition might this be?",
                "expected_conditions": ["pneumonia", "lung infection"],
                "condition_weight": 1.0
            }
        ]
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                response = await agent_func(case["input"])
                
                # Check if response contains expected conditions
                response_lower = response.lower()
                if any(condition.lower() in response_lower for condition in case["expected_conditions"]):
                    correct += 1
            except:
                pass  # Count as incorrect if agent fails
        
        score = correct / total if total > 0 else 0.0
        max_score = 1.0
        
        return {
            'score': score,
            'max_score': max_score,
            'details': {
                'correct_cases': correct,
                'total_cases': total,
                'test_cases': test_cases
            }
        }
    
    async def _rare_disease_identification(self, agent_func: Callable, **kwargs) -> Dict[str, Any]:
        """Benchmark for rare disease identification"""
        test_cases = [
            {
                "input": "Patient has chronic fatigue, joint pain, skin rashes that worsen with sun exposure, and kidney problems. What rare condition might this be?",
                "expected_conditions": ["lupus", "systemic lupus erythematosus"],
                "condition_weight": 1.0
            },
            {
                "input": "Patient has progressive muscle weakness, difficulty breathing, and symptoms that worsen throughout the day but improve with rest. What rare condition might this be?",
                "expected_conditions": ["myasthenia gravis"],
                "condition_weight": 0.9
            }
        ]
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                response = await agent_func(case["input"])
                
                # Check if response contains expected conditions
                response_lower = response.lower()
                if any(condition.lower() in response_lower for condition in case["expected_conditions"]):
                    correct += 1
            except:
                pass  # Count as incorrect if agent fails
        
        # Lower expectations for rare diseases
        score = (correct / total) * 0.7 if total > 0 else 0.0
        max_score = 0.7  # Lower max score for rare disease identification
        
        return {
            'score': score,
            'max_score': max_score,
            'details': {
                'correct_cases': correct,
                'total_cases': total,
                'test_cases': test_cases
            }
        }
    
    async def _drug_interaction_check(self, agent_func: Callable, **kwargs) -> Dict[str, Any]:
        """Benchmark for drug interaction checking"""
        test_cases = [
            {
                "input": "Can a patient take warfarin and ibuprofen together?",
                "expected_response": "not recommended",
                "risk_level": "high"
            },
            {
                "input": "Can a patient take aspirin and vitamin K together?",
                "expected_response": "interaction possible",
                "risk_level": "moderate"
            },
            {
                "input": "Can a patient take acetaminophen and vitamin C together?",
                "expected_response": "generally safe",
                "risk_level": "low"
            }
        ]
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                response = await agent_func(case["input"])
                
                # Check if response mentions the expected risk level
                response_lower = response.lower()
                if case["expected_response"] in response_lower:
                    correct += 1
            except:
                pass  # Count as incorrect if agent fails
        
        score = correct / total if total > 0 else 0.0
        max_score = 1.0
        
        return {
            'score': score,
            'max_score': max_score,
            'details': {
                'correct_cases': correct,
                'total_cases': total,
                'test_cases': test_cases
            }
        }
    
    async def _treatment_recommendation(self, agent_func: Callable, **kwargs) -> Dict[str, Any]:
        """Benchmark for treatment recommendations"""
        test_cases = [
            {
                "input": "Patient has mild headache. What treatment do you recommend?",
                "expected_elements": ["rest", "water", "acetaminophen", "ibuprofen", "hydration"],
                "severity": "mild"
            },
            {
                "input": "Patient has severe allergic reaction with difficulty breathing. What treatment do you recommend?",
                "expected_elements": ["emergency", "epinephrine", "911", "immediate", "medical attention"],
                "severity": "severe"
            }
        ]
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                response = await agent_func(case["input"])
                
                # Check if response contains expected treatment elements
                response_lower = response.lower()
                if any(element.lower() in response_lower for element in case["expected_elements"]):
                    correct += 1
            except:
                pass  # Count as incorrect if agent fails
        
        score = correct / total if total > 0 else 0.0
        max_score = 1.0
        
        return {
            'score': score,
            'max_score': max_score,
            'details': {
                'correct_cases': correct,
                'total_cases': total,
                'test_cases': test_cases
            }
        }
    
    async def _medical_literature_search(self, agent_func: Callable, **kwargs) -> Dict[str, Any]:
        """Benchmark for medical literature search capabilities"""
        test_cases = [
            {
                "input": "Find recent studies about COVID-19 treatment with antivirals",
                "expected_elements": ["study", "research", "clinical", "trial", "antiviral", "treatment"],
                "recency_requirement": "last 2 years"
            },
            {
                "input": "Find information about diabetes management guidelines",
                "expected_elements": ["guidelines", "management", "diabetes", "treatment", "recommendations"],
                "recency_requirement": "last 5 years"
            }
        ]
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                response = await agent_func(case["input"])
                
                # Check if response contains expected elements
                response_lower = response.lower()
                if any(element.lower() in response_lower for element in case["expected_elements"]):
                    correct += 1
            except:
                pass  # Count as incorrect if agent fails
        
        score = correct / total if total > 0 else 0.0
        max_score = 1.0
        
        return {
            'score': score,
            'max_score': max_score,
            'details': {
                'correct_cases': correct,
                'total_cases': total,
                'test_cases': test_cases
            }
        }
    
    async def _patient_communication(self, agent_func: Callable, **kwargs) -> Dict[str, Any]:
        """Benchmark for patient communication skills"""
        test_cases = [
            {
                "input": "Explain high blood pressure to a patient in simple terms",
                "evaluation_criteria": ["simple language", "clear explanation", "reassurance", "actionable advice"],
                "safety_check": True
            },
            {
                "input": "How would you comfort a patient who is anxious about a medical procedure?",
                "evaluation_criteria": ["empathy", "reassurance", "information", "support"],
                "safety_check": True
            }
        ]
        
        # For this benchmark, we'll evaluate based on response quality
        total_score = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                response = await agent_func(case["input"])
                
                # Evaluate response quality based on criteria
                response_lower = response.lower()
                criteria_met = sum(1 for criterion in case["evaluation_criteria"] 
                                 if criterion.replace(" ", "") in response_lower or 
                                 any(word in response_lower for word in criterion.split()))
                
                # Normalize score based on criteria met
                case_score = criteria_met / len(case["evaluation_criteria"])
                total_score += case_score
            except:
                pass  # Add 0 to total_score if agent fails
        
        score = total_score / total if total > 0 else 0.0
        max_score = 1.0
        
        return {
            'score': score,
            'max_score': max_score,
            'details': {
                'average_criteria_met': total_score,
                'total_cases': total,
                'test_cases': test_cases
            }
        }
    
    def get_leaderboard(self, category: Optional[BenchmarkCategory] = None) -> List[Dict[str, Any]]:
        """Get leaderboard of agents by performance"""
        # Group results by agent
        agent_scores = {}
        
        for result in self.results:
            if category and result.category != category:
                continue
                
            agent_id = result.agent_id
            if agent_id not in agent_scores:
                agent_scores[agent_id] = []
            agent_scores[agent_id].append(result.score)
        
        # Calculate average scores
        leaderboard = []
        for agent_id, scores in agent_scores.items():
            avg_score = statistics.mean(scores)
            leaderboard.append({
                'agent_id': agent_id,
                'average_score': avg_score,
                'total_tests': len(scores),
                'score_std_dev': statistics.stdev(scores) if len(scores) > 1 else 0
            })
        
        # Sort by average score (descending)
        leaderboard.sort(key=lambda x: x['average_score'], reverse=True)
        
        return leaderboard
    
    def get_category_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics by category"""
        category_stats = {}
        
        for category in BenchmarkCategory:
            category_results = [r for r in self.results if r.category == category]
            if category_results:
                scores = [r.score for r in category_results]
                category_stats[category.value] = {
                    'average_score': statistics.mean(scores),
                    'median_score': statistics.median(scores),
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'total_tests': len(scores)
                }
        
        return category_stats


class MedicalBenchmarkRunner:
    """Runner to execute benchmark suites"""
    
    def __init__(self):
        self.suite = MedicalBenchmarkSuite()
    
    async def run_agent_benchmark(self, 
                                 agent_func: Callable, 
                                 agent_id: str,
                                 run_comprehensive: bool = True) -> Dict[str, Any]:
        """Run benchmark for a single agent"""
        if run_comprehensive:
            return await self.suite.run_comprehensive_benchmark(agent_func, agent_id)
        else:
            # Run a quick benchmark with a subset of tests
            quick_results = []
            quick_benchmarks = ["emergency_triage_basic", "common_condition_diagnosis", "patient_communication"]
            
            for benchmark_name in quick_benchmarks:
                if benchmark_name in self.suite.benchmarks:
                    result = await self.suite.run_benchmark(benchmark_name, agent_func, agent_id)
                    quick_results.append(result)
            
            return {
                'agent_id': agent_id,
                'timestamp': datetime.now().isoformat(),
                'quick_benchmark_results': [
                    {
                        'test_id': r.test_id,
                        'benchmark_name': r.benchmark_name,
                        'category': r.category.value,
                        'score': r.score,
                        'execution_time': r.execution_time
                    } for r in quick_results
                ]
            }
    
    def get_benchmark_report(self) -> Dict[str, Any]:
        """Generate a comprehensive benchmark report"""
        return {
            'total_results': len(self.suite.results),
            'total_agents_tested': len(set(r.agent_id for r in self.suite.results)),
            'benchmarks_available': list(self.suite.benchmarks.keys()),
            'category_summary': self.suite.get_category_summary(),
            'leaderboard': self.suite.get_leaderboard(),
            'timestamp': datetime.now().isoformat()
        }


# Global benchmark runner instance
benchmark_runner = MedicalBenchmarkRunner()
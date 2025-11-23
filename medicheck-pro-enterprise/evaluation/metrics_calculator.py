"""
Metrics Calculator for Medical Assistant Evaluation
Calculates accuracy, precision, recall, and other medical-specific metrics
"""
import asyncio
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class ClassificationMetrics:
    """Metrics for classification tasks"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    specificity: float
    sensitivity: float
    auc_roc: Optional[float] = None


@dataclass
class RegressionMetrics:
    """Metrics for regression tasks"""
    mse: float
    rmse: float
    mae: float
    r2_score: float
    explained_variance: float


class MedicalMetricsCalculator:
    """Calculator for medical-specific evaluation metrics"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def calculate_classification_metrics(self, 
                                            y_true: List[int], 
                                            y_pred: List[int],
                                            y_scores: Optional[List[float]] = None) -> ClassificationMetrics:
        """Calculate classification metrics for medical predictions"""
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have the same length")
        
        # Calculate confusion matrix components
        tp = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 1)  # True Positives
        tn = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 0)  # True Negatives
        fp = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 1)  # False Positives
        fn = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 0)  # False Negatives
        
        total = len(y_true)
        
        # Calculate metrics
        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # Same as sensitivity
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        sensitivity = recall  # Sensitivity is the same as recall
        
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Calculate AUC-ROC if scores are provided
        auc_roc = None
        if y_scores is not None and len(y_scores) == len(y_true):
            auc_roc = self._calculate_auc_roc(y_true, y_scores)
        
        return ClassificationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            specificity=specificity,
            sensitivity=sensitivity,
            auc_roc=auc_roc
        )
    
    async def calculate_regression_metrics(self, 
                                         y_true: List[float], 
                                         y_pred: List[float]) -> RegressionMetrics:
        """Calculate regression metrics"""
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have the same length")
        
        if len(y_true) == 0:
            return RegressionMetrics(mse=0.0, rmse=0.0, mae=0.0, r2_score=0.0, explained_variance=0.0)
        
        # Convert to numpy arrays for calculations
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        
        # Calculate metrics
        mse = np.mean((y_true_arr - y_pred_arr) ** 2)
        rmse = math.sqrt(mse)
        mae = np.mean(np.abs(y_true_arr - y_pred_arr))
        
        # Calculate R² score
        ss_res = np.sum((y_true_arr - y_pred_arr) ** 2)
        ss_tot = np.sum((y_true_arr - np.mean(y_true_arr)) ** 2)
        r2_score = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        # Calculate explained variance
        explained_variance = 1 - (np.var(y_true_arr - y_pred_arr) / np.var(y_true_arr)) if np.var(y_true_arr) != 0 else 0.0
        
        return RegressionMetrics(
            mse=mse,
            rmse=rmse,
            mae=mae,
            r2_score=r2_score,
            explained_variance=explained_variance
        )
    
    async def calculate_medical_specific_metrics(self, 
                                               true_conditions: List[str], 
                                               predicted_conditions: List[str],
                                               severity_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Calculate medical-specific metrics considering condition severity"""
        if severity_weights is None:
            severity_weights = {
                'common_cold': 0.1,
                'flu': 0.3,
                'pneumonia': 0.8,
                'heart_attack': 1.0,
                'stroke': 1.0
            }
        
        # Calculate weighted accuracy considering severity
        total_weight = 0
        correct_weight = 0
        
        for true_condition, pred_condition in zip(true_conditions, predicted_conditions):
            weight = severity_weights.get(true_condition, 0.5)  # Default weight
            total_weight += weight
            
            if true_condition == pred_condition:
                correct_weight += weight
        
        weighted_accuracy = correct_weight / total_weight if total_weight > 0 else 0.0
        
        # Calculate condition-specific metrics
        unique_conditions = set(true_conditions + predicted_conditions)
        condition_metrics = {}
        
        for condition in unique_conditions:
            condition_indices = [i for i, c in enumerate(true_conditions) if c == condition]
            if condition_indices:
                condition_true = [true_conditions[i] for i in condition_indices]
                condition_pred = [predicted_conditions[i] for i in condition_indices]
                
                # Calculate metrics for this specific condition
                correct = sum(1 for t, p in zip(condition_true, condition_pred) if t == p)
                condition_accuracy = correct / len(condition_true)
                
                condition_metrics[condition] = {
                    'accuracy': condition_accuracy,
                    'count': len(condition_true),
                    'weight': severity_weights.get(condition, 0.5)
                }
        
        return {
            'weighted_accuracy': weighted_accuracy,
            'condition_metrics': condition_metrics,
            'total_conditions_evaluated': len(true_conditions)
        }
    
    async def calculate_risk_assessment_metrics(self, 
                                              true_risk_levels: List[int],  # 0-5 scale
                                              predicted_risk_levels: List[int]) -> Dict[str, float]:
        """Calculate metrics for risk assessment tasks"""
        if len(true_risk_levels) != len(predicted_risk_levels):
            raise ValueError("true_risk_levels and predicted_risk_levels must have the same length")
        
        if len(true_risk_levels) == 0:
            return {
                'mean_absolute_error': 0.0,
                'mean_squared_error': 0.0,
                'categorized_accuracy': 0.0,
                'high_risk_detection_rate': 0.0,
                'low_risk_detection_rate': 0.0
            }
        
        # Calculate basic metrics
        abs_errors = [abs(t - p) for t, p in zip(true_risk_levels, predicted_risk_levels)]
        squared_errors = [e**2 for e in abs_errors]
        
        mae = sum(abs_errors) / len(abs_errors)
        mse = sum(squared_errors) / len(squared_errors)
        
        # Calculate categorized accuracy (correct risk category)
        categorized_correct = sum(1 for t, p in zip(true_risk_levels, predicted_risk_levels) if t == p)
        categorized_accuracy = categorized_correct / len(true_risk_levels)
        
        # Calculate high-risk detection (typically risk >= 4)
        high_risk_indices = [i for i, risk in enumerate(true_risk_levels) if risk >= 4]
        if high_risk_indices:
            high_risk_correct = sum(1 for i in high_risk_indices 
                                  if predicted_risk_levels[i] >= 4)
            high_risk_detection_rate = high_risk_correct / len(high_risk_indices)
        else:
            high_risk_detection_rate = 0.0
        
        # Calculate low-risk detection (typically risk <= 2)
        low_risk_indices = [i for i, risk in enumerate(true_risk_levels) if risk <= 2]
        if low_risk_indices:
            low_risk_correct = sum(1 for i in low_risk_indices 
                                 if predicted_risk_levels[i] <= 2)
            low_risk_detection_rate = low_risk_correct / len(low_risk_indices)
        else:
            low_risk_detection_rate = 0.0
        
        return {
            'mean_absolute_error': mae,
            'mean_squared_error': mse,
            'categorized_accuracy': categorized_accuracy,
            'high_risk_detection_rate': high_risk_detection_rate,
            'low_risk_detection_rate': low_risk_detection_rate
        }
    
    async def calculate_conversation_quality_metrics(self, 
                                                   conversations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate metrics for conversation quality"""
        if not conversations:
            return {
                'average_response_length': 0.0,
                'relevance_score': 0.0,
                'coherence_score': 0.0,
                'medical_accuracy_score': 0.0,
                'patient_satisfaction_estimate': 0.0
            }
        
        total_response_length = 0
        total_relevance = 0
        total_coherence = 0
        total_accuracy = 0
        total_satisfaction = 0
        valid_conversations = 0
        
        for conv in conversations:
            if 'response' in conv and 'query' in conv:
                response = conv['response']
                query = conv['query']
                
                # Calculate response length
                response_length = len(response.split())
                total_response_length += response_length
                
                # Calculate relevance (simple keyword overlap)
                query_words = set(query.lower().split())
                response_words = set(response.lower().split())
                if query_words:
                    relevance = len(query_words.intersection(response_words)) / len(query_words)
                else:
                    relevance = 1.0
                total_relevance += relevance
                
                # Calculate coherence (simple metric based on response structure)
                sentences = response.split('.')
                avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()]) if sentences else 0
                coherence = min(1.0, avg_sentence_length / 20)  # Normalize to 0-1
                total_coherence += coherence
                
                # Medical accuracy (if reference is available)
                if 'reference_answer' in conv:
                    ref = conv['reference_answer']
                    accuracy = self._calculate_similarity(response.lower(), ref.lower())
                    total_accuracy += accuracy
                else:
                    total_accuracy += 0.5  # Default medium accuracy
                
                # Patient satisfaction estimate (if feedback is available)
                if 'satisfaction' in conv:
                    total_satisfaction += conv['satisfaction']
                else:
                    total_satisfaction += 0.7  # Default medium satisfaction
                
                valid_conversations += 1
        
        if valid_conversations > 0:
            return {
                'average_response_length': total_response_length / valid_conversations,
                'relevance_score': total_relevance / valid_conversations,
                'coherence_score': total_coherence / valid_conversations,
                'medical_accuracy_score': total_accuracy / valid_conversations,
                'patient_satisfaction_estimate': total_satisfaction / valid_conversations
            }
        else:
            return {
                'average_response_length': 0.0,
                'relevance_score': 0.0,
                'coherence_score': 0.0,
                'medical_accuracy_score': 0.0,
                'patient_satisfaction_estimate': 0.0
            }
    
    def _calculate_auc_roc(self, y_true: List[int], y_scores: List[float]) -> float:
        """Calculate AUC-ROC score"""
        # Sort by scores in descending order
        sorted_pairs = sorted(zip(y_scores, y_true), key=lambda x: x[0], reverse=True)
        
        # Calculate TPR and FPR at each threshold
        tpr_values = []
        fpr_values = []
        
        total_pos = sum(y_true)
        total_neg = len(y_true) - total_pos
        
        if total_pos == 0 or total_neg == 0:
            return 1.0 if total_pos == 0 else 0.0
        
        tp = 0
        fp = 0
        
        for score, true_label in sorted_pairs:
            if true_label == 1:
                tp += 1
            else:
                fp += 1
            
            tpr = tp / total_pos
            fpr = fp / total_neg
            tpr_values.append(tpr)
            fpr_values.append(fpr)
        
        # Calculate AUC using trapezoidal rule
        auc = 0
        for i in range(1, len(fpr_values)):
            auc += (fpr_values[i] - fpr_values[i-1]) * (tpr_values[i] + tpr_values[i-1]) / 2
        
        return abs(auc)
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
        
        # Simple word overlap for demonstration
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 1.0
        
        return len(intersection) / len(union)


class MedicalEvaluationDashboard:
    """Dashboard for visualizing medical evaluation metrics"""
    
    def __init__(self):
        self.calculator = MedicalMetricsCalculator()
        self.evaluation_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def add_evaluation(self, evaluation_data: Dict[str, Any]):
        """Add evaluation data to history"""
        evaluation_data['timestamp'] = datetime.now().isoformat()
        async with self._lock:
            self.evaluation_history.append(evaluation_data)
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of overall performance"""
        if not self.evaluation_history:
            return {
                'total_evaluations': 0,
                'average_metrics': {},
                'trend_analysis': {}
            }
        
        # Aggregate metrics from all evaluations
        classification_metrics = []
        regression_metrics = []
        medical_metrics = []
        
        for eval_data in self.evaluation_history:
            if 'classification_metrics' in eval_data:
                classification_metrics.append(eval_data['classification_metrics'])
            if 'regression_metrics' in eval_data:
                regression_metrics.append(eval_data['regression_metrics'])
            if 'medical_metrics' in eval_data:
                medical_metrics.append(eval_data['medical_metrics'])
        
        # Calculate averages
        avg_classification = {}
        if classification_metrics:
            keys = classification_metrics[0].__dict__.keys()
            for key in keys:
                values = [getattr(m, key) for m in classification_metrics if getattr(m, key) is not None]
                if values:
                    avg_classification[key] = sum(values) / len(values)
        
        avg_regression = {}
        if regression_metrics:
            keys = regression_metrics[0].__dict__.keys()
            for key in keys:
                values = [getattr(m, key) for m in regression_metrics]
                avg_regression[key] = sum(values) / len(values)
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'average_classification_metrics': avg_classification,
            'average_regression_metrics': avg_regression,
            'medical_metrics_summary': medical_metrics[-1] if medical_metrics else {},
            'latest_evaluation': self.evaluation_history[-1]['timestamp']
        }
    
    async def get_agent_comparison(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Compare performance across different agents"""
        agent_comparison = {}
        
        for agent_id in agent_ids:
            agent_evals = [e for e in self.evaluation_history if e.get('agent_id') == agent_id]
            
            if agent_evals:
                # Calculate average metrics for this agent
                classification_metrics = [e['classification_metrics'] for e in agent_evals 
                                        if 'classification_metrics' in e]
                
                if classification_metrics:
                    avg_acc = np.mean([m.accuracy for m in classification_metrics])
                    avg_prec = np.mean([m.precision for m in classification_metrics])
                    avg_rec = np.mean([m.recall for m in classification_metrics])
                    avg_f1 = np.mean([m.f1_score for m in classification_metrics])
                    
                    agent_comparison[agent_id] = {
                        'average_accuracy': avg_acc,
                        'average_precision': avg_prec,
                        'average_recall': avg_rec,
                        'average_f1_score': avg_f1,
                        'evaluation_count': len(classification_metrics)
                    }
        
        return agent_comparison


# Global metrics calculator instance
metrics_calculator = MedicalEvaluationDashboard()
"""
Metrics collector for LLM providers
"""

import time
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.models.llm import ProviderMetrics, ProviderRanking, ComplexityLevel, LLMProvider
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and analyze metrics for LLM providers"""
    
    def __init__(self):
        self.metrics_key_prefix = "llm_metrics"
        self.daily_metrics_ttl = 86400 * 7  # Keep daily metrics for 7 days
    
    async def record_request(
        self, 
        provider: str, 
        complexity: ComplexityLevel,
        latency_ms: int, 
        cost_usd: float, 
        success: bool,
        accuracy_score: Optional[float] = None
    ):
        """Record metrics for a request"""
        try:
            timestamp = datetime.now()
            date_key = timestamp.strftime("%Y-%m-%d")
            
            # Daily metrics key
            daily_key = f"{self.metrics_key_prefix}:daily:{provider}:{date_key}"
            
            # Get existing metrics
            existing_data = await redis_manager.get(daily_key)
            if existing_data:
                metrics_data = json.loads(existing_data)
            else:
                metrics_data = {
                    "provider_name": provider,
                    "date": date_key,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_latency_ms": 0,
                    "total_cost_usd": 0.0,
                    "accuracy_scores": [],
                    "complexity_breakdown": {
                        "simple": 0,
                        "complex": 0,
                        "structured": 0,
                        "multimedia": 0
                    },
                    "last_used": None
                }
            
            # Update metrics
            metrics_data["total_requests"] += 1
            metrics_data["last_used"] = timestamp.isoformat()
            
            if success:
                metrics_data["successful_requests"] += 1
                metrics_data["total_latency_ms"] += latency_ms
                metrics_data["total_cost_usd"] += cost_usd
                
                if accuracy_score is not None:
                    metrics_data["accuracy_scores"].append(accuracy_score)
            else:
                metrics_data["failed_requests"] += 1
            
            # Update complexity breakdown
            if complexity.value in metrics_data["complexity_breakdown"]:
                metrics_data["complexity_breakdown"][complexity.value] += 1
            
            # Save updated metrics
            await redis_manager.set(
                daily_key, 
                json.dumps(metrics_data), 
                ttl=self.daily_metrics_ttl
            )
            
            # Also update real-time metrics (shorter TTL)
            realtime_key = f"{self.metrics_key_prefix}:realtime:{provider}"
            await redis_manager.set(
                realtime_key,
                json.dumps({
                    "last_request": timestamp.isoformat(),
                    "last_latency_ms": latency_ms if success else None,
                    "last_cost_usd": cost_usd if success else None,
                    "last_success": success
                }),
                ttl=3600  # 1 hour
            )
            
        except Exception as e:
            logger.error(f"Error recording metrics for {provider}: {e}")
    
    async def get_provider_metrics(self, provider: str, days: int = 7) -> ProviderMetrics:
        """Get aggregated metrics for a provider"""
        try:
            # Get metrics for the last N days
            total_requests = 0
            successful_requests = 0
            failed_requests = 0
            total_latency_ms = 0
            total_cost_usd = 0.0
            accuracy_scores = []
            last_used = None
            
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_key = f"{self.metrics_key_prefix}:daily:{provider}:{date}"
                
                data = await redis_manager.get(daily_key)
                if data:
                    metrics_data = json.loads(data)
                    total_requests += metrics_data.get("total_requests", 0)
                    successful_requests += metrics_data.get("successful_requests", 0)
                    failed_requests += metrics_data.get("failed_requests", 0)
                    total_latency_ms += metrics_data.get("total_latency_ms", 0)
                    total_cost_usd += metrics_data.get("total_cost_usd", 0.0)
                    accuracy_scores.extend(metrics_data.get("accuracy_scores", []))
                    
                    if metrics_data.get("last_used"):
                        last_used_date = datetime.fromisoformat(metrics_data["last_used"])
                        if not last_used or last_used_date > last_used:
                            last_used = last_used_date
            
            # Calculate availability
            availability_pct = 100.0
            if total_requests > 0:
                availability_pct = (successful_requests / total_requests) * 100.0
            
            # Calculate average accuracy
            accuracy_score = 0.0
            if accuracy_scores:
                accuracy_score = sum(accuracy_scores) / len(accuracy_scores)
            
            return ProviderMetrics(
                provider_name=provider,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                total_latency_ms=total_latency_ms,
                total_cost_usd=total_cost_usd,
                accuracy_score=accuracy_score,
                availability_pct=availability_pct,
                last_used=last_used
            )
            
        except Exception as e:
            logger.error(f"Error getting metrics for {provider}: {e}")
            return ProviderMetrics(provider_name=provider)
    
    async def get_all_provider_metrics(self, days: int = 7) -> Dict[str, ProviderMetrics]:
        """Get metrics for all providers"""
        providers = [p.value for p in LLMProvider if p.value not in ["regex", "basic"]]
        metrics = {}
        
        for provider in providers:
            metrics[provider] = await self.get_provider_metrics(provider, days)
        
        return metrics
    
    async def get_provider_ranking(self, complexity: Optional[ComplexityLevel] = None) -> List[ProviderRanking]:
        """Get provider ranking based on performance metrics"""
        try:
            all_metrics = await self.get_all_provider_metrics()
            rankings = []
            
            for provider, metrics in all_metrics.items():
                if metrics.total_requests == 0:
                    continue
                
                # Calculate composite score
                factors = {}
                
                # Success rate (40%)
                success_rate = metrics.success_rate / 100.0
                factors["success_rate"] = success_rate * 0.4
                
                # Latency (30% - lower is better)
                avg_latency = metrics.avg_latency_ms
                if avg_latency > 0:
                    # Normalize latency (assume 5000ms is worst case)
                    latency_score = max(0, 1 - (avg_latency / 5000.0))
                    factors["latency"] = latency_score * 0.3
                else:
                    factors["latency"] = 0.0
                
                # Cost efficiency (20% - lower cost is better)
                avg_cost = metrics.avg_cost_per_request
                if avg_cost > 0:
                    # Normalize cost (assume $0.10 per request is worst case)
                    cost_score = max(0, 1 - (avg_cost / 0.10))
                    factors["cost_efficiency"] = cost_score * 0.2
                else:
                    factors["cost_efficiency"] = 0.2  # Free is best
                
                # Accuracy (10%)
                accuracy_score = metrics.accuracy_score / 100.0 if metrics.accuracy_score > 0 else 0.5
                factors["accuracy"] = accuracy_score * 0.1
                
                # Calculate total score
                total_score = sum(factors.values())
                
                # Determine recommended complexity levels
                recommended_for = []
                if provider == "deepseek":
                    recommended_for = [ComplexityLevel.SIMPLE, ComplexityLevel.COMPLEX]
                elif provider == "ollama":
                    recommended_for = [ComplexityLevel.SIMPLE]
                elif provider == "gemini":
                    recommended_for = [ComplexityLevel.COMPLEX, ComplexityLevel.MULTIMEDIA]
                elif provider == "openai":
                    recommended_for = [ComplexityLevel.STRUCTURED, ComplexityLevel.COMPLEX]
                elif provider == "anthropic":
                    recommended_for = [ComplexityLevel.MULTIMEDIA, ComplexityLevel.STRUCTURED]
                
                rankings.append(ProviderRanking(
                    provider=provider,
                    score=total_score,
                    factors=factors,
                    recommended_for=recommended_for
                ))
            
            # Sort by score (descending)
            rankings.sort(key=lambda x: x.score, reverse=True)
            
            return rankings
            
        except Exception as e:
            logger.error(f"Error calculating provider ranking: {e}")
            return []
    
    async def get_cost_summary(self, days: int = 7) -> Dict[str, float]:
        """Get cost summary by provider"""
        try:
            all_metrics = await self.get_all_provider_metrics(days)
            cost_summary = {}
            
            for provider, metrics in all_metrics.items():
                cost_summary[provider] = metrics.total_cost_usd
            
            return cost_summary
            
        except Exception as e:
            logger.error(f"Error getting cost summary: {e}")
            return {}
    
    async def record_accuracy_feedback(self, provider: str, request_id: str, accuracy_score: float):
        """Record accuracy feedback for a specific request"""
        try:
            feedback_key = f"{self.metrics_key_prefix}:feedback:{provider}:{request_id}"
            feedback_data = {
                "provider": provider,
                "request_id": request_id,
                "accuracy_score": accuracy_score,
                "timestamp": datetime.now().isoformat()
            }
            
            await redis_manager.set(
                feedback_key,
                json.dumps(feedback_data),
                ttl=86400 * 30  # Keep feedback for 30 days
            )
            
            # Update daily metrics with this feedback
            date_key = datetime.now().strftime("%Y-%m-%d")
            daily_key = f"{self.metrics_key_prefix}:daily:{provider}:{date_key}"
            
            existing_data = await redis_manager.get(daily_key)
            if existing_data:
                metrics_data = json.loads(existing_data)
                if "accuracy_scores" not in metrics_data:
                    metrics_data["accuracy_scores"] = []
                metrics_data["accuracy_scores"].append(accuracy_score)
                
                await redis_manager.set(
                    daily_key,
                    json.dumps(metrics_data),
                    ttl=self.daily_metrics_ttl
                )
            
        except Exception as e:
            logger.error(f"Error recording accuracy feedback: {e}")


# Global metrics collector
metrics_collector = MetricsCollector()
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    TOGETHER_AI = "together_ai"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    REPLICATE = "replicate"

@dataclass
class UsageEvent:
    timestamp: datetime
    service: ServiceType
    model: str
    operation: str  # "multi_role_analysis", "ux_generation", "html_generation"
    tokens_used: int
    estimated_cost: float
    user_session: Optional[str] = None
    success: bool = True
    response_time_ms: int = 0

@dataclass
class DailyCostSummary:
    date: str
    total_cost: float
    total_requests: int
    successful_requests: int
    average_response_time: float
    top_operations: List[Dict[str, Any]]
    cost_by_service: Dict[str, float]

class CostTracker:
    """
    Cost tracking service for serverless pay-per-use model.
    Tracks API usage costs and correlates with revenue generation.
    """
    
    def __init__(self):
        self.usage_events: List[UsageEvent] = []
        self.enabled = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"
        
        # API cost rates (per 1K tokens)
        self.cost_rates = {
            ServiceType.TOGETHER_AI: {
                "meta-llama/Llama-3-70b-chat-hf": 0.0008,  # $0.80 per 1M tokens
                "meta-llama/Llama-3-8b-chat-hf": 0.0002,   # $0.20 per 1M tokens
            },
            ServiceType.HUGGINGFACE: {
                "mistralai/Mistral-7B-Instruct-v0.1": 0.0003,
                "mistralai/Mixtral-8x7B-Instruct-v0.1": 0.0006,
                "microsoft/Phi-3-mini-4k-instruct": 0.0001,
                "Qwen/Qwen2-72B-Instruct": 0.0008,
            },
            ServiceType.OPENAI: {
                "gpt-3.5-turbo": 0.0015,  # $1.50 per 1M tokens
                "gpt-4": 0.03,            # $30 per 1M tokens
            }
        }
        
        logger.info(f"Cost tracking {'enabled' if self.enabled else 'disabled'}")

    async def track_usage(
        self,
        service: ServiceType,
        model: str,
        operation: str,
        tokens_used: int,
        response_time_ms: int = 0,
        user_session: Optional[str] = None,
        success: bool = True
    ) -> float:
        """Track API usage and return estimated cost"""
        
        if not self.enabled:
            return 0.0
            
        try:
            # Calculate estimated cost
            estimated_cost = self._calculate_cost(service, model, tokens_used)
            
            # Create usage event
            event = UsageEvent(
                timestamp=datetime.utcnow(),
                service=service,
                model=model,
                operation=operation,
                tokens_used=tokens_used,
                estimated_cost=estimated_cost,
                user_session=user_session,
                success=success,
                response_time_ms=response_time_ms
            )
            
            # Store event
            self.usage_events.append(event)
            
            # Log important usage
            if estimated_cost > 0.01:  # Log costs above 1 cent
                logger.info(
                    f"API Usage: {service.value}/{model} - "
                    f"{tokens_used} tokens, ${estimated_cost:.4f}, "
                    f"{response_time_ms}ms - {operation}"
                )
            
            # Clean up old events periodically
            if len(self.usage_events) > 10000:
                await self._cleanup_old_events()
                
            return estimated_cost
            
        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")
            return 0.0

    def _calculate_cost(self, service: ServiceType, model: str, tokens: int) -> float:
        """Calculate estimated cost based on service and model"""
        
        try:
            if service in self.cost_rates and model in self.cost_rates[service]:
                rate_per_1k = self.cost_rates[service][model]
                return (tokens / 1000) * rate_per_1k
            else:
                # Default fallback rate
                default_rate = 0.0002  # $0.20 per 1M tokens
                return (tokens / 1000) * default_rate
                
        except:
            return 0.0

    async def get_daily_summary(self, date: Optional[str] = None) -> DailyCostSummary:
        """Get cost summary for a specific date"""
        
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
            
        try:
            # Filter events for the specified date
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            daily_events = [
                event for event in self.usage_events
                if event.timestamp.date() == target_date
            ]
            
            if not daily_events:
                return DailyCostSummary(
                    date=date,
                    total_cost=0.0,
                    total_requests=0,
                    successful_requests=0,
                    average_response_time=0.0,
                    top_operations=[],
                    cost_by_service={}
                )
            
            # Calculate metrics
            total_cost = sum(event.estimated_cost for event in daily_events)
            total_requests = len(daily_events)
            successful_requests = sum(1 for event in daily_events if event.success)
            
            # Average response time
            response_times = [event.response_time_ms for event in daily_events if event.response_time_ms > 0]
            average_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Top operations by cost
            operation_costs = {}
            for event in daily_events:
                op = event.operation
                operation_costs[op] = operation_costs.get(op, 0) + event.estimated_cost
            
            top_operations = [
                {"operation": op, "cost": cost, "percentage": (cost/total_cost)*100}
                for op, cost in sorted(operation_costs.items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Cost by service
            service_costs = {}
            for event in daily_events:
                service = event.service.value
                service_costs[service] = service_costs.get(service, 0) + event.estimated_cost
            
            return DailyCostSummary(
                date=date,
                total_cost=total_cost,
                total_requests=total_requests,
                successful_requests=successful_requests,
                average_response_time=average_response_time,
                top_operations=top_operations,
                cost_by_service=service_costs
            )
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {str(e)}")
            return DailyCostSummary(
                date=date,
                total_cost=0.0,
                total_requests=0,
                successful_requests=0,
                average_response_time=0.0,
                top_operations=[],
                cost_by_service={}
            )

    async def get_monthly_projection(self) -> Dict[str, Any]:
        """Project monthly costs based on current usage patterns"""
        
        try:
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            days_in_month = (month_start.replace(month=month_start.month+1) - month_start).days
            current_day = now.day
            
            # Get current month events
            month_events = [
                event for event in self.usage_events
                if event.timestamp >= month_start
            ]
            
            if not month_events:
                return {
                    "current_month_cost": 0.0,
                    "projected_month_cost": 0.0,
                    "daily_average": 0.0,
                    "days_elapsed": current_day,
                    "projection_confidence": "low"
                }
            
            current_month_cost = sum(event.estimated_cost for event in month_events)
            daily_average = current_month_cost / current_day
            projected_month_cost = daily_average * days_in_month
            
            # Confidence based on days elapsed
            confidence = "high" if current_day >= 7 else "medium" if current_day >= 3 else "low"
            
            return {
                "current_month_cost": current_month_cost,
                "projected_month_cost": projected_month_cost,
                "daily_average": daily_average,
                "days_elapsed": current_day,
                "total_requests": len(month_events),
                "successful_requests": sum(1 for e in month_events if e.success),
                "projection_confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error calculating monthly projection: {str(e)}")
            return {"error": "Failed to calculate projection"}

    async def get_cost_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Analyze usage patterns and suggest cost optimizations"""
        
        suggestions = []
        
        try:
            # Analyze recent events (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_events = [
                event for event in self.usage_events
                if event.timestamp >= week_ago
            ]
            
            if not recent_events:
                return [{"type": "info", "message": "No recent usage to analyze"}]
            
            # Check for expensive model usage
            expensive_events = [e for e in recent_events if e.estimated_cost > 0.05]
            if expensive_events:
                total_expensive_cost = sum(e.estimated_cost for e in expensive_events)
                percentage = (total_expensive_cost / sum(e.estimated_cost for e in recent_events)) * 100
                
                suggestions.append({
                    "type": "optimization",
                    "priority": "high" if percentage > 50 else "medium",
                    "message": f"High-cost API calls account for {percentage:.1f}% of expenses",
                    "suggestion": "Consider using smaller models for simple tasks or implement response caching",
                    "potential_savings": f"${total_expensive_cost * 0.3:.2f}/week"
                })
            
            # Check for failed requests
            failed_events = [e for e in recent_events if not e.success]
            if failed_events:
                failure_rate = (len(failed_events) / len(recent_events)) * 100
                wasted_cost = sum(e.estimated_cost for e in failed_events)
                
                suggestions.append({
                    "type": "reliability",
                    "priority": "high" if failure_rate > 10 else "medium",
                    "message": f"API failure rate: {failure_rate:.1f}% (${wasted_cost:.3f} wasted)",
                    "suggestion": "Implement better retry logic and fallback models",
                    "potential_savings": f"${wasted_cost * 4:.2f}/month"
                })
            
            # Check for slow responses
            slow_events = [e for e in recent_events if e.response_time_ms > 10000]  # >10 seconds
            if slow_events:
                slow_percentage = (len(slow_events) / len(recent_events)) * 100
                
                suggestions.append({
                    "type": "performance",
                    "priority": "medium",
                    "message": f"{slow_percentage:.1f}% of requests are slow (>10s)",
                    "suggestion": "Consider request timeout optimization or faster models",
                    "impact": "Improved user experience"
                })
            
            # Check for usage patterns
            operation_counts = {}
            for event in recent_events:
                operation_counts[event.operation] = operation_counts.get(event.operation, 0) + 1
            
            most_used_operation = max(operation_counts.items(), key=lambda x: x[1])
            if most_used_operation[1] > len(recent_events) * 0.6:  # >60% of usage
                suggestions.append({
                    "type": "caching",
                    "priority": "medium",
                    "message": f"'{most_used_operation[0]}' accounts for {(most_used_operation[1]/len(recent_events)*100):.1f}% of usage",
                    "suggestion": "Implement aggressive caching for this operation",
                    "potential_savings": "20-40% cost reduction"
                })
            
            return suggestions if suggestions else [
                {"type": "success", "message": "Usage patterns look optimized!"}
            ]
            
        except Exception as e:
            logger.error(f"Error analyzing cost optimization: {str(e)}")
            return [{"type": "error", "message": "Failed to analyze usage patterns"}]

    async def _cleanup_old_events(self):
        """Remove events older than 30 days to prevent memory bloat"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            original_count = len(self.usage_events)
            
            self.usage_events = [
                event for event in self.usage_events
                if event.timestamp >= cutoff_date
            ]
            
            cleaned_count = original_count - len(self.usage_events)
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old usage events")
                
        except Exception as e:
            logger.error(f"Error cleaning up old events: {str(e)}")

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            "total_events": len(self.usage_events),
            "tracking_enabled": self.enabled,
            "supported_services": [service.value for service in ServiceType],
            "memory_usage": f"{len(self.usage_events) * 200} bytes (approx)"  # Rough estimate
        }

# Global cost tracker instance
cost_tracker = CostTracker() 
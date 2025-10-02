"""
Performance Profiling and Optimization System

This module provides comprehensive performance analysis for the face recognition system,
including timing measurements, memory usage tracking, and optimization suggestions.
"""

import time
import psutil
import numpy as np
import cv2
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import queue
import statistics
import json
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance measurement"""
    operation: str
    duration_ms: float
    memory_mb: float
    cpu_percent: float
    timestamp: float
    context: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'operation': self.operation,
            'duration_ms': self.duration_ms,
            'memory_mb': self.memory_mb,
            'cpu_percent': self.cpu_percent,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'context': self.context or {}
        }

@dataclass
class PerformanceStats:
    """Performance statistics for an operation"""
    operation: str
    count: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    std_duration_ms: float
    avg_memory_mb: float
    avg_cpu_percent: float
    total_time_ms: float
    ops_per_second: float

class PerformanceProfiler:
    """
    Comprehensive performance profiling system
    
    Features:
    - Operation timing with context
    - Memory usage tracking
    - CPU utilization monitoring
    - Statistical analysis
    - Performance suggestions
    - Baseline comparisons
    """
    
    def __init__(self, log_file: str = "data/performance_metrics.json"):
        self.log_file = log_file
        self.metrics: List[PerformanceMetric] = []
        self.active_operations: Dict[str, float] = {}
        self.baseline_stats: Dict[str, PerformanceStats] = {}
        
        # Performance thresholds (in milliseconds)
        self.thresholds = {
            'face_detection': 200,
            'face_encoding': 500,
            'face_recognition': 100,
            'trust_evaluation': 10,
            'response_generation': 5,
            'frame_processing': 100
        }
        
        # System monitoring
        self.process = psutil.Process()
        
        logger.info("Performance Profiler initialized")
    
    def start_operation(self, operation: str, context: Dict[str, Any] = None) -> str:
        """Start timing an operation"""
        operation_id = f"{operation}_{time.time()}"
        self.active_operations[operation_id] = time.time()
        return operation_id
    
    def end_operation(self, operation_id: str, context: Dict[str, Any] = None) -> PerformanceMetric:
        """End timing an operation and record metrics"""
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found in active operations")
            return None
        
        start_time = self.active_operations.pop(operation_id)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Get system metrics
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent()
        
        # Extract operation name
        operation = operation_id.split('_')[0]
        
        metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            timestamp=end_time,
            context=context
        )
        
        self.metrics.append(metric)
        
        # Check if operation exceeds threshold
        threshold = self.thresholds.get(operation, 1000)
        if duration_ms > threshold:
            logger.warning(f"⚠️ Performance warning: {operation} took {duration_ms:.1f}ms "
                         f"(threshold: {threshold}ms)")
        
        return metric
    
    def measure_operation(self, operation: str, func, *args, context: Dict[str, Any] = None, **kwargs):
        """Measure a function call and return result with metrics"""
        operation_id = self.start_operation(operation, context)
        try:
            result = func(*args, **kwargs)
            metric = self.end_operation(operation_id, context)
            return result, metric
        except Exception as e:
            self.end_operation(operation_id, {'error': str(e)})
            raise
    
    def get_operation_stats(self, operation: str, last_n: Optional[int] = None) -> Optional[PerformanceStats]:
        """Get statistics for a specific operation"""
        operation_metrics = [m for m in self.metrics if m.operation == operation]
        
        if not operation_metrics:
            return None
        
        if last_n:
            operation_metrics = operation_metrics[-last_n:]
        
        durations = [m.duration_ms for m in operation_metrics]
        memory_usage = [m.memory_mb for m in operation_metrics]
        cpu_usage = [m.cpu_percent for m in operation_metrics]
        
        total_time = sum(durations)
        count = len(operation_metrics)
        
        # Calculate time span for ops/second
        if count > 1:
            time_span = operation_metrics[-1].timestamp - operation_metrics[0].timestamp
            ops_per_second = count / max(time_span, 0.001)
        else:
            ops_per_second = 0
        
        return PerformanceStats(
            operation=operation,
            count=count,
            avg_duration_ms=statistics.mean(durations),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            std_duration_ms=statistics.stdev(durations) if count > 1 else 0,
            avg_memory_mb=statistics.mean(memory_usage),
            avg_cpu_percent=statistics.mean(cpu_usage),
            total_time_ms=total_time,
            ops_per_second=ops_per_second
        )
    
    def save_baseline(self, name: str = "default") -> None:
        """Save current performance as baseline"""
        baseline = {}
        
        for operation in set(m.operation for m in self.metrics):
            stats = self.get_operation_stats(operation)
            if stats:
                baseline[operation] = stats
        
        self.baseline_stats[name] = baseline
        
        # Save to file
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            baseline_file = self.log_file.replace('.json', f'_baseline_{name}.json')
            
            baseline_dict = {
                op: asdict(stats) for op, stats in baseline.items()
            }
            
            with open(baseline_file, 'w') as f:
                json.dump(baseline_dict, f, indent=2)
            
            logger.info(f"Saved performance baseline '{name}' with {len(baseline)} operations")
        except Exception as e:
            logger.error(f"Error saving baseline: {e}")
    
    def compare_to_baseline(self, baseline_name: str = "default") -> Dict[str, Dict[str, float]]:
        """Compare current performance to baseline"""
        if baseline_name not in self.baseline_stats:
            logger.warning(f"Baseline '{baseline_name}' not found")
            return {}
        
        baseline = self.baseline_stats[baseline_name]
        comparison = {}
        
        for operation in baseline:
            current_stats = self.get_operation_stats(operation, last_n=50)  # Last 50 operations
            if current_stats:
                baseline_stats = baseline[operation]
                
                comparison[operation] = {
                    'duration_improvement': (baseline_stats.avg_duration_ms - current_stats.avg_duration_ms) / baseline_stats.avg_duration_ms * 100,
                    'memory_change': (current_stats.avg_memory_mb - baseline_stats.avg_memory_mb) / baseline_stats.avg_memory_mb * 100,
                    'throughput_improvement': (current_stats.ops_per_second - baseline_stats.ops_per_second) / baseline_stats.ops_per_second * 100 if baseline_stats.ops_per_second > 0 else 0
                }
        
        return comparison
    
    def get_performance_suggestions(self) -> List[str]:
        """Generate performance optimization suggestions"""
        suggestions = []
        
        # Analyze recent metrics
        recent_metrics = self.metrics[-100:] if len(self.metrics) > 100 else self.metrics
        
        if not recent_metrics:
            return ["No performance data available for analysis"]
        
        # Group by operation
        operation_groups = {}
        for metric in recent_metrics:
            if metric.operation not in operation_groups:
                operation_groups[metric.operation] = []
            operation_groups[metric.operation].append(metric)
        
        for operation, metrics_list in operation_groups.items():
            avg_duration = statistics.mean([m.duration_ms for m in metrics_list])
            threshold = self.thresholds.get(operation, 1000)
            
            if avg_duration > threshold:
                improvement_needed = ((avg_duration - threshold) / threshold) * 100
                suggestions.append(
                    f"🐌 {operation} is {improvement_needed:.1f}% slower than threshold "
                    f"({avg_duration:.1f}ms vs {threshold}ms)"
                )
            
            # Check for memory usage
            avg_memory = statistics.mean([m.memory_mb for m in metrics_list])
            if avg_memory > 500:  # 500MB threshold
                suggestions.append(
                    f"🧠 {operation} using high memory: {avg_memory:.1f}MB"
                )
            
            # Check for high variability
            if len(metrics_list) > 5:
                durations = [m.duration_ms for m in metrics_list]
                std_dev = statistics.stdev(durations)
                cv = std_dev / avg_duration if avg_duration > 0 else 0
                
                if cv > 0.5:  # Coefficient of variation > 50%
                    suggestions.append(
                        f"📊 {operation} has high variability (CV: {cv:.2f}) - consider optimization"
                    )
        
        if not suggestions:
            suggestions.append("✅ Performance looks good! All operations within thresholds.")
        
        return suggestions
    
    def print_performance_report(self, detailed: bool = False) -> None:
        """Print comprehensive performance report"""
        print("\n📊 Performance Analysis Report")
        print("=" * 60)
        
        if not self.metrics:
            print("No performance data available")
            return
        
        # Overall statistics
        total_operations = len(self.metrics)
        time_span = self.metrics[-1].timestamp - self.metrics[0].timestamp if total_operations > 1 else 0
        overall_ops_per_sec = total_operations / max(time_span, 0.001)
        
        print(f"Total Operations: {total_operations}")
        print(f"Time Span: {time_span:.1f}s")
        print(f"Overall Throughput: {overall_ops_per_sec:.1f} ops/sec")
        
        # Per-operation statistics
        operations = set(m.operation for m in self.metrics)
        
        print(f"\n📈 Operation Statistics:")
        print("-" * 60)
        
        for operation in sorted(operations):
            stats = self.get_operation_stats(operation)
            if stats:
                threshold = self.thresholds.get(operation, "N/A")
                status = "✅" if isinstance(threshold, (int, float)) and stats.avg_duration_ms <= threshold else "⚠️"
                
                print(f"{status} {operation.upper()}")
                print(f"   Count: {stats.count}")
                print(f"   Avg Duration: {stats.avg_duration_ms:.1f}ms (threshold: {threshold})")
                print(f"   Range: {stats.min_duration_ms:.1f}ms - {stats.max_duration_ms:.1f}ms")
                print(f"   Std Dev: {stats.std_duration_ms:.1f}ms")
                print(f"   Throughput: {stats.ops_per_second:.1f} ops/sec")
                print(f"   Memory: {stats.avg_memory_mb:.1f}MB")
                if detailed:
                    print(f"   CPU: {stats.avg_cpu_percent:.1f}%")
                print()
        
        # Performance suggestions
        suggestions = self.get_performance_suggestions()
        print("💡 Performance Suggestions:")
        print("-" * 40)
        for suggestion in suggestions:
            print(f"   {suggestion}")
        
        # Memory usage trend
        recent_memory = [m.memory_mb for m in self.metrics[-20:]]
        if recent_memory:
            memory_trend = "📈" if len(recent_memory) > 1 and recent_memory[-1] > recent_memory[0] else "📉"
            print(f"\n{memory_trend} Recent Memory Usage: {statistics.mean(recent_memory):.1f}MB")

# Integration with existing face recognition system
class OptimizedFaceRecognizer:
    """Face recognizer with performance optimization features"""
    
    def __init__(self, base_recognizer, profiler: PerformanceProfiler):
        self.base_recognizer = base_recognizer
        self.profiler = profiler
        
        # Optimization settings
        self.frame_skip_count = 0
        self.frame_skip_interval = 2  # Process every 2nd frame
        self.face_tracking_enabled = True
        self.tracked_faces = {}
        self.tracking_timeout = 1.0  # 1 second
        
    def detect_faces_optimized(self, frame: np.ndarray) -> List:
        """Optimized face detection with frame skipping"""
        # Frame skipping optimization
        if self.frame_skip_count < self.frame_skip_interval:
            self.frame_skip_count += 1
            return []  # Skip this frame
        
        self.frame_skip_count = 0
        
        # Measure detection performance
        result, metric = self.profiler.measure_operation(
            'face_detection',
            self.base_recognizer.face_detector.detect_faces,
            frame,
            context={'frame_shape': frame.shape}
        )
        
        return result
    
    def recognize_face_optimized(self, face_encoding: np.ndarray) -> Tuple:
        """Optimized face recognition with caching"""
        result, metric = self.profiler.measure_operation(
            'face_recognition',
            self.base_recognizer.recognize_face,
            face_encoding,
            context={'encoding_shape': face_encoding.shape}
        )
        
        return result

# Example usage and testing
if __name__ == "__main__":
    # Create profiler
    profiler = PerformanceProfiler()
    
    print("🧪 Testing Performance Profiling System...")
    
    # Simulate some operations
    for i in range(10):
        # Simulate face detection
        op_id = profiler.start_operation('face_detection', {'frame_size': (640, 480)})
        time.sleep(0.05 + np.random.normal(0, 0.01))  # Simulate variable timing
        profiler.end_operation(op_id)
        
        # Simulate face recognition
        op_id = profiler.start_operation('face_recognition', {'encoding_size': 128})
        time.sleep(0.02 + np.random.normal(0, 0.005))
        profiler.end_operation(op_id)
        
        # Simulate trust evaluation
        op_id = profiler.start_operation('trust_evaluation', {'user_id': f'user_{i}'})
        time.sleep(0.001 + np.random.normal(0, 0.0002))
        profiler.end_operation(op_id)
    
    # Save baseline
    profiler.save_baseline("initial_test")
    
    # Generate report
    profiler.print_performance_report(detailed=True)
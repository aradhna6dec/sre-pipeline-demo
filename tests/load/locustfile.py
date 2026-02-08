"""
Load Testing with Locust
Simulates realistic user behavior and traffic patterns
"""

from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask
import random
import json


class APIUser(HttpUser):
    """
    Simulates a typical API user
    Models realistic user behavior with think time
    """
    
    # Wait 1-3 seconds between requests (realistic user behavior)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts - initialization"""
        self.item_ids = []
        # Warm up: get initial list of items
        response = self.client.get("/api/v1/items?limit=10")
        if response.status_code == 200:
            self.item_ids = [item["id"] for item in response.json()]
    
    @task(10)  # Weight: 10/40 = 25% of requests
    def get_items_list(self):
        """Get list of items - most common operation"""
        skip = random.randint(0, 100)
        limit = random.randint(5, 20)
        
        with self.client.get(
            f"/api/v1/items?skip={skip}&limit={limit}",
            catch_response=True,
            name="/api/v1/items [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(20)  # Weight: 20/40 = 50% of requests
    def get_item_detail(self):
        """Get specific item details - most common read"""
        if not self.item_ids:
            raise RescheduleTask()
        
        item_id = random.choice(self.item_ids)
        
        with self.client.get(
            f"/api/v1/items/{item_id}",
            catch_response=True,
            name="/api/v1/items/[id] [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # 404 is acceptable, remove bad ID
                self.item_ids.remove(item_id)
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(5)  # Weight: 5/40 = 12.5% of requests
    def create_item(self):
        """Create new item - write operation"""
        payload = {
            "name": f"Load Test Item {random.randint(1, 10000)}",
            "description": "Created by load testing",
            "price": round(random.uniform(10, 1000), 2)
        }
        
        with self.client.post(
            "/api/v1/items",
            json=payload,
            catch_response=True,
            name="/api/v1/items [CREATE]"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.item_ids.append(data["id"])
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(3)  # Weight: 3/40 = 7.5% of requests
    def health_check(self):
        """Health check - simulating monitoring"""
        self.client.get("/health/ready", name="/health/ready [HEALTH]")
    
    @task(2)  # Weight: 2/40 = 5% of requests
    def trigger_slow_query(self):
        """Intentionally slow request - edge case"""
        delay = random.choice([1, 2, 3])
        self.client.get(
            f"/api/v1/slow?delay={delay}",
            name="/api/v1/slow [SLOW]"
        )


class StressTestUser(HttpUser):
    """
    Aggressive user for stress testing
    No wait time between requests
    """
    wait_time = between(0.1, 0.5)
    
    @task
    def rapid_fire_requests(self):
        """Rapid requests to test system limits"""
        self.client.get("/api/v1/items?limit=1")


class BurstTrafficUser(HttpUser):
    """
    Simulates burst traffic patterns
    Periods of high activity followed by quiet
    """
    wait_time = between(0, 1)
    
    @task
    def burst_requests(self):
        """Burst of requests"""
        for _ in range(random.randint(5, 15)):
            self.client.get(f"/api/v1/items/{random.randint(1, 100)}")
        
        # Then wait
        self.wait_time = between(5, 10)


# ==============================================================================
# Event Handlers - Custom metrics and reporting
# ==============================================================================

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Track custom metrics for each request
    """
    if exception:
        print(f"Request failed: {name} - {exception}")
    
    # Alert on slow requests (SLA violation)
    if response_time > 2000:  # 2 seconds
        print(f"⚠️  SLOW REQUEST: {name} took {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called at the start of load test
    """
    print(f"🚀 Load test started with {environment.runner.user_count} users")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called at the end of load test - custom reporting
    """
    print("\n" + "="*80)
    print("📊 LOAD TEST RESULTS")
    print("="*80)
    
    stats = environment.runner.stats
    
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio*100:.2f}%")
    print(f"Avg Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.0f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.0f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    
    print("\n📈 Response Time Percentiles:")
    print(f"  50th: {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"  75th: {stats.total.get_response_time_percentile(0.75):.0f}ms")
    print(f"  90th: {stats.total.get_response_time_percentile(0.90):.0f}ms")
    print(f"  95th: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  99th: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    
    # Check SLA compliance (example: P95 < 500ms, P99 < 1000ms)
    p95 = stats.total.get_response_time_percentile(0.95)
    p99 = stats.total.get_response_time_percentile(0.99)
    
    print("\n🎯 SLA Compliance:")
    print(f"  P95 < 500ms: {'✅ PASS' if p95 < 500 else '❌ FAIL'} ({p95:.0f}ms)")
    print(f"  P99 < 1000ms: {'✅ PASS' if p99 < 1000 else '❌ FAIL'} ({p99:.0f}ms)")
    print(f"  Error rate < 1%: {'✅ PASS' if stats.total.fail_ratio < 0.01 else '❌ FAIL'} ({stats.total.fail_ratio*100:.2f}%)")
    
    print("\n" + "="*80)


# ==============================================================================
# USAGE:
# ==============================================================================
# 
# 1. Web UI mode (recommended):
#    locust -f tests/load/locustfile.py --host=http://localhost:8000
#    Open: http://localhost:8089
# 
# 2. Headless mode (CI/CD):
#    locust -f tests/load/locustfile.py \
#           --host=http://localhost:8000 \
#           --users=100 \
#           --spawn-rate=10 \
#           --run-time=5m \
#           --headless \
#           --html=report.html
# 
# 3. Distributed mode (high load):
#    # Master:
#    locust -f tests/load/locustfile.py --master
#    
#    # Workers (on multiple machines):
#    locust -f tests/load/locustfile.py --worker --master-host=<master-ip>
# 
# 4. Different user classes:
#    # Stress test:
#    locust -f tests/load/locustfile.py --host=http://localhost:8000 StressTestUser
#    
#    # Burst traffic:
#    locust -f tests/load/locustfile.py --host=http://localhost:8000 BurstTrafficUser
# 
# ==============================================================================

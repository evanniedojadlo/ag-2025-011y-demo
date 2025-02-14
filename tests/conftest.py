import pytest
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Create a gauge metric to track the test result (1=pass, 0=fail)
registry = CollectorRegistry()
test_result = Gauge('demo_test_result', 'Result of the demo test (1=pass, 0=fail)', registry=registry)

@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    print("Starting tests...")

@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    # Set the test result
    result = 1 if exitstatus == 0 else 0
    test_result.set(result)
    print(f"Reported test result to Prometheus Pushgateway: {result}")
    # Push the metric to Pushgateway
    push_to_gateway('pushgateway:9091', job='demo-test', registry=registry)

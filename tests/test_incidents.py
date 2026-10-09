import pytest
from datetime import datetime, timedelta
from app.models import LogEntry, LogLevel, ServiceName
from app.incident_engine import IncidentEngine
from app.incident_models import IncidentType
from unittest.mock import patch

def test_brute_force_detection():
    engine = IncidentEngine()
    base_time = datetime.now()
    ip = "192.168.1.100"
    
    for i in range(4):
        log = LogEntry(
            service=ServiceName.AUTH,
            level=LogLevel.ERROR,
            message="Failed login attempt",
            ip=ip,
            timestamp=base_time + timedelta(seconds=i*5)
        )
        incidents, alerts = engine.analyze(log)
        assert len(incidents) == 0
        
    log = LogEntry(
        service=ServiceName.AUTH,
        level=LogLevel.ERROR,
        message="Failed login attempt",
        ip=ip,
        timestamp=base_time + timedelta(seconds=20)
    )
    incidents, alerts = engine.analyze(log)
    assert len(incidents) == 1
    assert incidents[0].type == IncidentType.BRUTE_FORCE
    assert len(alerts) == 1

def test_error_spike_detection():
    engine = IncidentEngine()
    base_time = datetime.now()
    
    for i in range(11):
        log = LogEntry(
            service=ServiceName.BACKEND,
            level=LogLevel.ERROR,
            message="Internal server error",
            timestamp=base_time + timedelta(seconds=i)
        )
        incidents, alerts = engine.analyze(log)
        
    # the 11th one triggers the incident
    assert len(incidents) == 1
    assert incidents[0].type == IncidentType.ERROR_SPike

def test_deduplication():
    engine = IncidentEngine()
    base_time = datetime.now()
    ip = "192.168.1.105"
    
    # First brute force
    for i in range(5):
        log = LogEntry(
            service=ServiceName.AUTH,
            level=LogLevel.ERROR,
            message="Failed login attempt",
            ip=ip,
            timestamp=base_time + timedelta(seconds=i)
        )
        incidents, alerts = engine.analyze(log)
        
    assert len(incidents) == 1
    assert incidents[0].type == IncidentType.BRUTE_FORCE
    
    # Needs another 5 to trigger another incident that gets aggregated
    for i in range(5, 10):
        log = LogEntry(
            service=ServiceName.AUTH,
            level=LogLevel.ERROR,
            message="Failed login attempt",
            ip=ip,
            timestamp=base_time + timedelta(seconds=i)
        )
        incidents, alerts = engine.analyze(log)
    
    # The deduplication engine returns the updated existing incident
    assert len(incidents) == 1
    assert incidents[0].event_count > 1

def test_suppression():
    engine = IncidentEngine()
    base_time = datetime.now()
    ip = "192.168.1.110"
    dedup_key = f"brute_force:auth:{ip}"
    
    engine.dedup.suppress(dedup_key, 3600, "Known scanner")
    
    for i in range(5):
        log = LogEntry(
            service=ServiceName.AUTH,
            level=LogLevel.ERROR,
            message="Failed login attempt",
            ip=ip,
            timestamp=base_time + timedelta(seconds=i)
        )
        incidents, alerts = engine.analyze(log)
        assert len(incidents) == 0

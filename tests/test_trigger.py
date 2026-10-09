from core.trigger_monitor import TriggerMonitor

def test_empty_trigger_is_false():
    assert TriggerMonitor.is_running('') is False

def test_unlikely_process_is_false():
    assert TriggerMonitor.is_running('mapre_process_that_does_not_exist_84729.exe') is False

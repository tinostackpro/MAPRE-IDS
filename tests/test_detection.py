from modules.intrusion_detector import IntrusionDetector

def test_alert_on_threshold():
    detector=IntrusionDetector(threshold=3, window_seconds=60)
    assert detector.observe('proc','1.1.1.1:80') is None
    assert detector.observe('proc','1.1.1.1:80') is None
    alert=detector.observe('proc','1.1.1.1:80')
    assert alert and alert['category']=='Possível anomalia'

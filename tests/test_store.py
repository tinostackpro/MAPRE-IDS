from storage.event_store import EventStore

def test_event_round_trip(tmp_path):
    store=EventStore(tmp_path/'events.db')
    store.add('Teste','Info','evento de teste','origem','destino','detalhes')
    rows=store.recent()
    assert len(rows)==1
    assert rows[0]['description']=='evento de teste'

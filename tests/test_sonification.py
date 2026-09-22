from src.sonification import SonificationEngine

def test_clamp():
    engine = SonificationEngine(None)

    assert engine.clamp(50) == 50
    assert engine.clamp(158) == 127
    assert engine.clamp(-40) == 0

def test_snap_to_scale():
    engine = SonificationEngine(None)

    scale_notes = [60, 62, 64, 67, 69]

    for note in [61, 63, 65, 66, 68]:
        snapped = engine.snap_to_scale(note)
        
        assert snapped in scale_notes

def test_scale_degree_up():
    engine = SonificationEngine(None)

    assert engine.scale_degree_up(60, 2) == 64
    assert engine.scale_degree_up(60, 4) == 69


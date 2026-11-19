import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import habitats
from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT
from habitat_round import Stage
from habitat_scene import HabitatScene


class StubReader:
    def __init__(self):
        self.scores_sent = []
        self._queued_events = []

    def drain(self):
        pass

    def poll_events(self):
        events, self._queued_events = self._queued_events, []
        return events

    def send_score(self, score):
        self.scores_sent.append(score)

    def queue_scan(self, statue):
        self._queued_events.append(statue)


def _make_scene(reader, habitat=habitats.PATRICK):
    return HabitatScene(habitat=habitat, go_to_menu=lambda: None, rfid_reader=reader)


def test_scene_pushes_zero_on_entry():
    reader = StubReader()
    _make_scene(reader)
    assert reader.scores_sent == [0]


def test_prev_and_next_events_do_not_advance_the_round():
    reader = StubReader()
    scene = _make_scene(reader)
    stage_before = scene._round.stage
    scene.handle_event(pygame.event.Event(BUTTON_PREV_EVENT))
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))
    assert scene._round.stage == stage_before


def test_enter_event_advances_the_round():
    reader = StubReader()
    scene = _make_scene(reader)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    assert scene._round.stage == Stage.PHASE_1


def test_score_is_pushed_again_only_when_it_changes():
    reader = StubReader()
    scene = _make_scene(reader)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # start phase 1
    scene.update(0.0)
    sent_count = len(reader.scores_sent)
    scene.update(0.0)  # nothing scanned, score unchanged
    assert len(reader.scores_sent) == sent_count

    # HabitatRound.score only updates when a phase banks (at _end_phase),
    # not on each individual scan - so complete Patrick's full combination
    # to make phase 1 actually bank its patties.
    for statue in ("SEA_URCHIN", "KELP", "ROCKS_WITH_MUD"):
        reader.queue_scan(statue)
    scene.update(0.0)
    assert reader.scores_sent[-1] == scene._round.score
    assert reader.scores_sent[-1] > 0


def test_scan_that_fits_spawns_flying_patties():
    reader = StubReader()
    scene = _make_scene(reader)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # start phase 1
    reader.queue_scan("SEA_URCHIN")  # fits Patrick
    scene.update(0.0)
    assert len(scene._flying_patties._patties) > 0


def test_scan_that_does_not_fit_spawns_no_flying_patties():
    reader = StubReader()
    scene = _make_scene(reader)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    reader.queue_scan("SUN")  # Patrick has no use for Sandy's sun (fit == 0)
    scene.update(0.0)
    assert scene._flying_patties._patties == []


def test_partial_fit_scan_spawns_flying_patties():
    # ROCKS_WITH_MUD isn't one of SpongeBob's placements, but it's a
    # partial fit (0.5) for him, so it still earns patties and should
    # still fly - not just statues that perfectly complete a placement.
    reader = StubReader()
    scene = _make_scene(reader, habitat=habitats.SPONGEBOB)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # start phase 1
    reader.queue_scan("ROCKS_WITH_MUD")
    scene.update(0.0)
    assert len(scene._flying_patties._patties) > 0


def test_character_frame_index_matches_round_state():
    reader = StubReader()
    scene = _make_scene(reader, habitat=habitats.PATRICK)
    assert scene._character_frame_index() == 1  # neutral, before phase 1 starts

    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # start phase 1
    assert scene._character_frame_index() == 1  # neutral during phase 1

    scene.update(999.0)  # timer runs out with nothing scanned -> phase 2
    assert scene._round.phase == 2
    assert scene._character_frame_index() == 0  # struggling/fixing


def test_character_frame_index_is_celebrating_when_perfect():
    reader = StubReader()
    scene = _make_scene(reader, habitat=habitats.PATRICK)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    for statue in ("SEA_URCHIN", "KELP", "ROCKS_WITH_MUD"):
        reader.queue_scan(statue)
    scene.update(0.0)
    assert scene._round.is_perfect
    assert scene._character_frame_index() == 2


def test_three_character_frames_loaded_for_spongebob_sandy_patrick():
    for habitat in (habitats.SPONGEBOB, habitats.SANDY, habitats.PATRICK):
        reader = StubReader()
        scene = _make_scene(reader, habitat=habitat)
        assert scene._characters is not None
        assert len(scene._characters) == 3


def test_squidward_and_krabs_have_no_character_art_yet():
    for habitat in (habitats.SQUIDWARD, habitats.MR_KRABS):
        reader = StubReader()
        scene = _make_scene(reader, habitat=habitat)
        assert scene._characters is None


if __name__ == "__main__":
    test_scene_pushes_zero_on_entry()
    test_prev_and_next_events_do_not_advance_the_round()
    test_enter_event_advances_the_round()
    test_score_is_pushed_again_only_when_it_changes()
    test_scan_that_fits_spawns_flying_patties()
    test_scan_that_does_not_fit_spawns_no_flying_patties()
    test_partial_fit_scan_spawns_flying_patties()
    test_character_frame_index_matches_round_state()
    test_character_frame_index_is_celebrating_when_perfect()
    test_three_character_frames_loaded_for_spongebob_sandy_patrick()
    test_squidward_and_krabs_have_no_character_art_yet()
    print("OK")

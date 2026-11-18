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


def _make_scene(reader):
    return HabitatScene(habitat=habitats.PATRICK, go_to_menu=lambda: None, rfid_reader=reader)


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


if __name__ == "__main__":
    test_scene_pushes_zero_on_entry()
    test_prev_and_next_events_do_not_advance_the_round()
    test_enter_event_advances_the_round()
    test_score_is_pushed_again_only_when_it_changes()
    print("OK")

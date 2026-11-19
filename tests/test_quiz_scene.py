import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT
from quiz_questions import QuizQuestion
from quiz_scene import (
    FEEDBACK_SECONDS,
    QUIZ_BASE_BONUS,
    QUIZ_TIME_LIMIT_SECONDS,
    QuizScene,
    compute_bonus,
)

_QUESTION = QuizQuestion(text="2+2?", options=("3", "4", "5"), correct_index=1)


def _make_scene(calls, base_score=20):
    return QuizScene(
        habitat_name="Patrick",
        base_score=base_score,
        go_to_leaderboard=lambda score: calls.append(score),
        question=_QUESTION,
    )


def test_wrong_answer_gives_zero_bonus():
    assert compute_bonus(correct=False, seconds_taken=0.0) == 0
    assert compute_bonus(correct=False, seconds_taken=999.0) == 0


def test_slow_correct_answer_gives_exactly_the_base_bonus():
    assert compute_bonus(correct=True, seconds_taken=QUIZ_TIME_LIMIT_SECONDS) == QUIZ_BASE_BONUS
    assert compute_bonus(correct=True, seconds_taken=999.0) == QUIZ_BASE_BONUS


def test_instant_correct_answer_gives_the_maximum_bonus():
    assert compute_bonus(correct=True, seconds_taken=0.0) == round(QUIZ_BASE_BONUS * 1.5)


def test_prev_and_next_move_focus_with_wraparound():
    scene = _make_scene([])
    assert scene._focused_index == 0
    scene.handle_event(pygame.event.Event(BUTTON_PREV_EVENT))
    assert scene._focused_index == 2
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))
    assert scene._focused_index == 0


def test_submitting_the_correct_answer_adds_a_bonus_once_feedback_elapses():
    calls = []
    scene = _make_scene(calls, base_score=20)
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))  # focus -> index 1 (correct)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # submit
    scene.update(FEEDBACK_SECONDS + 0.01)
    assert len(calls) == 1
    assert 24 <= calls[0] <= 26  # base 20 + bonus 4-6 (answered almost instantly)


def test_submitting_the_wrong_answer_adds_no_bonus():
    calls = []
    scene = _make_scene(calls, base_score=20)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # index 0 is wrong
    scene.update(FEEDBACK_SECONDS + 0.01)
    assert calls == [20]


def test_input_after_answering_is_ignored():
    calls = []
    scene = _make_scene(calls, base_score=20)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # answers wrong (index 0)
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))  # ignored
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # ignored - no double submit
    scene.update(FEEDBACK_SECONDS + 0.01)
    assert calls == [20]


def test_does_not_transition_before_feedback_delay_elapses():
    calls = []
    scene = _make_scene(calls, base_score=20)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    scene.update(FEEDBACK_SECONDS / 2)
    assert calls == []
    scene.update(FEEDBACK_SECONDS / 2 + 0.01)
    assert calls == [20]


if __name__ == "__main__":
    test_wrong_answer_gives_zero_bonus()
    test_slow_correct_answer_gives_exactly_the_base_bonus()
    test_instant_correct_answer_gives_the_maximum_bonus()
    test_prev_and_next_move_focus_with_wraparound()
    test_submitting_the_correct_answer_adds_a_bonus_once_feedback_elapses()
    test_submitting_the_wrong_answer_adds_no_bonus()
    test_input_after_answering_is_ignored()
    test_does_not_transition_before_feedback_delay_elapses()
    print("OK")

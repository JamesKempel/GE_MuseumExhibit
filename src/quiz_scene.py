import random
import time
from typing import Callable

import pygame

from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT
from quiz_questions import QuizQuestion, random_question

QUIZ_BASE_BONUS = 4
QUIZ_TIME_LIMIT_SECONDS = 10.0
QUIZ_SPEED_BONUS_PER_SECOND = 0.05
FEEDBACK_SECONDS = 1.5
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)

FOCUS_COLOR = (255, 215, 0)
CORRECT_COLOR = (120, 230, 120)
WRONG_COLOR = (255, 80, 80)
TEXT_COLOR = (255, 255, 255)


def compute_bonus(correct: bool, seconds_taken: float) -> int:
    if not correct:
        return 0
    seconds_remaining = max(0.0, QUIZ_TIME_LIMIT_SECONDS - seconds_taken)
    multiplier = 1 + QUIZ_SPEED_BONUS_PER_SECOND * seconds_remaining
    return round(QUIZ_BASE_BONUS * multiplier)


def _shuffled(question: QuizQuestion, rng: random.Random) -> QuizQuestion:
    """Returns a new QuizQuestion with the options in a random order, so
    the correct answer isn't always at a predictable position - a kid
    mashing Enter shouldn't reliably land on it."""
    indices = list(range(len(question.options)))
    rng.shuffle(indices)
    new_options = tuple(question.options[i] for i in indices)
    new_correct_index = indices.index(question.correct_index)
    return QuizQuestion(text=question.text, options=new_options, correct_index=new_correct_index)


class QuizScene:
    """A single trivia question from the just-played habitat's pool.
    One attempt; a correct answer adds a small, speed-scaled bonus to
    that round's score. The answer timer is never displayed or saved -
    it only feeds compute_bonus."""

    def __init__(
        self,
        habitat_name: str,
        base_score: int,
        go_to_leaderboard: Callable[[int], None],
        question: QuizQuestion | None = None,
        shuffle: bool = True,
        rng: random.Random | None = None,
    ) -> None:
        base_question = question if question is not None else random_question(habitat_name)
        self._question = _shuffled(base_question, rng or random.Random()) if shuffle else base_question
        self._base_score = base_score
        self._go_to_leaderboard = go_to_leaderboard
        self._focused_index = 0
        self._answered = False
        self._correct = False
        self._final_score = base_score
        self._start_time = time.monotonic()
        self._feedback_elapsed = 0.0
        self._font = pygame.font.SysFont(None, 36)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._answered:
            return
        if event.type == BUTTON_PREV_EVENT or (
            event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_UP)
        ):
            self._move_focus(-1)
        elif event.type == BUTTON_NEXT_EVENT or (
            event.type == pygame.KEYDOWN and event.key in (pygame.K_RIGHT, pygame.K_DOWN)
        ):
            self._move_focus(1)
        elif event.type == BUTTON_ENTER_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        ):
            self._submit()

    def _move_focus(self, step: int) -> None:
        self._focused_index = (self._focused_index + step) % len(self._question.options)

    def _submit(self) -> None:
        seconds_taken = time.monotonic() - self._start_time
        self._correct = self._focused_index == self._question.correct_index
        bonus = compute_bonus(self._correct, seconds_taken)
        self._final_score = self._base_score + bonus
        self._answered = True

    def update(self, dt: float) -> None:
        if not self._answered:
            return
        self._feedback_elapsed += dt
        if self._feedback_elapsed >= FEEDBACK_SECONDS:
            self._go_to_leaderboard(self._final_score)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((15, 30, 55))
        title = self._font.render(self._question.text, True, TEXT_COLOR)
        surface.blit(title, title.get_rect(midtop=(surface.get_width() // 2, 40)))

        option_font = pygame.font.SysFont(None, 28)
        y = 140
        for i, option in enumerate(self._question.options):
            color = TEXT_COLOR
            if self._answered:
                if i == self._question.correct_index:
                    color = CORRECT_COLOR
                elif i == self._focused_index:
                    color = WRONG_COLOR
            elif i == self._focused_index:
                color = FOCUS_COLOR
            text = option_font.render(option, True, color)
            surface.blit(text, text.get_rect(midtop=(surface.get_width() // 2, y)))
            y += 40

        if self._answered:
            feedback = "Correct!" if self._correct else "Not quite..."
            feedback_surface = self._font.render(feedback, True, FOCUS_COLOR)
            surface.blit(feedback_surface, feedback_surface.get_rect(midtop=(surface.get_width() // 2, y + 20)))

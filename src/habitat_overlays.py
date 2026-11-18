"""Drawing for the timed habitat round: HUD, intro cards, phase 2 hints and
highlights, and the results card. Pure drawing - no game state changes."""

import math
from dataclasses import dataclass

import pygame

from habitat_round import COMBINATION_SIZE, PHASE_1, PHASE_2, HabitatRound, Hint
from krabby_patty import draw_patty_stack

TEXT_COLOR = (255, 255, 255)
MUTED_TEXT_COLOR = (200, 210, 225)
ACCENT_COLOR = (255, 215, 0)
WARNING_COLOR = (255, 80, 80)
GOOD_COLOR = (120, 230, 120)
PANEL_COLOR = (15, 25, 45, 215)
SCRIM_COLOR = (0, 0, 0, 140)
PANEL_RADIUS = 14
PANEL_PADDING = 24
LINE_GAP = 6
HUD_TOP = 16
TIMER_WARNING_SECONDS = 5  # countdown turns red at this point
STOPWATCH_RADIUS = 8
STOPWATCH_GAP = 6
HIGHLIGHT_PULSE_HZ = 2.0


@dataclass(frozen=True)
class Fonts:
    title: pygame.font.Font
    body: pygame.font.Font
    small: pygame.font.Font

    @classmethod
    def create(cls) -> "Fonts":
        return cls(
            title=pygame.font.SysFont(None, 56),
            body=pygame.font.SysFont(None, 32),
            small=pygame.font.SysFont(None, 26),
        )


# ---------- Helpers ----------

def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _draw_panel(surface: pygame.Surface, rect: pygame.Rect, border: tuple[int, int, int]) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, PANEL_COLOR, panel.get_rect(), border_radius=PANEL_RADIUS)
    surface.blit(panel, rect)
    pygame.draw.rect(surface, border, rect, width=3, border_radius=PANEL_RADIUS)


def _draw_scrim(surface: pygame.Surface) -> None:
    scrim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    scrim.fill(SCRIM_COLOR)
    surface.blit(scrim, (0, 0))


def _draw_lines(
    surface: pygame.Surface,
    lines: list[tuple[pygame.font.Font, str, tuple[int, int, int]]],
    center_x: int,
    top: int,
) -> int:
    """Draw centered lines top to bottom; returns the y below the last one."""
    y = top
    for font, text, color in lines:
        rendered = font.render(text, True, color)
        surface.blit(rendered, rendered.get_rect(midtop=(center_x, y)))
        y += rendered.get_height() + LINE_GAP
    return y


def _card(
    surface: pygame.Surface,
    lines: list[tuple[pygame.font.Font, str, tuple[int, int, int]]],
    width: int,
    border: tuple[int, int, int],
) -> None:
    height = sum(font.get_linesize() + LINE_GAP for font, _, _ in lines) + PANEL_PADDING * 2
    rect = pygame.Rect(0, 0, width, height)
    rect.center = surface.get_rect().center
    _draw_scrim(surface)
    _draw_panel(surface, rect, border)
    _draw_lines(surface, lines, rect.centerx, rect.top + PANEL_PADDING)


def _wrapped(font: pygame.font.Font, text: str, width: int, color: tuple[int, int, int]):
    return [(font, line, color) for line in wrap_text(font, text, width)]


# ---------- HUD ----------

START_PROMPT = "Press Enter or the button to start"


def _patty_word(count: int) -> str:
    return "Krabby Patty" if count == 1 else "Krabby Patties"


def _draw_stopwatch(surface: pygame.Surface, center: tuple[int, int], color) -> None:
    x, y = center
    pygame.draw.rect(surface, color, (x - 2, y - STOPWATCH_RADIUS - 4, 4, 3))  # top button
    pygame.draw.circle(surface, color, center, STOPWATCH_RADIUS, width=2)
    pygame.draw.line(surface, color, center, (x, y - STOPWATCH_RADIUS + 3), 2)
    pygame.draw.line(surface, color, center, (x + 3, y), 2)


def _draw_countdown(
    surface: pygame.Surface, fonts: Fonts, time_left: float, midbottom: tuple[int, int]
) -> None:
    """Small stopwatch + "0:37" riding on top of the patty stack, so it's
    clear the stack is a timer."""
    seconds = math.ceil(time_left)
    color = WARNING_COLOR if seconds <= TIMER_WARNING_SECONDS else TEXT_COLOR
    text = fonts.small.render(f"{seconds // 60}:{seconds % 60:02d}", True, color)
    icon_width = STOPWATCH_RADIUS * 2
    content = pygame.Rect(0, 0, icon_width + STOPWATCH_GAP + text.get_width(), text.get_height())
    content.midbottom = midbottom
    _draw_panel(surface, content.inflate(20, 10), color)
    _draw_stopwatch(surface, (content.left + STOPWATCH_RADIUS, content.centery + 1), color)
    surface.blit(text, text.get_rect(midleft=(content.left + icon_width + STOPWATCH_GAP, content.centery)))


def draw_hud(
    surface: pygame.Surface,
    fonts: Fonts,
    round_: HabitatRound,
    patty: pygame.Surface,
    elapsed: float,
) -> None:
    """The timer is the patty stack on the left; the banked score is top right."""
    count = round_.patties_left
    seconds_until_next_loss = round_.time_left - (count - 1) * round_.rules.seconds_per_patty
    top = draw_patty_stack(surface, patty, count, seconds_until_next_loss, elapsed)

    _draw_countdown(surface, fonts, round_.time_left, midbottom=(top.centerx, top.top - 10))

    score = fonts.body.render(f"{_patty_word(round_.score)}: {round_.score}", True, TEXT_COLOR)
    picks = fonts.small.render(
        f"Statues {len(round_.pieces)}/{COMBINATION_SIZE}", True, MUTED_TEXT_COLOR
    )
    score_rect = score.get_rect(topright=(surface.get_width() - 24, HUD_TOP + 8))
    picks_rect = picks.get_rect(topright=(score_rect.right, score_rect.bottom + 4))
    _draw_panel(surface, score_rect.union(picks_rect).inflate(28, 16), ACCENT_COLOR)
    surface.blit(score, score_rect)
    surface.blit(picks, picks_rect)


# ---------- Intro cards ----------

def _phase_1_instructions(round_: HabitatRound) -> str:
    return (
        f"Scan {COMBINATION_SIZE} statues that {round_.habitat.name} would love. "
        f"The Krabby Patty stack on the left is your timer: it starts with "
        f"{PHASE_1.timer_patties} and loses one every {PHASE_1.seconds_per_patty:g} seconds. "
        f"You keep the patties that are left, plus {PHASE_1.statue_patties} for every "
        f"statue that fits!"
    )


def _phase_2_instructions(round_: HabitatRound) -> str:
    wrong = len(round_.hints())
    earned = round_.phase_score(1)
    return (
        f"Phase 1 earned you {earned} {_patty_word(earned)}. "
        f"{wrong} {'piece needs' if wrong == 1 else 'pieces need'} changing - scan new "
        f"statues to swap them out. This time the stack has only {PHASE_2.timer_patties} "
        f"patties and each statue that fits earns {PHASE_2.statue_patties}."
    )


def draw_intro(surface: pygame.Surface, fonts: Fonts, round_: HabitatRound) -> None:
    habitat = round_.habitat
    width = 700
    text_width = width - PANEL_PADDING * 2
    if round_.phase == 1:
        heading, border = f"Phase 1: Build {habitat.name}'s habitat!", ACCENT_COLOR
        instructions = _phase_1_instructions(round_)
    else:
        heading, border = "Phase 2: Not quite - fix it!", WARNING_COLOR
        instructions = _phase_2_instructions(round_)
    lines = [
        (fonts.title, heading, border),
        (fonts.body, f"What {habitat.name} likes:", MUTED_TEXT_COLOR),
        *_wrapped(fonts.body, habitat.blurb, text_width, TEXT_COLOR),
        (fonts.small, "", TEXT_COLOR),
        *_wrapped(fonts.small, instructions, text_width, TEXT_COLOR),
        (fonts.small, "", TEXT_COLOR),
        (fonts.body, START_PROMPT, ACCENT_COLOR),
    ]
    _card(surface, lines, width, border)


# ---------- Phase 2 ----------

def draw_highlight(
    surface: pygame.Surface, fonts: Fonts, rect: pygame.Rect, number: int, elapsed: float
) -> None:
    pulse = 0.5 + 0.5 * math.sin(elapsed * HIGHLIGHT_PULSE_HZ * 2 * math.pi)
    radius = max(rect.width, rect.height) // 2 + 10 + round(4 * pulse)
    pygame.draw.circle(surface, WARNING_COLOR, rect.center, radius, width=4)
    badge = fonts.small.render(str(number), True, TEXT_COLOR)
    badge_center = (rect.centerx + radius - 4, rect.centery - radius + 4)
    pygame.draw.circle(surface, WARNING_COLOR, badge_center, 13)
    surface.blit(badge, badge.get_rect(center=badge_center))


def draw_hint_panel(surface: pygame.Surface, fonts: Fonts, hints: tuple[Hint, ...]) -> None:
    if not hints:
        return
    width = 620
    text_width = width - PANEL_PADDING * 2
    lines = []
    for number, hint in enumerate(hints, start=1):
        lines.extend(_wrapped(fonts.small, f"{number}. {hint.text}", text_width, TEXT_COLOR))
    height = sum(fonts.small.get_linesize() + LINE_GAP for _ in lines) + PANEL_PADDING
    rect = pygame.Rect(0, 0, width, height)
    rect.midtop = (surface.get_width() // 2, 110)
    _draw_panel(surface, rect, WARNING_COLOR)
    y = rect.top + PANEL_PADDING // 2
    for font, text, color in lines:
        rendered = font.render(text, True, color)
        surface.blit(rendered, (rect.left + PANEL_PADDING, y))
        y += font.get_linesize() + LINE_GAP


# ---------- Results ----------

def draw_results(surface: pygame.Surface, fonts: Fonts, round_: HabitatRound) -> None:
    if round_.perfect_first_try:
        heading, border = "Perfect habitat on the first try!", GOOD_COLOR
    elif round_.is_perfect:
        heading, border = "You fixed it - perfect habitat!", GOOD_COLOR
    else:
        heading, border = "Time's up!", WARNING_COLOR
    lines = [(fonts.title, heading, border)]
    for entry in round_.ledger:
        color = TEXT_COLOR if entry.patties else MUTED_TEXT_COLOR
        lines.append((fonts.small, f"Phase {entry.phase} - {entry.label}: +{entry.patties}", color))
    lines += [
        (fonts.small, "", TEXT_COLOR),
        (fonts.title, f"Total: {round_.score} {_patty_word(round_.score)}", ACCENT_COLOR),
        (fonts.small, "Press Enter or the button to go back to the menu", MUTED_TEXT_COLOR),
    ]
    _card(surface, lines, 700, border)

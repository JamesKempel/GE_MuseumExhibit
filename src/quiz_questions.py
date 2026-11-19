"""Trivia questions for the end-of-round quiz, transcribed from
questions.md (that file is the human-editable source; this module is
what the game actually reads). Keyed by the exact Habitat.name strings
in habitats.py."""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class QuizQuestion:
    text: str
    options: tuple[str, ...]
    correct_index: int


QUESTIONS_BY_HABITAT: dict[str, tuple[QuizQuestion, ...]] = {
    "Patrick": (
        QuizQuestion(
            "What does Patrick like to eat?",
            ("Sea Urchins", "Fish", "Shrimp", "Rocks"),
            correct_index=0,
        ),
        QuizQuestion(
            "What environment does Patrick like to live in?",
            ("Private Jet", "Mud", "Underwater Volcano", "Pineapple"),
            correct_index=1,
        ),
        QuizQuestion(
            "Why does Patrick like kelp in his environment?",
            (
                "Sea urchins eat kelp and Patrick eats sea urchins",
                "Patrick likes to use the kelp as a blanket when he is cold",
                "Kelp attracts fish for Patrick to play with",
                "Patrick likes to play in the kelp",
            ),
            correct_index=0,
        ),
    ),
    "SpongeBob": (
        QuizQuestion(
            "Why does SpongeBob like coral in his environment?",
            (
                "Coral is colorful and gives SpongeBob a place to blend in and hide",
                "SpongeBob likes to eat coral",
                "SpongeBob likes to play with the coral",
                "SpongeBob eats fish that hide in the coral",
            ),
            correct_index=0,
        ),
        QuizQuestion(
            "Why does SpongeBob like rocks and shells in his environment?",
            (
                "SpongeBob eats rocks and shells",
                "SpongeBob likes to play with shells and kick rocks",
                "SpongeBob attaches to hard objects like rocks and shells",
                "SpongeBob throws the rocks at predators and uses the shells as a shield",
            ),
            correct_index=2,
        ),
    ),
    "Mr. Krabs": (
        QuizQuestion(
            "What does Krabs like to eat?",
            ("Fish", "Kelp", "Rocks", "Jellyfish"),
            correct_index=0,
        ),
        QuizQuestion(
            "Why does Mr. Krabs like clams?",
            (
                "Because crabs eats clams",
                "Clams eat crabs",
                "Because clams eat fish and crabs doesn't like fish",
                "Because clams don't interact with crabs",
            ),
            correct_index=0,
        ),
        QuizQuestion(
            "What does mud do for Krabs?",
            (
                "Because mud is comfy for crabs",
                "Because mud has a lot of bugs",
                "Because mud isn't normally in his home",
                "Because mud makes him a lot of money",
            ),
            correct_index=0,
        ),
        QuizQuestion(
            "Why does Krabs like fish?",
            (
                "Crabs eats fish",
                "Fish clean environment for the crabs",
                "Fish eat crabs",
                "Crabs don't need fish",
            ),
            correct_index=0,
        ),
    ),
    "Squidward": (
        QuizQuestion(
            "Why is coral helpful for Squidward's environment?",
            (
                "Squidward likes to play in the coral",
                "Squidward uses the multiple colors of the coral to blend in and hide",
                "Squidward likes to eat coral",
                "Squidward does not like coral",
            ),
            correct_index=1,
        ),
        QuizQuestion(
            "What do clams do for Squidward?",
            (
                "By eating clams, Squidward gets nutrients that help him grow and have energy",
                "Clams clamp down on Squidward's arms and prevent him from moving around",
                "Clams are fun for Squidward to throw",
            ),
            correct_index=0,
        ),
    ),
    "Sandy": (
        QuizQuestion(
            "Why does planting acorns help Sandy's home?",
            ("Acorns help trees grow", "Acorns are fun to throw around", "Acorns are good to use as a pillow"),
            correct_index=0,
        ),
        QuizQuestion(
            "What does the sun help Sandy with?",
            ("Trees need the sun to grow", "The sun is nice to look at", "Sandy likes to tan"),
            correct_index=0,
        ),
        QuizQuestion(
            "Why does Sandy have trees in her habitat?",
            (
                "They add color and make her happy",
                "They provide oxygen and soak up carbon dioxide",
                "They tell her what season it is when the leaves change colors",
            ),
            correct_index=1,
        ),
    ),
}


def random_question(habitat_name: str) -> QuizQuestion:
    return random.choice(QUESTIONS_BY_HABITAT[habitat_name])

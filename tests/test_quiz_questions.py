import habitats
from quiz_questions import QUESTIONS_BY_HABITAT, random_question


def test_every_habitat_has_at_least_one_question():
    for habitat in habitats.ALL_HABITATS:
        assert habitat.name in QUESTIONS_BY_HABITAT
        assert len(QUESTIONS_BY_HABITAT[habitat.name]) >= 1


def test_every_question_has_a_valid_correct_index_and_at_least_two_options():
    for questions in QUESTIONS_BY_HABITAT.values():
        for question in questions:
            assert len(question.options) >= 2
            assert 0 <= question.correct_index < len(question.options)


def test_random_question_returns_one_from_that_habitats_pool():
    pool = QUESTIONS_BY_HABITAT["Patrick"]
    for _ in range(20):
        assert random_question("Patrick") in pool


if __name__ == "__main__":
    test_every_habitat_has_at_least_one_question()
    test_every_question_has_a_valid_correct_index_and_at_least_two_options()
    test_random_question_returns_one_from_that_habitats_pool()
    print("OK")

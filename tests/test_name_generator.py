from name_generator import ADJECTIVES, NOUNS, random_display_name


def test_random_display_name_is_an_adjective_and_a_noun_from_the_pools():
    for _ in range(20):
        name = random_display_name()
        parts = name.split(" ")
        assert len(parts) == 2
        assert parts[0] in ADJECTIVES
        assert parts[1] in NOUNS


if __name__ == "__main__":
    test_random_display_name_is_an_adjective_and_a_noun_from_the_pools()
    print("OK")

import statue_tags


def test_new_tags_map_to_expected_statues():
    expected = {
        "4042C3BE": "SEA_URCHIN",
        "C0BBC3BE": "SHELL",
        "D040C4BE": "ROCK",
        "506EC4BE": "CLAM",
        "D0B6C3BE": "CORAL",
    }
    for uid, statue in expected.items():
        assert statue_tags.TAG_TO_STATUE.get(uid) == statue, f"{uid} -> {statue_tags.TAG_TO_STATUE.get(uid)}"


def test_import_does_not_raise_on_duplicate_tags():
    # build_tag_lookup() already ran at import time; if a new UID had
    # collided with an existing one (e.g. the KELP prototype tag) the
    # import itself would have raised ValueError before reaching here.
    assert len(statue_tags.TAG_TO_STATUE) >= 6  # 5 new + the existing KELP prototype tag


if __name__ == "__main__":
    test_new_tags_map_to_expected_statues()
    test_import_does_not_raise_on_duplicate_tags()
    print("OK")

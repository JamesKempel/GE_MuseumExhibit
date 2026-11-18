import rfid


def test_classify_line_recognizes_each_button_and_uid_and_ignores_junk():
    assert rfid._classify_line("Button: prev pressed") == ("button", "prev")
    assert rfid._classify_line("Button: next pressed") == ("button", "next")
    assert rfid._classify_line("Button: enter pressed") == ("button", "enter")
    assert rfid._classify_line("Card UID: AA E1 16 DC") == ("uid", "AAE116DC")
    assert rfid._classify_line("RC522 version: 0x92") is None


def test_poll_methods_drain_only_their_own_queue():
    reader = rfid.RFIDReader()
    try:
        reader._button_presses["prev"].put(None)
        reader._button_presses["prev"].put(None)
        reader._button_presses["next"].put(None)
        assert reader.poll_prev_presses() == 2
        assert reader.poll_next_presses() == 1
        assert reader.poll_enter_presses() == 0
        assert reader.poll_prev_presses() == 0  # draining again returns 0, not an error
    finally:
        reader.stop()


def test_send_score_is_a_no_op_when_not_connected():
    reader = rfid.RFIDReader()
    try:
        reader.send_score(42)  # must not raise even though nothing is connected
    finally:
        reader.stop()


def test_send_score_writes_to_the_active_connection():
    class FakeConnection:
        def __init__(self):
            self.written = b""

        def write(self, data):
            self.written += data

    reader = rfid.RFIDReader()
    try:
        fake = FakeConnection()
        with reader._connection_lock:
            reader._connection = fake
        reader.send_score(7)
        assert fake.written == b"SCORE 7\n"
    finally:
        reader.stop()


if __name__ == "__main__":
    test_classify_line_recognizes_each_button_and_uid_and_ignores_junk()
    test_poll_methods_drain_only_their_own_queue()
    test_send_score_is_a_no_op_when_not_connected()
    test_send_score_writes_to_the_active_connection()
    print("OK")

from auto_leetcode.leetcode.submitter import _parse_float, _parse_int


class TestParseInt:
    def test_normal(self) -> None:
        assert _parse_int("40 ms") == 40

    def test_no_unit(self) -> None:
        assert _parse_int("100") == 100

    def test_none(self) -> None:
        assert _parse_int(None) is None

    def test_invalid(self) -> None:
        assert _parse_int("abc") is None


class TestParseFloat:
    def test_normal(self) -> None:
        assert _parse_float("16.5 MB") == 16.5

    def test_no_unit(self) -> None:
        assert _parse_float("20.0") == 20.0

    def test_none(self) -> None:
        assert _parse_float(None) is None

    def test_invalid(self) -> None:
        assert _parse_float("xyz") is None

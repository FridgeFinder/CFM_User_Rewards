"""Unit tests for rules.py"""

from rules import get_fridge_report_awards


class TestGetFridgeReportAwards:
    #NOTE: remove this test once the function is implemented
    def test_returns_none(self):
        result = get_fridge_report_awards("", "")
        assert result is None

"""Tests for akcli library"""

from datetime import datetime, timedelta, timezone


class TestTradingCalendar:
    """Tests for trading calendar module"""

    def test_is_trading_day_weekend(self):
        """Weekend should not be trading day"""
        from akcli.trading_calendar import is_trading_day

        saturday = datetime(2024, 6, 8, 12, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        sunday = datetime(2024, 6, 9, 12, 0, 0, tzinfo=timezone(timedelta(hours=8)))

        assert is_trading_day(saturday) == 0
        assert is_trading_day(sunday) == 0

    def test_prev_trading_day(self):
        """Test previous trading day calculation"""
        from akcli.trading_calendar import prev_trading_day

        monday = datetime(2024, 6, 10, 12, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        prev = prev_trading_day(monday)

        assert prev.weekday() < 5


class TestTTL:
    """Tests for TTL module"""

    def test_ttl_default(self):
        """Test default TTL"""
        from akcli.ttl import ttl

        result = ttl("unknown_api")
        assert result == 1800

    def test_ttl_with_params(self):
        """Test TTL with function name"""
        from akcli.ttl import ttl

        result = ttl("stock_zh_a_hist")
        assert isinstance(result, int)

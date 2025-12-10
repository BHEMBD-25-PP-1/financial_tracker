import datetime

import pytest
from pydantic import ValidationError

from app.analytics import models as m


def test_summary_response_valid():
    obj = m.SummaryResponse(
        total_income=100.0,
        total_expense=50.0,
        balance=50.0,
        transaction_count=2,
    )
    assert obj.balance == 50.0


def test_period_type_enum_invalid():
    with pytest.raises(ValueError):
        m.PeriodType("invalid")


def test_trends_response_nested():
    trend = m.TrendInfo(direction="up", change_percentage=10.0, average_daily=5.0)
    resp = m.TrendsResponse(income_trend=trend, expense_trend=trend)
    assert resp.income_trend.direction == m.TrendDirection.UP


def test_category_analytics_response_list():
    stat = m.CategoryStatistic(category="Еда", total_amount=10.0, transaction_count=2)
    resp = m.CategoryAnalyticsResponse(categories=[stat])
    assert resp.categories[0].category == "Еда"


from datetime import timedelta
import pytest

from homeassistant.util.dt import utcnow
from integration import get_test_context
from custom_components.octopus_energy.api_client import OctopusEnergyApiClient

@pytest.mark.asyncio
async def test_when_get_electricity_consumption_costs_is_called_then_half_hourly_costs_returned():
    # Arrange
    context = get_test_context()

    client = OctopusEnergyApiClient(context.api_key)
    period_from = (utcnow() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    period_to = period_from + timedelta(days=1)

    # Act
    costs = await client.async_get_electricity_consumption_costs(context.account_id, context.electricity_mpan, period_from, period_to)

    # Assert
    assert len(costs) == 48

    expected_start = period_from
    for cost in costs:
        assert cost["start"] == expected_start
        assert cost["end"] == expected_start + timedelta(minutes=30)
        assert cost["consumption"] >= 0
        assert cost["cost"] >= 0

        expected_start = cost["end"]

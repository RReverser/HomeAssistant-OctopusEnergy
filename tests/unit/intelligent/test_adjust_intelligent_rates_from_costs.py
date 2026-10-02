import pytest

from homeassistant.util.dt import parse_datetime
from custom_components.octopus_energy.intelligent import adjust_intelligent_rates_from_costs
from tests.integration import create_rate_data

peak_rate = 30.1
off_peak_rate = 9.11

def create_rates():
  rates = []
  rates.extend(create_rate_data(
    parse_datetime("2022-10-09T12:00:00Z"),
    parse_datetime("2022-10-09T23:30:00Z"),
    [peak_rate]
  ))
  rates.extend(create_rate_data(
    parse_datetime("2022-10-09T23:30:00Z"),
    parse_datetime("2022-10-10T05:30:00Z"),
    [off_peak_rate]
  ))
  rates.extend(create_rate_data(
    parse_datetime("2022-10-10T05:30:00Z"),
    parse_datetime("2022-10-10T12:00:00Z"),
    [peak_rate]
  ))
  return rates

def create_costs(rates, charged_rates: dict, consumption = 0.5):
  # What Octopus charged for each period: its own rate, unless charged_rates says otherwise. Costs are rounded to a hundredth of a
  # penny, as Octopus returns them.
  return list(map(lambda rate: {
    "start": rate["start"],
    "end": rate["end"],
    "consumption": consumption,
    "cost": round(consumption * charged_rates.get(rate["start"].isoformat(), rate["value_inc_vat"]), 2)
  }, rates))

@pytest.mark.asyncio
async def test_when_rates_empty_then_empty_rates_returned():
  # Arrange
  rates = []

  # Act
  adjusted_rates = adjust_intelligent_rates_from_costs(rates, [])

  # Assert
  assert adjusted_rates == rates

@pytest.mark.asyncio
async def test_when_all_periods_charged_at_their_rates_then_rates_not_adjusted():
  # Arrange
  rates = create_rates()
  costs = create_costs(rates, {})

  # Act
  adjusted_rates = adjust_intelligent_rates_from_costs(rates, costs)

  # Assert
  assert adjusted_rates == rates

@pytest.mark.asyncio
async def test_when_peak_periods_charged_at_off_peak_rate_then_those_rates_adjusted():
  # Arrange
  rates = create_rates()
  dispatched = ["2022-10-09T18:00:00+00:00", "2022-10-09T18:30:00+00:00", "2022-10-10T06:00:00+00:00"]
  costs = create_costs(rates, dict((start, off_peak_rate) for start in dispatched), consumption=0.013)

  # Act
  adjusted_rates = adjust_intelligent_rates_from_costs(rates, costs)

  # Assert
  assert len(adjusted_rates) == len(rates)
  for index, rate in enumerate(adjusted_rates):
    assert rate["start"] == rates[index]["start"]
    assert rate["end"] == rates[index]["end"]
    if rate["start"].isoformat() in dispatched:
      assert rate["value_inc_vat"] == off_peak_rate
      assert rate["is_intelligent_adjusted"] == True
      assert rate["tariff_code"] == rates[index]["tariff_code"]
      assert rate["is_capped"] == rates[index]["is_capped"]
    else:
      assert rate == rates[index]

@pytest.mark.asyncio
async def test_when_periods_have_no_consumption_then_rates_not_adjusted():
  # Arrange
  rates = create_rates()
  costs = create_costs(rates, {}, consumption=0)

  # Act
  adjusted_rates = adjust_intelligent_rates_from_costs(rates, costs)

  # Assert
  assert adjusted_rates == rates

@pytest.mark.asyncio
async def test_when_periods_have_no_costs_then_rates_not_adjusted():
  # Arrange
  rates = create_rates()
  costs = create_costs(rates, { "2022-10-09T18:00:00+00:00": off_peak_rate })[0:1]

  # Act
  adjusted_rates = adjust_intelligent_rates_from_costs(rates, costs)

  # Assert
  assert adjusted_rates == rates

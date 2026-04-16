"""Tests for lightcurve plotting helpers, focusing on SNR-based filtering."""

from typing import Any

from babamul.lightcurves import SNR_THRESHOLD, get_prv_candidates


def make_alert(prv_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {"prv_candidates": prv_candidates}


def test_snr_threshold_constant():
    """SNR_THRESHOLD should be 3."""
    assert SNR_THRESHOLD == 3


def test_high_snr_is_detection():
    """Data points with SNR > threshold should be included as detections."""
    alert = make_alert(
        [
            {
                "jd": 2460500.5,
                "magpsf": 18.5,
                "sigmapsf": 0.1,
                "diffmaglim": 20.5,
                "band": "r",
                "snr": 20.0,
            }
        ]
    )
    result = get_prv_candidates(alert)
    assert len(result) == 1
    assert result[0]["lim"] is False
    assert result[0]["mag"] == 18.5
    assert result[0]["magerr"] == 0.1


def test_low_snr_becomes_non_detection():
    """Data points with SNR <= threshold should be treated as non-detections using diffmaglim."""
    alert = make_alert(
        [
            {
                "jd": 2460500.5,
                "magpsf": 18.5,
                "sigmapsf": 1500.0,
                "diffmaglim": 20.5,
                "band": "z",
                "snr": 0.01,
            }
        ]
    )
    result = get_prv_candidates(alert)
    assert len(result) == 1
    assert result[0]["lim"] is True
    assert result[0]["mag"] == 20.5  # uses diffmaglim, not the bad magpsf


def test_low_snr_no_diffmaglim_is_skipped():
    """Data points with SNR <= threshold and no diffmaglim should be skipped entirely."""
    alert = make_alert(
        [
            {
                "jd": 2460500.5,
                "magpsf": 18.5,
                "sigmapsf": 1500.0,
                "diffmaglim": None,
                "band": "z",
                "snr": 0.01,
            }
        ]
    )
    result = get_prv_candidates(alert)
    assert len(result) == 0


def test_zero_snr_with_diffmaglim_is_non_detection():
    """Data points with SNR=0 and diffmaglim should be treated as non-detections."""
    alert = make_alert(
        [
            {
                "jd": 2460500.5,
                "magpsf": 99.9,
                "sigmapsf": 9999.0,
                "diffmaglim": 21.0,
                "band": "g",
                "snr": 0.0,
            }
        ]
    )
    result = get_prv_candidates(alert)
    assert len(result) == 1
    assert result[0]["lim"] is True
    assert result[0]["mag"] == 21.0


def test_no_snr_no_mag_is_skipped():
    """Data points with no SNR and no mag/magerr should be skipped."""
    alert = make_alert([{"jd": 2460500.5, "band": "r"}])
    result = get_prv_candidates(alert)
    assert len(result) == 0


def test_multiple_mixed_snr():
    """Multiple candidates with mixed SNR are handled correctly."""
    alert = make_alert(
        [
            # Good detection
            {
                "jd": 2460500.5,
                "magpsf": 18.5,
                "sigmapsf": 0.1,
                "diffmaglim": 20.5,
                "band": "r",
                "snr": 20.0,
            },
            # Bad data point -> non-detection
            {
                "jd": 2460501.5,
                "magpsf": 18.5,
                "sigmapsf": 1500.0,
                "diffmaglim": 20.5,
                "band": "z",
                "snr": 0.01,
            },
            # Bad data point, no diffmaglim -> skipped
            {
                "jd": 2460502.5,
                "magpsf": 18.5,
                "sigmapsf": 9999.0,
                "diffmaglim": None,
                "band": "z",
                "snr": 1.0,
            },
        ]
    )
    result = get_prv_candidates(alert)
    assert len(result) == 2
    assert result[0]["lim"] is False
    assert result[1]["lim"] is True


def test_empty_prv_candidates():
    """Empty prv_candidates list returns empty result."""
    alert = make_alert([])
    result = get_prv_candidates(alert)
    assert result == []


def test_missing_prv_candidates_key():
    """Alert dict with no prv_candidates key returns empty result."""
    result = get_prv_candidates({})
    assert result == []

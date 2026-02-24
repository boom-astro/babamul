from enum import Enum
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import pandas as pd

if TYPE_CHECKING:
    from matplotlib.axes import Axes

# Define colors for bands
band_colors = {
    "g": "green",
    "r": "red",
    "i": "orange",
    "z": "purple",
    "y": "brown",
    "u": "blue",
}

surveys = ["ztf", "lsst"]


def get_key_from_any(data: Any, key: str, default: Any = None) -> Any:
    # Handle both dict and classes
    if isinstance(data, dict):
        return data.get(key, default)
    else:
        return getattr(data, key, default)


def _normalize_band(band: Any) -> str:
    """Normalize a band value to a plain string, handling Enum instances."""
    if isinstance(band, Enum):
        return band.value
    return str(band)


# to avoid duplication, let's write some helper functions that prepare the data for each type of lightcurve
def get_prv_candidates(alert: dict[str, Any] | Any):
    data = []
    for prv in get_key_from_any(alert, "prv_candidates", []):
        data.append(
            {
                "mjd": get_key_from_any(prv, "jd", 0) - 2400000.5,
                "mag": get_key_from_any(prv, "magpsf", 0),
                "magerr": get_key_from_any(prv, "sigmapsf", 0.1),
                "band": get_key_from_any(prv, "band", "unknown"),
                "lim": False,
            }
        )
    return data


def get_prv_nondetections(alert: dict[str, Any] | Any):
    data = []
    for lim in get_key_from_any(alert, "prv_nondetections", []):
        data.append(
            {
                "mjd": get_key_from_any(lim, "jd", 0) - 2400000.5,
                "mag": get_key_from_any(lim, "diffmaglim", 0),
                "magerr": 0.3,  # arbitrary error for limits
                "band": get_key_from_any(lim, "band", "unknown"),
                "lim": True,
            }
        )
    return data


def get_fp_hists(alert: dict[str, Any] | Any):
    data = []
    for fp in get_key_from_any(alert, "fp_hists", []):
        snr = get_key_from_any(fp, "snr", 0)
        if snr and snr > 3:
            data.append(
                {
                    "mjd": get_key_from_any(fp, "jd", 0) - 2400000.5,
                    "mag": get_key_from_any(fp, "magpsf", 0),
                    "magerr": get_key_from_any(fp, "sigmapsf", 0.1),
                    "band": get_key_from_any(fp, "band", "unknown"),
                    "lim": False,
                }
            )
        elif get_key_from_any(fp, "diffmaglim") is not None:
            data.append(
                {
                    "mjd": get_key_from_any(fp, "jd", 0) - 2400000.5,
                    "mag": get_key_from_any(fp, "diffmaglim", 0),
                    "magerr": 0.3,
                    "band": get_key_from_any(fp, "band", "unknown"),
                    "lim": True,
                }
            )
    return data


def get_survey_matches(alert: dict[str, Any] | Any) -> list[dict[str, Any]]:
    data = []
    survey_matches = get_key_from_any(alert, "survey_matches", {})
    for survey in surveys:
        match = get_key_from_any(survey_matches, survey, None)
        if match is None:
            continue
        # match also has a prv_candidates and fp_hists.
        # Only ZTF matches are expected to expose prv_nondetections.
        data.extend(get_prv_candidates(match))
        if survey == "ztf":
            data.extend(get_prv_nondetections(match))
        data.extend(get_fp_hists(match))
    return data


def plot_lightcurve(
    alert: dict[str, Any] | Any,
    include_survey_matches: bool = True,
    include_nondetections: bool = True,
    ax: "Axes | None" = None,
    show: bool = True,
) -> None:
    """
    Plot the lightcurve for a ZTF alert, including survey matches photometry.

    Parameters:
    -----------
    alert : dict | Any
        The alert dictionary or model instance containing cutout data.
    include_survey_matches : bool, optional
        Whether to include photometry from survey matches. Default is True.
    include_nondetections : bool, optional
        Whether to include non-detection upper limits. Default is True.
    ax : matplotlib.axes.Axes, optional
        The axes to plot on. If None, a new figure and axes will be created.
    show : bool, optional
        Whether to display the plot immediately. Default is True.
    """

    # Combine current and previous detections
    all_detections = []

    all_detections.extend(get_prv_candidates(alert))
    all_detections.extend(get_prv_nondetections(alert))
    all_detections.extend(get_fp_hists(alert))
    if include_survey_matches:
        all_detections.extend(get_survey_matches(alert))

    df = pd.DataFrame(all_detections)
    if not df.empty:
        df["band"] = df["band"].apply(_normalize_band)
    if not include_nondetections:
        df = df[~df["lim"]]

    # Plot
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    for band in df["band"].unique():
        band_data = df[df["band"] == band]
        detections = band_data[~band_data["lim"]]
        limits = band_data[band_data["lim"]]

        color = band_colors.get(band, "gray")

        # Plot detections
        if len(detections) > 0:
            ax.errorbar(
                detections["mjd"],
                detections["mag"],
                yerr=detections["magerr"],
                fmt="o",
                color=color,
                label=f"{band}-band",
                markersize=8,
                capsize=3,
            )

        # Plot upper limits
        if len(limits) > 0:
            ax.scatter(
                limits["mjd"],
                limits["mag"],
                marker="v",
                color=color,
                alpha=0.3,
                s=50,
            )

    ax.invert_yaxis()
    ax.ticklabel_format(axis="x", style="plain", useOffset=False)
    ax.set_xlabel("MJD", fontsize=12)
    ax.set_ylabel("AB Mag", fontsize=12)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    if show:
        title = f"Lightcurve for {get_key_from_any(alert, 'objectId', 'Unknown Object')}"
        if include_survey_matches:
            survey_matches = get_key_from_any(alert, "survey_matches", {})
            match_ids = []
            for survey in surveys:
                match = get_key_from_any(survey_matches, survey, None)
                if match is not None:
                    match_id = get_key_from_any(match, "objectId", None)
                    if match_id is not None:
                        match_ids.append(f"{survey}: {match_id}")
            if match_ids:
                title += " (Matches: " + ", ".join(match_ids) + ")"
        ax.set_title(title, fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.show()

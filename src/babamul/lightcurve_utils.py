from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

# Define colors for bands
band_colors = {
    "g": "green",
    "r": "red",
    "i": "orange",
    "z": "purple",
    "y": "brown",
    "u": "blue",
}


def get_key_from_any(data: Any, key: str, default=None):
    # Handle both dict and classes
    if isinstance(data, dict):
        return data.get(key, default)
    else:
        return getattr(data, key, default)


def plot_lightcurve(
    alert: dict[str, Any], ax: plt.Axes | None = None, show: bool = True
):
    """
    Plot the lightcurve for a ZTF alert.

    Parameters:
    -----------
    alert : dict
        The alert dictionary or model instance containing cutout data.
    """

    # Combine current and previous detections
    all_detections = []

    # Add previous detections
    for prv in get_key_from_any(alert, "prv_candidates", []):
        all_detections.append(
            {
                "mjd": get_key_from_any(prv, "jd", 0) - 2400000.5,
                "mag": get_key_from_any(prv, "magpsf", 0),
                "magerr": get_key_from_any(prv, "sigmapsf", 0.1),
                "band": get_key_from_any(prv, "band", "unknown"),
                "lim": False,
            }
        )
    for lim in get_key_from_any(alert, "prv_nondetections", []):
        all_detections.append(
            {
                "mjd": get_key_from_any(lim, "jd", 0) - 2400000.5,
                "mag": get_key_from_any(lim, "diffmaglim", 0),
                "magerr": 0.3,  # arbitrary error for limits
                "band": get_key_from_any(lim, "band", "unknown"),
                "lim": True,
            }
        )
    for fp in get_key_from_any(alert, "fp_hists", []):
        snr = get_key_from_any(fp, "snr", 0)
        if snr and snr > 3:
            all_detections.append(
                {
                    "mjd": get_key_from_any(fp, "jd", 0) - 2400000.5,
                    "mag": get_key_from_any(fp, "magpsf", 0),
                    "magerr": get_key_from_any(fp, "sigmapsf", 0.1),
                    "band": get_key_from_any(fp, "band", "unknown"),
                    "lim": False,
                }
            )
        elif get_key_from_any(fp, "diffmaglim") is not None:
            all_detections.append(
                {
                    "mjd": get_key_from_any(fp, "jd", 0) - 2400000.5,
                    "mag": get_key_from_any(fp, "diffmaglim", 0),
                    "magerr": 0.3,
                    "band": get_key_from_any(fp, "band", "unknown"),
                    "lim": True,
                }
            )

    df = pd.DataFrame(all_detections)

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
    ax.set_xlabel("MJD", fontsize=12)
    ax.set_ylabel("AB Mag", fontsize=12)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    if show:
        ax.set_title(
            f"Lightcurve for {alert['objectId']}",
            fontsize=14,
            fontweight="bold",
        )
        plt.tight_layout()
        plt.show()

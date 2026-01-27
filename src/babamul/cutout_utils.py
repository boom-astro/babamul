import gzip
import io
import logging
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from astropy.visualization import (
    AsymmetricPercentileInterval,
    ImageNormalize,
    LinearStretch,
    LogStretch,
)
from scipy.ndimage import rotate

logger = logging.getLogger(__name__)

CUTOUT_TYPES = ["Science", "Template", "Difference"]


def plot_cutouts(
    alert: dict[str, Any],
    survey: str,
    use_rotation: bool = False,
    axes: list[plt.Axes] | None = None,
    show: bool = True,
    orientation: str = "horizontal",
    figsize: tuple | None = None,
    title: str | None = None,
) -> list[plt.Axes]:
    """
    Plot all three cutout images (Science, Template, Difference) for a ZTF alert.

    Parameters
    ----------
    alert : dict
        The alert dictionary or model instance containing cutout data.
    survey : str
        The survey name, e.g., "ZTF" or "LSST".
    use_rotation : bool, default=False
        Whether to apply rotation based on FITS header (if available).
    axes : list of matplotlib.axes.Axes, optional
        List of 3 axes to plot on. If None, creates new figure.
    show : bool, default=True
        Whether to call plt.show() after plotting.
    orientation : str, default='horizontal'
        Layout orientation: 'horizontal' or 'vertical'. (overwritten if axes is not None)
    figsize : tuple, optional
        Figure size. If None, uses defaults based on orientation.
    title : str, optional
        Overall figure title. If None, uses objectId.

    Returns
    -------
    list of matplotlib.axes.Axes
        List of the three axes objects.

    Examples
    --------
    >>> # Horizontal layout
    >>> plot_cutouts(alert)
    >>>
    >>> # Vertical layout with custom size
    >>> plot_cutouts(alert, orientation='vertical', figsize=(4, 10))
    """
    # Create figure if needed
    if axes is None:
        if figsize is None:
            figsize = (12, 4) if orientation == "horizontal" else (4, 10)

        if orientation == "horizontal":
            fig, axes = plt.subplots(1, 3, figsize=figsize)
        else:
            fig, axes = plt.subplots(3, 1, figsize=figsize)

    for ax, ctype in zip(axes, CUTOUT_TYPES, strict=True):
        cutout_key = f"cutout{ctype}"

        # Handle both dict and classes
        if isinstance(alert, dict):
            cutout_data = alert.get(cutout_key)
        else:
            cutout_data = getattr(alert, cutout_key, None)
        if cutout_data is None or cutout_data == b"":
            ax.set_title(f"No {ctype} cutout")
            ax.axis("off")
            logger.warning(f"{ctype} cutout missing in alert")
            continue

        # handle both compressed and uncompressed data
        rotpa = None
        try:
            with (
                gzip.open(io.BytesIO(cutout_data), "rb") as f,
                fits.open(
                    io.BytesIO(f.read()), ignore_missing_simple=True
                ) as hdu,
            ):
                rotpa = hdu[0].header.get("ROTPA", None)
                data = hdu[0].data
        except OSError:
            with fits.open(
                io.BytesIO(cutout_data), ignore_missing_simple=True
            ) as hdu:
                rotpa = hdu[0].header.get("ROTPA", None)
                data = hdu[0].data

        # Clean the data
        img = np.array(data)
        xl = np.greater(np.abs(img), 1e20, where=~np.isnan(img))
        if img[xl].any():
            img[xl] = np.nan
        if np.isnan(img).any():
            median = float(np.nanmean(img.flatten()))
            img = np.nan_to_num(img, nan=median)

        # Normalize
        stretch = LinearStretch() if ctype == "Difference" else LogStretch()
        norm = ImageNormalize(img, stretch=stretch)
        img_norm = norm(img)

        normalizer = AsymmetricPercentileInterval(
            lower_percentile=1, upper_percentile=100
        )
        vmin, vmax = normalizer.get_limits(img_norm)

        # Apply rotation if requested and ROTPA is present in header
        if use_rotation and rotpa is not None:
            try:
                # Rotate clockwise by ROTPA degrees, reshape to avoid cropping, fill blanks with 0
                img_norm = rotate(
                    img_norm,
                    -rotpa,
                    reshape=True,
                    order=1,
                    mode="constant",
                    cval=0.0,
                )
            except Exception as e:
                # If scipy is not available or rotation fails, skip rotation
                logger.warning(f"Rotation failed for {ctype} cutout: {e}")

        if survey == "ZTF":
            # For ZTF, flip upside down so north is up
            img_norm = np.flipud(img_norm)

        # Display
        ax.imshow(img_norm, cmap="bone", origin="lower", vmin=vmin, vmax=vmax)
        ax.set_title(ctype, fontsize=10)
        ax.axis("off")

    if show:
        if title is None:
            title = f"Thumbnails for {alert['objectId']}"
        plt.suptitle(title, fontsize=12, fontweight="bold")
        plt.tight_layout()
        plt.show()

    return axes

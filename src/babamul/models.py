"""Pydantic models for Babamul alerts."""

from datetime import timezone
from typing import TYPE_CHECKING, cast

import matplotlib.pyplot as plt
from astropy.time import Time
from pydantic import AliasChoices, BaseModel, Field, computed_field

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from .cutouts import plot_cutouts
from .lightcurves import plot_lightcurve
from .raw_models import (
    EnrichedLsstAlert,
    EnrichedZtfAlert,
    LsstAlertProperties,
    LsstCandidate,
    Photometry,
    ZtfAlertProperties,
    ZtfCandidate,
)

__all__ = [
    "AlertCutouts",
    "CrossMatches",
    "EnrichedLsstAlert",
    "EnrichedZtfAlert",
    "LsstAlert",
    "LsstCandidate",
    "NedMatch",
    "ObjectSearchResult",
    "ObjPhotometry",
    "Photometry",
    "UserProfile",
    "ZtfAlert",
    "ZtfCandidate",
    "add_cross_matches",
]

# --- API response models ---


class AlertCutouts(BaseModel):
    """Cutout images for an alert."""

    candid: int
    cutoutScience: bytes
    cutoutTemplate: bytes
    cutoutDifference: bytes

    model_config = {"arbitrary_types_allowed": True}


class ObjPhotometry(BaseModel):
    """Photometry data for an object."""

    objectId: str = Field(
        ..., validation_alias=AliasChoices("objectId", "object_id")
    )
    prv_candidates: list[Photometry] = Field(default_factory=list)
    prv_nondetections: list[Photometry] = Field(default_factory=list)
    fp_hists: list[Photometry] = Field(default_factory=list)


class ObjectSearchResult(BaseModel):
    """Result from object search."""

    objectId: str
    ra: float
    dec: float
    survey: str


class UserProfile(BaseModel):
    """User profile information."""

    id: str = Field(..., validation_alias=AliasChoices("id", "_id"))
    username: str
    email: str
    created_at: int


class NedMatch(BaseModel):
    objname: str | None = Field(
        None, validation_alias=AliasChoices("objname", "obj_name", "_id")
    )
    objtype: str | None = None
    ra: float
    dec: float
    z: float | None = None
    z_unc: float | None = None
    z_tech: str | None = None
    z_qual: str | bool | None = None
    DistMpc: float | None = None
    DistMpc_unc: float | None = None
    ebv: float | None = None
    distance_arcsec: float | None = None
    distance_kpc: float | None = None


class CatwiseMatch(BaseModel):
    source_name: str
    ra: float
    dec: float
    sigra: float | None = None
    sigdec: float | None = None
    w1mpro: float | None = None
    w2mpro: float | None = None
    w1sigmpro: float | None = None
    w2sigmpro: float | None = None
    w1rchi2: float | None = None
    w2rchi2: float | None = None
    pmra: float | None = None
    pmdec: float | None = None
    sigpmra: float | None = None
    sigpmdec: float | None = None
    unwise_objid: int | str | None = None
    distance_arcsec: float | None = None


class VsxMatch(BaseModel):
    name: str
    var_flag: str | int | None = None
    ra: float
    dec: float
    types: list[str] | None = None
    max: float | None = None
    max_band: str | None = None
    min_is_amplitude: bool | None = None
    min: float | None = None
    min_band: str | None = None
    epoch: float | None = None
    period: float | None = None
    spectral_type: str | None = None
    distance_arcsec: float | None = None


class MilliquasarMatch(BaseModel):
    _id: str
    ra: float
    dec: float
    distance_arcsec: float | None = None


class GaiaMatch(BaseModel):
    id: int | str = Field(..., validation_alias=AliasChoices("id", "_id"))
    ra: float
    dec: float
    parallax: float | None = None
    parallax_error: float | None = None
    pm: float | None = None
    pmra: float | None = None
    pmra_error: float | None = None
    pmdec: float | None = None
    pmdec_error: float | None = None
    phot_g_mean_mag: float | None = None
    phot_bp_mean_mag: float | None = None
    phot_rp_mean_mag: float | None = None
    phot_g_n_obs: int | None = None
    phot_bp_n_obs: int | None = None
    phot_rp_n_obs: int | None = None
    ruwe: float | None = None
    phot_bp_rp_excess_factor: float | None = None
    distance_arcsec: float | None = None


class LSPSCMatch(BaseModel):
    id: int | str = Field(..., validation_alias=AliasChoices("id", "_id"))
    ra: float
    dec: float
    score: float | None = None
    mag_white: float | None = None
    distance_arcsec: float | None = None


class CrossMatches(BaseModel):
    """Cross-matches with other surveys."""

    # survey name -> list of matches
    ned: list[NedMatch] | None = Field(
        [], validation_alias=AliasChoices("ned", "NED")
    )
    catwise: list[CatwiseMatch] | None = Field(
        [], validation_alias=AliasChoices("catwise", "CatWISE", "CatWISE2020")
    )
    vsx: list[VsxMatch] | None = Field(
        [], validation_alias=AliasChoices("vsx", "VSX")
    )
    milliquasar: list[MilliquasarMatch] | None = Field(
        [],
        validation_alias=AliasChoices(
            "milliquasar", "Milliquasar", "milliquas_v8"
        ),
    )
    gaia: list[GaiaMatch] | None = Field(
        [],
        validation_alias=AliasChoices("gaia", "Gaia", "Gaia_DR3", "Gaia_EDR3"),
    )
    lspsc: list[LSPSCMatch] | None = Field(
        [],
        validation_alias=AliasChoices(
            "lspsc", "LSPSC", "LegacySurveyPSCCatalog"
        ),
    )


# here we just want to re-export the raw model we autogenerated from
# avro using pydantic-avro, as the main model
# to which we add extra functions, like a `get_photometry` accessor
# that takes care of combining the different photometry sources
# (prv_candidates, prv_nondetections, fp_hists)
class ZtfAlert(EnrichedZtfAlert):
    """Pydantic model for a Babamul ZTF alert."""

    topic: str | None = None
    cross_matches: CrossMatches | None = None

    def get_photometry(self, deduplicated: bool = True) -> list[Photometry]:
        """Combine and return all photometry data from the alert."""
        if (
            self.prv_candidates is None
            and self.fp_hists is None
            and self.prv_nondetections is None
        ):
            from .api import get_photometry as get_photometry_from_api

            photometry_data = get_photometry_from_api("ZTF", self.objectId)
            self.prv_candidates = photometry_data.prv_candidates
            self.fp_hists = photometry_data.fp_hists
            self.prv_nondetections = photometry_data.prv_nondetections
        photometry: list[Photometry] = []
        # Add prv_candidates photometry
        if self.prv_candidates:
            photometry.extend(self.prv_candidates)
        # Add fp_hists photometry if available
        if self.fp_hists:
            photometry.extend(self.fp_hists)
        # Add prv_nondetections photometry
        if self.prv_nondetections:
            photometry.extend(self.prv_nondetections)

        # Sort photometry by Julian Date (jd)
        photometry.sort(key=lambda x: x.jd)

        # if deduplicated, remove duplicates based on (jd, band)
        if deduplicated:
            seen = set()
            deduped_photometry = []
            for p in photometry:
                key = (p.jd, p.band)
                if key not in seen:
                    seen.add(key)
                    deduped_photometry.append(p)
            photometry = deduped_photometry

        return photometry

    # `computed_field` makes it a property and includes it in schema/dumps
    @computed_field
    def survey(self) -> str:
        return "ZTF"

    @property
    def drb(self) -> float | None:
        """Return the reliability (DRB) score of the candidate, if available."""
        return self.candidate.drb

    def plot_cutouts(
        self,
        orientation: str = "horizontal",
        axes: "list[Axes] | None" = None,
        show: bool = True,
        figsize: tuple[float, float] | None = None,
        title: str | None = None,
    ) -> "list[Axes]":
        """Display the science, template, and difference cutouts for this alert.

        Parameters
        ----------
        orientation : str, default='horizontal'
            Layout orientation: 'horizontal' or 'vertical'. (overwritten if axes is not None)
        axes : list of matplotlib.axes.Axes, optional
            List of 3 axes to plot on. If None, creates new figure.
        show : bool, default=True
            Whether to call plt.show() after plotting.
        figsize : tuple, optional
            Figure size. If None, uses defaults based on orientation.
        title : str, optional
            Overall figure title. If None, uses objectId.

        Returns
        -------
        list of matplotlib.axes.Axes
            List of the three axes objects (science, template, difference).
        """
        if (
            self.cutoutScience is None
            or self.cutoutTemplate is None
            or self.cutoutDifference is None
        ):
            self.get_cutouts()
        return plot_cutouts(
            self,
            cast(str, self.survey),
            False,
            axes,
            show,
            orientation,
            figsize,
            title or self.objectId,
        )

    def show_cutouts(
        self,
        orientation: str = "horizontal",
    ) -> None:
        """Display the cutouts in a new matplotlib figure.

        Parameters
        ----------
        orientation : str, default='horizontal'
            Layout orientation: 'horizontal' or 'vertical'.
        """
        self.plot_cutouts(orientation=orientation, show=True)

    def get_cutouts(self) -> AlertCutouts:
        """Fetch cutouts for this alert from the API.

        Returns
        -------
        AlertCutouts
            Cutout images (science, template, difference) as bytes.
        """
        if (
            self.cutoutScience is not None
            and self.cutoutTemplate is not None
            and self.cutoutDifference is not None
        ):
            return AlertCutouts(
                candid=self.candid,
                cutoutScience=self.cutoutScience,
                cutoutTemplate=self.cutoutTemplate,
                cutoutDifference=self.cutoutDifference,
            )
        from .api import get_cutouts as get_cutouts_from_api

        cutouts = get_cutouts_from_api("ZTF", self.candid)
        self.cutoutScience = cutouts.cutoutScience
        self.cutoutTemplate = cutouts.cutoutTemplate
        self.cutoutDifference = cutouts.cutoutDifference
        return cutouts

    def get_cross_matches(self) -> CrossMatches | None:
        """Fetch cross-matches for this alert from the API.

        Returns
        -------
        CrossMatches | None
            Cross-matches with other surveys, if available.
        """
        if self.cross_matches is not None:
            return self.cross_matches
        from .api import get_cross_matches as get_cross_matches_from_api

        self.cross_matches = get_cross_matches_from_api("ZTF", self.objectId)
        return self.cross_matches

    def plot_lightcurve(
        self, ax: "Axes | None" = None, show: bool = True
    ) -> None:
        """Plot the lightcurve for this alert.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axis to plot on. If None, creates new figure.
        show : bool, default=True
            Whether to call plt.show() after plotting.
        """
        if (
            self.prv_candidates is None
            and self.fp_hists is None
            and self.prv_nondetections is None
        ):
            from .api import get_photometry as get_photometry_from_api

            photometry_data = get_photometry_from_api("ZTF", self.objectId)
            self.prv_candidates = photometry_data.prv_candidates
            self.fp_hists = photometry_data.fp_hists
            self.prv_nondetections = photometry_data.prv_nondetections
        plot_lightcurve(self, ax=ax, show=show)

    def plot_cross_matches(
        self, ax: "Axes | None" = None, show: bool = True
    ) -> None:
        # here we just want to show a table of the cross-matches, so we can use `ax.table` for that
        cross_matches = self.get_cross_matches()
        if cross_matches is None:
            print("No cross-match information available.")
            return
        # we convert the cross-matches to a list of dicts, and then to a pandas DataFrame, so we can display it as a table
        import pandas as pd

        rows = []
        for match in cross_matches.ned or []:
            rows.append(
                {
                    "catalog": "NED",
                    "objtype": match.objtype,
                    "ra": match.ra,
                    "dec": match.dec,
                    "z": match.z,
                    "distance_arcsec": match.distance_arcsec,
                }
            )
        # skip the others for now
        if not rows:
            print("No cross-match information available.")
            return
        df = pd.DataFrame(rows)
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, len(df) * 0.5 + 1))
        ax.axis("off")
        table = ax.table(
            cellText=df.values.tolist(),
            colLabels=df.columns.tolist(),
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.auto_set_column_width(col=list(range(len(df.columns))))
        if show:
            plt.show()

    def show_lightcurve(self) -> None:
        """Display the lightcurve in a new matplotlib figure."""
        self.plot_lightcurve(show=True)

    def show(
        self,
        orientation: str = "horizontal",
        include_cross_matches: bool = False,
    ) -> None:
        """Display both cutouts and lightcurve for this alert."""
        if not include_cross_matches:
            if orientation == "horizontal":
                fig = plt.figure(figsize=(12, 6))
                gs = fig.add_gridspec(
                    3, 2, width_ratios=[1, 2], height_ratios=[1, 1, 1]
                )
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[1, 0])
                ax3 = fig.add_subplot(gs[2, 0])
                ax4 = fig.add_subplot(gs[:, 1])
            else:
                fig = plt.figure(figsize=(10, 10))
                gs = fig.add_gridspec(
                    2, 3, width_ratios=[1, 1, 1], height_ratios=[1, 2]
                )
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax3 = fig.add_subplot(gs[0, 2])
                ax4 = fig.add_subplot(gs[1, :])
            self.plot_cutouts(
                orientation=orientation, axes=[ax1, ax2, ax3], show=False
            )
            self.plot_lightcurve(ax=ax4, show=False)
        else:
            # in both orientations, the crossmatches should be on their own row,
            # under the cutouts and lightcurve, so we can just use a 2x3 grid
            # and span the crossmatch plot across all 3 columns
            if orientation == "horizontal":
                fig = plt.figure(figsize=(16, 10))
                gs = fig.add_gridspec(
                    3, 3, width_ratios=[1, 2, 1], height_ratios=[1, 2, 1]
                )
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[1, 0])
                ax3 = fig.add_subplot(gs[2, 0])
                ax4 = fig.add_subplot(gs[0:2, 1])
                fig.add_subplot(gs[2, :])
            else:
                fig = plt.figure(figsize=(12, 12))
                gs = fig.add_gridspec(
                    3, 3, width_ratios=[1, 1, 1], height_ratios=[1, 2, 1]
                )
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax3 = fig.add_subplot(gs[0, 2])
                ax4 = fig.add_subplot(gs[1, :])
                fig.add_subplot(gs[2, :])
            self.plot_cutouts(
                orientation=orientation, axes=[ax1, ax2, ax3], show=False
            )
            self.plot_lightcurve(ax=ax4, show=False)
            # Display cross-match info
            self.get_cross_matches()
        plt.suptitle(f"{self.objectId}", fontsize=16, fontweight="bold")
        plt.tight_layout()
        plt.show()


# Add datetime property to ZtfCandidate for convenience
# Note: Mypy doesn't support dynamic property assignment, so we ignore this
ZtfCandidate.datetime = property(  # type: ignore[attr-defined]
    lambda self: Time(self.jd, format="jd").to_datetime(timezone=timezone.utc)
)


class LsstAlert(EnrichedLsstAlert):
    """Pydantic model for a Babamul LSST alert."""

    topic: str | None = None
    cross_matches: CrossMatches | None = None

    def get_photometry(self, deduplicated: bool = True) -> list[Photometry]:
        """Combine and return all photometry data from the alert."""
        if self.prv_candidates is None and self.fp_hists is None:
            from .api import get_photometry as get_photometry_from_api

            photometry_data = get_photometry_from_api("LSST", self.objectId)
            self.prv_candidates = photometry_data.prv_candidates
            self.fp_hists = photometry_data.fp_hists
        photometry: list[Photometry] = []
        # Add prv_candidates photometry
        if self.prv_candidates:
            photometry.extend(self.prv_candidates)
        # Add fp_hists photometry if available
        if self.fp_hists:
            photometry.extend(self.fp_hists)

        # Sort photometry by Julian Date (jd)
        photometry.sort(key=lambda x: x.jd)

        # if deduplicated, remove duplicates based on (jd, band)
        if deduplicated:
            seen = set()
            deduped_photometry = []
            for p in photometry:
                key = (p.jd, p.band)
                if key not in seen:
                    seen.add(key)
                    deduped_photometry.append(p)
            photometry = deduped_photometry

        return photometry

    # `computed_field` makes it a property and includes it in schema/dumps
    @computed_field
    def survey(self) -> str:
        return "LSST"

    @property
    def drb(self) -> float | None:
        """Return the reliability (DRB) score of the candidate, if available."""
        return self.candidate.reliability

    def plot_cutouts(
        self,
        orientation: str = "horizontal",
        use_rotation: bool = True,
        axes: "list[Axes] | None" = None,
        show: bool = True,
        figsize: tuple[float, float] | None = None,
        title: str | None = None,
    ) -> "list[Axes]":
        """Display the science, template, and difference cutouts for this alert.

        Parameters
        ----------
        orientation : str, default='horizontal'
            Layout orientation: 'horizontal' or 'vertical'. (overwritten if axes is not None)
        use_rotation : bool, default=True
            Whether to apply rotation based on FITS header (if available).
        axes : list of matplotlib.axes.Axes, optional
            List of 3 axes to plot on. If None, creates new figure.
        show : bool, default=True
            Whether to call plt.show() after plotting.
        figsize : tuple, optional
            Figure size. If None, uses defaults based on orientation.
        title : str, optional
            Overall figure title. If None, uses objectId.

        Returns
        -------
        list of matplotlib.axes.Axes
            List of the three axes objects (science, template, difference).
        """
        if (
            self.cutoutScience is None
            or self.cutoutTemplate is None
            or self.cutoutDifference is None
        ):
            self.get_cutouts()
        return plot_cutouts(
            self,
            cast(str, self.survey),
            use_rotation,
            axes,
            show,
            orientation,
            figsize,
            title or self.objectId,
        )

    def show_cutouts(
        self,
        orientation: str = "horizontal",
        use_rotation: bool = True,
    ) -> None:
        """Display the cutouts in a new matplotlib figure.

        Parameters
        ----------
        orientation : str, default='horizontal'
            Layout orientation: 'horizontal' or 'vertical'.
        use_rotation : bool, default=True
            Whether to apply rotation based on FITS header (if available).
        """
        self.plot_cutouts(
            use_rotation=use_rotation, orientation=orientation, show=True
        )

    def get_cutouts(self) -> AlertCutouts:
        """Fetch cutouts for this alert from the API.

        Returns
        -------
        AlertCutouts
            Cutout images (science, template, difference) as bytes.
        """
        if (
            self.cutoutScience is not None
            and self.cutoutTemplate is not None
            and self.cutoutDifference is not None
        ):
            return AlertCutouts(
                candid=self.candid,
                cutoutScience=self.cutoutScience,
                cutoutTemplate=self.cutoutTemplate,
                cutoutDifference=self.cutoutDifference,
            )
        from .api import get_cutouts as get_cutouts_from_api

        cutouts = get_cutouts_from_api("LSST", self.candid)
        self.cutoutScience = cutouts.cutoutScience
        self.cutoutTemplate = cutouts.cutoutTemplate
        self.cutoutDifference = cutouts.cutoutDifference
        return cutouts

    def get_cross_matches(self) -> CrossMatches | None:
        """Fetch cross-matches for this alert from the API.

        Returns
        -------
        CrossMatches | None
            Cross-matches with other surveys, if available.
        """
        if self.cross_matches is not None:
            return self.cross_matches

        from .api import get_cross_matches as get_cross_matches_from_api

        self.cross_matches = get_cross_matches_from_api("LSST", self.objectId)
        return self.cross_matches

    def plot_lightcurve(
        self, ax: "Axes | None" = None, show: bool = True
    ) -> None:
        """Plot the lightcurve for this alert.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axis to plot on. If None, creates new figure.
        show : bool, default=True
            Whether to call plt.show() after plotting.
        """
        if self.prv_candidates is None and self.fp_hists is None:
            from .api import get_photometry as get_photometry_from_api

            photometry_data = get_photometry_from_api("LSST", self.objectId)
            self.prv_candidates = photometry_data.prv_candidates
            self.fp_hists = photometry_data.fp_hists
        plot_lightcurve(self, ax=ax, show=show)

    def show_lightcurve(self) -> None:
        """Display the lightcurve in a new matplotlib figure."""
        self.plot_lightcurve(show=True)

    def show(
        self,
        orientation: str = "horizontal",
        include_cross_matches: bool = False,
    ) -> None:
        """Display both cutouts and lightcurve for this alert."""
        if not include_cross_matches:
            if orientation == "horizontal":
                fig = plt.figure(figsize=(12, 6))
                gs = fig.add_gridspec(
                    3, 2, width_ratios=[1, 2], height_ratios=[1, 1, 1]
                )
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[1, 0])
                ax3 = fig.add_subplot(gs[2, 0])
                ax4 = fig.add_subplot(gs[:, 1])
            else:
                fig = plt.figure(figsize=(10, 10))
                gs = fig.add_gridspec(
                    2, 3, width_ratios=[1, 1, 1], height_ratios=[1, 2]
                )
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax3 = fig.add_subplot(gs[0, 2])
                ax4 = fig.add_subplot(gs[1, :])
            self.plot_cutouts(
                orientation=orientation, axes=[ax1, ax2, ax3], show=False
            )
            self.plot_lightcurve(ax=ax4, show=False)
        else:
            # in both orientations, the crossmatches should be on their own row,
            # under the cutouts and lightcurve, so we can just use a 2x3 grid
            # and span the crossmatch plot across all 3 columns
            if orientation == "horizontal":
                fig = plt.figure(figsize=(16, 10))
                gs = fig.add_gridspec(
                    3, 3, width_ratios=[1, 2, 1], height_ratios=[1, 2, 1]
                )
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[1, 0])
                ax3 = fig.add_subplot(gs[2, 0])
                ax4 = fig.add_subplot(gs[0:2, 1])
                fig.add_subplot(gs[2, :])
            else:
                fig = plt.figure(figsize=(12, 12))
                gs = fig.add_gridspec(
                    3, 3, width_ratios=[1, 1, 1], height_ratios=[1, 2, 1]
                )
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax3 = fig.add_subplot(gs[0, 2])
                ax4 = fig.add_subplot(gs[1, :])
                fig.add_subplot(gs[2, :])
            self.plot_cutouts(
                orientation=orientation, axes=[ax1, ax2, ax3], show=False
            )
            self.plot_lightcurve(ax=ax4, show=False)
            # Display cross-match info
            self.get_cross_matches()
        plt.suptitle(f"{self.objectId}", fontsize=16, fontweight="bold")
        plt.tight_layout()
        plt.show()


# Add datetime property to LsstCandidate for convenience
# Note: Mypy doesn't support dynamic property assignment, so we ignore this
LsstCandidate.datetime = property(  # type: ignore[attr-defined]
    lambda self: Time(self.jd, format="jd").to_datetime(timezone=timezone.utc)
)


def add_cross_matches(
    alerts: list[ZtfAlert | LsstAlert], n_threads: int = 1
) -> None:
    """Helper function to add cross-matches to a list of alerts."""
    from .api import get_cross_matches_bulk

    # group and fetch cross-matches in bulk for efficiency, per survey
    ztf_object_ids = [
        a.objectId
        for a in alerts
        if isinstance(a, ZtfAlert) and a.cross_matches is None
    ]
    ztf_cross_matches = get_cross_matches_bulk(
        "ZTF", ztf_object_ids, n_threads=n_threads
    )

    lsst_object_ids = [
        a.objectId
        for a in alerts
        if isinstance(a, LsstAlert) and a.cross_matches is None
    ]
    lsst_cross_matches = get_cross_matches_bulk(
        "LSST", lsst_object_ids, n_threads=n_threads
    )

    # assign cross-matches back to alerts
    for alert in alerts:
        if isinstance(alert, ZtfAlert):
            alert.cross_matches = ztf_cross_matches.get(alert.objectId)
        elif isinstance(alert, LsstAlert):
            alert.cross_matches = lsst_cross_matches.get(alert.objectId)


# # --- LSST API models ---


class ZtfApiAlert(BaseModel):
    candid: int
    objectId: str
    candidate: ZtfCandidate
    properties: ZtfAlertProperties
    classifications: dict[str, float] | None = None

    def fetch_full_object(self) -> ZtfAlert:
        """Fetch the full ZTF object from the API.

        Returns
        -------
        ZtfAlert
            Full object with all available data.
        """
        from .api import get_object

        return cast(ZtfAlert, get_object("ZTF", self.objectId))

    def fetch_cutouts(self) -> AlertCutouts:
        """Fetch cutouts for this alert from the API.

        Returns
        -------
        AlertCutouts
            Cutout images (science, template, difference) as bytes.
        """
        from .api import get_cutouts

        return get_cutouts("ZTF", self.candid)


# --- LSST API models ---


class LsstApiAlert(BaseModel):
    candid: int
    objectId: str
    candidate: LsstCandidate
    properties: LsstAlertProperties
    classifications: dict[str, float] | None = None

    def fetch_full_object(self) -> LsstAlert:
        """Fetch the full LSST object from the API.

        Returns
        -------
        LsstAlert
            Full object with all available data.
        """
        from .api import get_object

        return cast(LsstAlert, get_object("LSST", self.objectId))

    def fetch_cutouts(self) -> AlertCutouts:
        """Fetch cutouts for this alert from the API.

        Returns
        -------
        AlertCutouts
            Cutout images (science, template, difference) as bytes.
        """
        from .api import get_cutouts

        return get_cutouts("LSST", self.candid)

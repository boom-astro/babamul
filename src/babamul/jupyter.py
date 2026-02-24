"""Functionality for working with Babamul in Jupyter notebooks."""

from typing import Any

from IPython.display import display
from ipywidgets import widgets

from babamul.models import LsstAlert, ZtfAlert


def scan_alerts(
    alerts: list[ZtfAlert | LsstAlert],
    include_survey_matches: bool = True,
    include_nondetections: bool = True,
) -> None:
    # Create buttons and output area
    prev_button = widgets.Button(description="← Previous")
    next_button = widgets.Button(description="Next →")
    survey_matches_toggle = widgets.Checkbox(
        value=include_survey_matches,
        description="Show survey matches",
        indent=False,
    )
    nondetections_toggle = widgets.Checkbox(
        value=include_nondetections,
        description="Show non-detections",
        indent=False,
    )
    info_label = widgets.HTML()
    output = widgets.Output()

    # State
    current_idx = [0]

    def update_display() -> None:
        if len(alerts) == 0:
            info_label.value = "No alerts found"
            return
        idx = current_idx[0]
        alert: ZtfAlert | LsstAlert = alerts[idx]
        obs_date = alert.candidate.jd
        info_label.value = (
            f"<b>Alert {idx + 1} of {len(alerts)}</b>"
            f" (observed {obs_date} by {alert.survey})"
        )
        with output:
            output.clear_output(wait=True)
            try:
                alert.show(
                    include_survey_matches=survey_matches_toggle.value,
                    include_nondetections=nondetections_toggle.value,
                )  # This will display the cutouts and metadata
            except Exception as e:
                print(f"Error displaying alert: {e}")
            # let's also show a clickable link to the alert on the Babamul web interface
            alert_url = f"https://babamul.caltech.edu/objects/{alert.survey}/{alert.objectId}"
            print(f"View on Babamul: {alert_url}")

    def on_prev(b: Any) -> None:
        if current_idx[0] > 0:
            current_idx[0] -= 1
            update_display()

    def on_next(b: Any) -> None:
        if current_idx[0] < len(alerts) - 1:
            current_idx[0] += 1
            update_display()

    def on_toggle_change(change: Any) -> None:
        if change["name"] == "value":
            update_display()

    prev_button.on_click(on_prev)
    next_button.on_click(on_next)
    survey_matches_toggle.observe(on_toggle_change)
    nondetections_toggle.observe(on_toggle_change)
    # Layout
    buttons = widgets.HBox(
        [prev_button, next_button, survey_matches_toggle, nondetections_toggle]
    )
    container = widgets.VBox([info_label, buttons, output])
    display(container)  # type: ignore[no-untyped-call]
    update_display()

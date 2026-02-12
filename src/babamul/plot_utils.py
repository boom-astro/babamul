

from babamul.models import ZtfAlert, LsstAlert
from ipywidgets import widgets
from IPython.display import display

import matplotlib.pyplot as plt
def scan_alerts(alerts: list[ZtfAlert | LsstAlert], include_cross_matches: bool = False):
    # Create buttons and output area
    prev_button = widgets.Button(description="← Previous")
    next_button = widgets.Button(description="Next →")
    info_label = widgets.HTML()
    output = widgets.Output()

    # State
    current_idx = [0]

    def update_display():
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
                alert.show(include_cross_matches=include_cross_matches)  # This will display the cutouts and metadata
            except Exception as e:
                print(f"Error displaying alert: {e}")
            # let's also show a clickable link to the alert on the Babamul web interface
            alert_url = f"https://babamul.caltech.edu/objects/{alert.survey}/{alert.objectId}"
            print(f"View on Babamul: {alert_url}")


    def on_prev(b):
        if current_idx[0] > 0:
            current_idx[0] -= 1
            update_display()


    def on_next(b):
        if current_idx[0] < len(alerts) - 1:
            current_idx[0] += 1
            update_display()


    prev_button.on_click(on_prev)
    next_button.on_click(on_next)
    # Layout
    buttons = widgets.HBox([prev_button, next_button])
    container = widgets.VBox([info_label, buttons, output])
    display(container)
    update_display()

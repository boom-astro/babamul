#!/usr/bin/env python3
"""Basic usage example for babamul."""

from babamul import AlertConsumer, LsstCandidate, ZtfCandidate


def main() -> None:
    """Consume and display alerts from Babamul."""
    print("Waiting for alerts...")

    try:
        with AlertConsumer(
            topics=[
                "babamul.ztf.lsst-match.hosted",
                "babamul.lsst.ztf-match.hosted",
            ],
            offset="earliest",
            timeout=30.0,
        ) as consumer:
            for i, alert in enumerate(consumer):
                # Whether its a candidate from ZTF or LSST, we can access
                # common properties.
                candidate: ZtfCandidate | LsstCandidate = alert.candidate
                # Basic info
                print(f"\nAlert #{i + 1}")
                print(f"  Object ID: {alert.objectId}")
                print(
                    "  Position: "
                    f"RA={candidate.ra:.6f}, Dec={candidate.dec:.6f}"
                )
                print(f"  Time: {candidate.datetime.isoformat()}")
                print(
                    "  Magnitude: "
                    f"{candidate.magpsf:.2f}±{candidate.sigmapsf:.2f}"
                )

                # Light curve summary
                print("  Photometry points: " f"{len(alert.get_photometry())}")

                # Real bogus / reliability score if available
                print("  Real/Bogus or Reliability score: " f"{alert.drb:.2f}")

                # We can conveniently access the survey name
                print(f"  Survey: {alert.survey}")

                # Display the cutouts
                alert.show_cutouts()

                # Stop after 5 alerts for demo
                if i >= 4:
                    print("\n(Stopping after 5 alerts)")
                    break

    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    main()

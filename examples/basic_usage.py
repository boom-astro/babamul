#!/usr/bin/env python3
"""Basic usage example for babamul.

This example demonstrates how to consume alerts from Babamul Kafka streams.

Before running, set your credentials:
    export BABAMUL_KAFKA_USERNAME="your_username"
    export BABAMUL_KAFKA_PASSWORD="your_password"

Or pass them directly to AlertConsumer.
"""

from babamul import AlertConsumer, LsstCandidate, ZtfCandidate


def main() -> None:
    """Consume and display alerts from Babamul."""
    # Create consumer (credentials from environment or pass directly)
    consumer = AlertConsumer(
        # username="your_username",  # Or set BABAMUL_KAFKA_USERNAME env var
        # password="your_password",  # Or set BABAMUL_KAFKA_PASSWORD env var
        # server=BACKUP_KAFKA_SERVERS,  # Optional, defaults to MAIN_KAFKA_SERVER
        topics=[
            "babamul.ztf.lsst-match.hosted",
            "babamul.lsst.ztf-match.hosted",
        ],  # Example topic
        offset="earliest",  # Start from the earliest available message
        timeout=30.0,  # Wait up to 30 seconds for each message
    )

    print("Waiting for alerts...")

    try:
        for i, alert in enumerate(consumer):
            # whether its a candidate from ZTF or LSST, we can access common properties
            candidate: ZtfCandidate | LsstCandidate = alert.candidate
            # Basic info
            print(f"\nAlert #{i + 1}")
            print(f"  Object ID: {alert.objectId}")
            print(
                f"  Position: RA={candidate.ra:.6f}, Dec={candidate.dec:.6f}"
            )
            print(f"  Time: {candidate.datetime.isoformat()}")
            print(
                f"  Magnitude: {candidate.magpsf:.2f}±{candidate.sigmapsf:.2f}"
            )

            # Light curve summary
            print(f"  Photometry points: {len(alert.get_photometry())}")

            # Real bogus / reliability score if available
            print(f"  Real/Bogus or Reliability score: {alert.drb:.2f}")

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
    finally:
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()

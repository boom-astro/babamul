# babamul

Python client for consuming ZTF/LSST astronomical transient alerts from Babamul Kafka streams.

## Installation

```bash
pip install babamul
```

## Quick Start

```python
from babamul import AlertConsumer

# Iterate over alerts
for alert in AlertConsumer(username="your_username", password="your_password", topics=["babamul.ztf.lsst-match.hosted"]):
    print(f"{alert.objectId}: RA={alert.candidate.ra:.4f}, Dec={alert.candidate.dec:.4f}")
    break
```

## Configuration

### Via Constructor

```python
from babamul import AlertConsumer

consumer = AlertConsumer(
    username="your_username",
    password="your_password",
    topics=["babamul.ztf.lsst-match.hosted"],  # Topic(s) to subscribe to
    offset="earliest",                     # "latest" or "earliest"
    timeout=30.0,                        # Seconds to wait for messages (None = forever)
    group_id="my-consumer-group",        # Optional, auto-generated if not set
)
```

### Via Environment Variables

```bash
export BABAMUL_KAFKA_USERNAME="your_username"
export BABAMUL_KAFKA_PASSWORD="your_password"
export BABAMUL_SERVER="kaboom.caltech.edu:9093"  # Optional, defaults to kaboom.caltech.edu:9093
```

Then in Python:

```python
from babamul import AlertConsumer

# Credentials loaded from environment
for alert in AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]):
    print(f"{alert.objectId}: RA={alert.candidate.ra:.4f}, Dec={alert.candidate.dec:.4f}")
```

## Working with Alerts

### Alert Properties

```python
from babamul import AlertConsumer

consumer = AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"])
for alert in consumer:
    # Basic info
    print(f"  Object ID: {alert.objectId}")
    print(f"  Candidate ID: {alert.candid}")
    print(f"  Position: RA={alert.candidate.ra:.6f}, Dec={alert.candidate.dec:.6f}")
    print(f"  Time: {alert.candidate.datetime.isoformat()} (JD={alert.candidate.jd:.5f})")
    print(f"  Magnitude: {alert.candidate.magpsf:.2f}±{alert.candidate.sigmapsf:.2f}")
```

### Photometry / Light Curves

```python
from babamul import AlertConsumer

consumer = AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"])
for alert in consumer:
    for phot in alert.get_photometry(): # Full light curve
        if phot.magpsf is not None:
            print(f"  JD {phot.jd:.5f}: {phot.magpsf:.2f} mag ({phot.band})")
        else:
            print(f"  JD {phot.jd:.5f}: non-detection, limit={phot.diffmaglim:.2f} ({phot.band})")
```

### Cutouts

```python
from babamul import AlertConsumer

consumer = AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"])
for alert in consumer:
    alert.show_cutouts()  # Displays science, template, and difference images
```

## Context Manager

For proper resource cleanup:

```python
from babamul import AlertConsumer

with AlertConsumer(username="user", password="pass", topics=["babamul.ztf.lsst-match.hosted"]) as consumer:
    for i, alert in enumerate(consumer):
        # process alerts
        if i >= 100:
            break
# Consumer is automatically closed
```

## Error Handling

```python
from babamul import AlertConsumer, AuthenticationError, BabamulConnectionError

consumer = None
try:
    consumer = AlertConsumer(username="user", password="pass", topics=["babamul.ztf.lsst-match.hosted"])
    for alert in consumer:
        # process alerts
        pass
except AuthenticationError:
    print("Invalid credentials")
except BabamulConnectionError:
    print("Cannot connect to Kafka server")
finally:
    if consumer:
        consumer.close()
```

## Available Topics

Babamul provides several topic categories based on survey and classification:

### LSST Topics

**LSST-only** (no ZTF counterpart):

| Topic                                       | Description                  |
|---------------------------------------------|------------------------------|
| `babamul.lsst.no-ztf-match.stellar`         | Alerts classified as stellar |
| `babamul.lsst.no-ztf-match.hosted`          | Alerts with a host galaxy    |
| `babamul.lsst.no-ztf-match.hostless`        | Alerts without a host galaxy |
| `babamul.lsst.no-ztf-match.unknown`         | Unclassified alerts          |

**LSST with ZTF match**:

| Topic                             | Description                  |
|-----------------------------------|------------------------------|
| `babamul.lsst.ztf-match.stellar`  | Alerts classified as stellar |
| `babamul.lsst.ztf-match.hosted`   | Alerts with a host galaxy    |
| `babamul.lsst.ztf-match.hostless` | Alerts without a host galaxy |
| `babamul.lsst.ztf-match.unknown`  | Unclassified alerts          |

### ZTF Topics

**ZTF-only** (no LSST counterpart):

| Topic                               | Description                  |
|-------------------------------------|------------------------------|
| `babamul.ztf.no-lsst-match.stellar` | Alerts classified as stellar |
| `babamul.ztf.no-lsst-match.hosted`  | Alerts with a host galaxy    |
| `babamul.ztf.no-lsst-match.hostless`| Alerts without a host galaxy |
| `babamul.ztf.no-lsst-match.unknown` | Unclassified alerts          |

**ZTF with LSST match**:

| Topic                            | Description                  |
|----------------------------------|------------------------------|
| `babamul.ztf.lsst-match.stellar` | Alerts classified as stellar |
| `babamul.ztf.lsst-match.hosted`  | Alerts with a host galaxy    |
| `babamul.ztf.lsst-match.hostless`| Alerts without a host galaxy |
| `babamul.ztf.lsst-match.unknown` | Unclassified alerts          |

### Wildcard Subscriptions

You can use wildcards to subscribe to multiple topics:

```python
from babamul import AlertConsumer
# All LSST topics
consumer = AlertConsumer(topics=["babamul.lsst.*"], ...)

# All ZTF topics with LSST matches
consumer = AlertConsumer(topics=["babamul.ztf.lsst-match.*"], ...)

# All hosted alerts from both surveys
consumer = AlertConsumer(topics=["babamul.*.*.hosted"], ...)
```

## Requirements

- Python >= 3.10
- confluent-kafka >= 2.3.0
- fastavro >= 1.9.0
- pydantic >= 2.0.0

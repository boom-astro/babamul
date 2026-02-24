# babamul

[![PyPI](https://img.shields.io/pypi/v/babamul)](https://pypi.org/project/babamul/)

Python client for consuming ZTF/LSST astronomical transient alerts from Babamul Kafka streams.

## Installation

```bash
uv add babamul
```

or

```bash
pip install babamul
```

## Quick Start

Set your credentials via environment variables or a local `.env`, then start
consuming alerts:

```bash
export BABAMUL_KAFKA_USERNAME="your_username"
export BABAMUL_KAFKA_PASSWORD="your_password"
export BABAMUL_API_TOKEN="your_api_token"
```

```python
from babamul import AlertConsumer

# Iterate over alerts (credentials loaded from env vars or .env)
with AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]) as consumer:
    for alert in consumer:
        print(
            f"{alert.objectId}: RA={alert.candidate.ra:.4f}, "
            f"Dec={alert.candidate.dec:.4f}"
        )
        break
```

## Configuration

Avoid hardcoding credentials in code. Prefer environment variables or a local
`.env` file that is not committed to version control. Passing
`username`/`password` in code should be limited to one-off REPL usage.

### Environmental Variables

```bash
export BABAMUL_KAFKA_USERNAME="your_username"
export BABAMUL_KAFKA_PASSWORD="your_password"
export BABAMUL_API_TOKEN="your_api_token"
export BABAMUL_KAFKA_SERVER="kaboom.caltech.edu:9093"  # Optional
```

or define these in a `.env` file kept out of version control and read
with the `python-dotenv` package.

### Constructor Options

Use the constructor for runtime options like offsets and timeouts.

```python
from babamul import AlertConsumer

with AlertConsumer(
    topics=["babamul.ztf.lsst-match.hosted"],  # Topic(s) to subscribe to
    offset="earliest",  # "latest" or "earliest"
    timeout=30.0,  # Seconds to wait for messages (None = forever)
    group_id="my-consumer-group",  # Optional, auto-generated if not set
) as consumer:
    # Consume alerts here
    for alert in consumer:
        print(
            f"{alert.objectId}: RA={alert.candidate.ra:.4f}, "
            f"Dec={alert.candidate.dec:.4f}"
        )
```

## Working with Alerts

### Alert Properties

```python
from babamul import AlertConsumer

with AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]) as consumer:
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

with AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]) as consumer:
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

with AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]) as consumer:
    for alert in consumer:
        alert.show_cutouts()  # Displays science, template, and difference images
```

## Context Manager

For proper resource cleanup:

```python
from babamul import AlertConsumer

with AlertConsumer(topics=["babamul.ztf.lsst-match.hosted"]) as consumer:
    for i, alert in enumerate(consumer):
        # process alerts
        if i >= 100:
            break
# Consumer is automatically closed
```

## Error Handling

```python
from babamul import AlertConsumer, AuthenticationError, BabamulConnectionError

try:
    with AlertConsumer(
        topics=["babamul.ztf.lsst-match.hosted"],
    ) as consumer:
        for alert in consumer:
            # process alerts
            pass
except AuthenticationError:
    print("Invalid credentials")
except BabamulConnectionError:
    print("Cannot connect to Kafka server")
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
with AlertConsumer(topics=["babamul.lsst.*"], ...) as consumer:
    pass

# All ZTF topics with LSST matches
with AlertConsumer(topics=["babamul.ztf.lsst-match.*"], ...) as consumer:
    pass

# All hosted alerts from both surveys
with AlertConsumer(topics=["babamul.*.*.hosted"], ...) as consumer:
    pass
```

## Development Setup

For development and testing, use a `.env` file to manage your credentials:

```bash
# 1. Copy the example file
cp tests/.env.example tests/.env

# 2. Edit tests/.env with your credentials
#    Get credentials at: https://babamul.caltech.edu/signup
nano tests/.env

# 3. Load automatically when running tests
# The .env file is gitignored and will not be committed
```

Your `tests/.env` file should look like:

```bash
BABAMUL_KAFKA_USERNAME=your_username
BABAMUL_KAFKA_PASSWORD=your_password
BABAMUL_API_TOKEN=your_api_token
```

Most examples and tests will automatically load credentials from `.env` using `python-dotenv`.

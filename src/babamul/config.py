"""Configuration management for Babamul alerts."""

import os

from dataclasses import dataclass

MAIN_KAFKA_SERVER = "kaboom.caltech.edu:9093" # Default BABAMUL Kafka server in Caltech
BACKUP_KAFKA_SERVERS = "babamul.umn.edu:9093" # Backup BABAMUL Kafka server in the University of Minnesota


@dataclass
class BabamulConfig:
    """Configuration for connecting to Babamul Kafka streams."""

    username: str
    password: str
    server: str = MAIN_KAFKA_SERVER
    group_id: str | None = None
    offset: str = "latest"
    timeout: float | None = None

    @classmethod
    def from_env(
        cls,
        username: str | None = None,
        password: str | None = None,
        server: str | None = None,
        group_id: str | None = None,
        offset: str = "latest",
        timeout: float | None = None,
    ) -> "BabamulConfig":
        """Create configuration from environment variables.

        Environment variables:
            BABAMUL_KAFKA_USERNAME: Kafka username
            BABAMUL_KAFKA_PASSWORD: Kafka password
            BABAMUL_SERVER: Kafka server address

        Args:
            username: Override for BABAMUL_KAFKA_USERNAME
            password: Override for BABAMUL_KAFKA_PASSWORD
            server: Override for BABAMUL_SERVER
            group_id: Consumer group ID
            offset: Starting offset ("latest" or "earliest")
            timeout: Poll timeout in seconds

        Returns:
            BabamulConfig instance
        """
        final_username = username or os.environ.get("BABAMUL_KAFKA_USERNAME")
        final_password = password or os.environ.get("BABAMUL_KAFKA_PASSWORD")
        final_server = server or os.environ.get("BABAMUL_SERVER", MAIN_KAFKA_SERVER)
        if not final_username:
            raise ValueError(
                "Username is required. Provide it directly or set BABAMUL_KAFKA_USERNAME environment variable."
            )
        if not final_password:
            raise ValueError(
                "Password is required. Provide it directly or set BABAMUL_KAFKA_PASSWORD environment variable."
            )

        return cls(
            username=final_username,
            password=final_password,
            server=final_server,
            group_id=group_id,
            offset=offset,
            timeout=timeout,
        )

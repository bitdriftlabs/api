#!/usr/bin/env python
from datetime import datetime

import click
from bdapi import Bitdrift, MetricPlatform
from bdapi.client import APIError, UnauthorizedError


@click.command()
@click.option("--api-key", required=True, help="Your bitdrift API key")
@click.option("--metric-id", required=True, help="The metric ID to ingest")
@click.option(
    "--platform",
    type=click.Choice(["APPLE", "ANDROID", "ELECTRON"], case_sensitive=False),
    required=True,
    help="The client platform",
)
@click.option("--app-id", required=True, help="App ID (e.g. com.example.app)")
@click.option("--app-version", required=True, help="App version (e.g. 1.0.0)")
@click.option("--delta", type=int, default=1, show_default=True, help="Counter delta value")
@click.option(
    "--timestamp",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S"]),
    default=None,
    help="Optional ISO timestamp (e.g. 2025-04-04T15:30:00)",
)
def main(
    api_key: str,
    metric_id: str,
    platform: str,
    app_id: str,
    app_version: str,
    delta: int,
    timestamp: datetime | None,
):
    """Ingest a metric using the Bitdrift API."""
    client = Bitdrift(api_key=api_key, base_url="https://api.bitdrift.dev")
    try:
        client.ingest_metric(
            metric_id=metric_id,
            platform=MetricPlatform[platform.upper()],
            app_id=app_id,
            app_version=app_version,
            timestamp=timestamp,
            counter_delta=delta,
        )
        click.secho("✅ Metric ingested successfully!", fg="green")
    except UnauthorizedError as e:
        click.secho("🔑 Unauthorized: Invalid API key", fg="red")
        raise SystemExit(1)

    except APIError as e:
        click.secho(f"❌ API Error: {e.message}", fg="red")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

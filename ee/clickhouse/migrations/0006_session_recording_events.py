from infi.clickhouse_orm import migrations

from ee.clickhouse.sql.session_recording_events import (
    DISTRIBUTED_SESSION_RECORDING_EVENTS_TABLE_SQL,
    KAFKA_SESSION_RECORDING_EVENTS_TABLE_SQL,
    SESSION_RECORDING_EVENTS_MATERIALIZED_COLUMN_COMMENTS_SQL,
    SESSION_RECORDING_EVENTS_TABLE_MV_SQL,
    SESSION_RECORDING_EVENTS_TABLE_SQL,
    WRITABLE_SESSION_RECORDING_EVENTS_TABLE_SQL,
)
from posthog.settings.data_stores import CLICKHOUSE_REPLICATION

operations = [
    migrations.RunSQL(SESSION_RECORDING_EVENTS_TABLE_SQL()),
    migrations.RunSQL(SESSION_RECORDING_EVENTS_MATERIALIZED_COLUMN_COMMENTS_SQL()),
    migrations.RunSQL(KAFKA_SESSION_RECORDING_EVENTS_TABLE_SQL()),
    migrations.RunSQL(SESSION_RECORDING_EVENTS_TABLE_MV_SQL()),
]

if CLICKHOUSE_REPLICATION:
    operations.extend(
        [
            migrations.RunSQL(WRITABLE_SESSION_RECORDING_EVENTS_TABLE_SQL()),
            migrations.RunSQL(DISTRIBUTED_SESSION_RECORDING_EVENTS_TABLE_SQL()),
        ]
    )

from datetime import datetime
from typing import Any, Callable, List, Optional, Tuple

from posthog.constants import AnalyticsDBMS
from posthog.settings import ASYNC_MIGRATIONS_DEFAULT_TIMEOUT_SECONDS
from posthog.version_requirement import ServiceVersionRequirement


# used to prevent circular imports
class AsyncMigrationType:
    id: int
    name: str
    description: str
    progress: int
    status: int
    current_operation_index: int
    current_query_id: str
    celery_task_id: str
    started_at: datetime
    finished_at: datetime
    posthog_min_version: str
    posthog_max_version: str


class AsyncMigrationOperation:
    def __init__(
        self,
        fn: Callable[[str], None],
        rollback_fn: Callable[[str], None] = lambda _: None,
        debug_context: Optional[Any] = None,
    ):
        self.fn = fn

        # This should not be a long operation as it will be executed synchronously!
        # Defaults to a no-op ("") - None causes a failure to rollback
        self.rollback_fn = rollback_fn

        self.debug_context = debug_context

    @classmethod
    def simple_op(
        cls,
        sql,
        rollback=None,
        database: AnalyticsDBMS = AnalyticsDBMS.CLICKHOUSE,
        timeout_seconds: int = ASYNC_MIGRATIONS_DEFAULT_TIMEOUT_SECONDS,
    ):
        return cls(
            fn=cls.get_db_op(database=database, sql=sql, timeout_seconds=timeout_seconds),
            rollback_fn=cls.get_db_op(database=database, sql=rollback) if rollback else lambda _: None,
            debug_context={"sql": sql, "rollback": rollback, "database": database},
        )

    @classmethod
    def get_db_op(
        cls,
        sql: str,
        database: AnalyticsDBMS = AnalyticsDBMS.CLICKHOUSE,
        timeout_seconds: int = ASYNC_MIGRATIONS_DEFAULT_TIMEOUT_SECONDS,
    ):
        from posthog.async_migrations.utils import execute_op_clickhouse, execute_op_postgres

        # timeout is currently CH only
        def run_db_op(query_id):
            if database == AnalyticsDBMS.CLICKHOUSE:
                execute_op_clickhouse(sql, query_id, timeout_seconds)
            else:
                execute_op_postgres(sql, query_id)

        return run_db_op


class AsyncMigrationDefinition:

    # the migration cannot be run before this version
    posthog_min_version = "0.0.0"

    # the migration _must_ be run before this version
    posthog_max_version = "10000.0.0"

    # use this to add information about why this migration is needed to self-hosted users
    description = ""

    # list of versions accepted for the services the migration relies on e.g. ClickHouse, Postgres
    service_version_requirements: List[ServiceVersionRequirement] = []

    # list of operations the migration will perform _in order_
    operations: List[AsyncMigrationOperation] = []

    # name of async migration this migration depends on
    depends_on: Optional[str] = None

    # will be run before starting the migration, return a boolean specifying if the instance needs this migration
    # e.g. instances with CLICKHOUSE_REPLICATION is True might need different migrations
    def is_required(self) -> bool:
        return True

    # run before starting the migration
    def precheck(self) -> Tuple[bool, Optional[str]]:
        return (True, None)

    # run at a regular interval while the migration is being executed
    def healthcheck(self) -> Tuple[bool, Optional[str]]:
        return (True, None)

    # return an int between 0-100 to specify how far along this migration is
    def progress(self, migration_instance: AsyncMigrationType) -> int:
        return int(100 * migration_instance.current_operation_index / len(self.operations))

import os
from urllib.parse import urlparse

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from posthog.constants import AnalyticsDBMS
from posthog.settings.base_variables import DEBUG, IS_COLLECT_STATIC, TEST
from posthog.settings.utils import get_from_env, str_to_bool

# See https://docs.djangoproject.com/en/3.1/ref/settings/#std:setting-DATABASE-DISABLE_SERVER_SIDE_CURSORS
DISABLE_SERVER_SIDE_CURSORS = get_from_env("USING_PGBOUNCER", False, type_cast=str_to_bool)

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

if TEST or DEBUG:
    PG_HOST = os.getenv("PGHOST", "localhost")
    PG_USER = os.getenv("PGUSER", "posthog")
    PG_PASSWORD = os.getenv("PGPASSWORD", "posthog")
    PG_PORT = os.getenv("PGPORT", "5432")
    DATABASE_URL = os.getenv("DATABASE_URL", f"postgres://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/posthog")
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    DATABASES = {"default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}
    if DISABLE_SERVER_SIDE_CURSORS:
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
elif os.getenv("POSTHOG_DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": get_from_env("POSTHOG_DB_NAME"),
            "USER": os.getenv("POSTHOG_DB_USER", "postgres"),
            "PASSWORD": os.getenv("POSTHOG_DB_PASSWORD", ""),
            "HOST": os.getenv("POSTHOG_POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTHOG_POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 0,
            "DISABLE_SERVER_SIDE_CURSORS": DISABLE_SERVER_SIDE_CURSORS,
            "SSL_OPTIONS": {
                "sslmode": os.getenv("POSTHOG_POSTGRES_SSL_MODE", None),
                "sslrootcert": os.getenv("POSTHOG_POSTGRES_CLI_SSL_CA", None),
                "sslcert": os.getenv("POSTHOG_POSTGRES_CLI_SSL_CRT", None),
                "sslkey": os.getenv("POSTHOG_POSTGRES_CLI_SSL_KEY", None),
            },
        }
    }

    ssl_configurations = []
    for ssl_option, value in DATABASES["default"]["SSL_OPTIONS"].items():
        if value:
            ssl_configurations.append("{}={}".format(ssl_option, value))

    if ssl_configurations:
        ssl_configuration = "?{}".format("&".join(ssl_configurations))
    else:
        ssl_configuration = ""

    DATABASE_URL = "postgres://{}{}{}{}:{}/{}{}".format(
        DATABASES["default"]["USER"],
        ":" + DATABASES["default"]["PASSWORD"] if DATABASES["default"]["PASSWORD"] else "",
        "@" if DATABASES["default"]["USER"] or DATABASES["default"]["PASSWORD"] else "",
        DATABASES["default"]["HOST"],
        DATABASES["default"]["PORT"],
        DATABASES["default"]["NAME"],
        ssl_configuration,
    )
else:
    raise ImproperlyConfigured(
        f'The environment vars "DATABASE_URL" or "POSTHOG_DB_NAME" are absolutely required to run this software'
    )

# Clickhouse Settings
CLICKHOUSE_TEST_DB = "posthog_test"

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_DATABASE = CLICKHOUSE_TEST_DB if TEST else os.getenv("CLICKHOUSE_DATABASE", "default")
CLICKHOUSE_CLUSTER = os.getenv("CLICKHOUSE_CLUSTER", "posthog")
CLICKHOUSE_CA = os.getenv("CLICKHOUSE_CA", None)
CLICKHOUSE_SECURE = get_from_env("CLICKHOUSE_SECURE", not TEST and not DEBUG, type_cast=str_to_bool)
CLICKHOUSE_VERIFY = get_from_env("CLICKHOUSE_VERIFY", True, type_cast=str_to_bool)
CLICKHOUSE_REPLICATION = get_from_env("CLICKHOUSE_REPLICATION", False, type_cast=str_to_bool)
CLICKHOUSE_ENABLE_STORAGE_POLICY = get_from_env("CLICKHOUSE_ENABLE_STORAGE_POLICY", False, type_cast=str_to_bool)
CLICKHOUSE_ASYNC = get_from_env("CLICKHOUSE_ASYNC", False, type_cast=str_to_bool)

CLICKHOUSE_CONN_POOL_MIN = get_from_env("CLICKHOUSE_CONN_POOL_MIN", 20, type_cast=int)
CLICKHOUSE_CONN_POOL_MAX = get_from_env("CLICKHOUSE_CONN_POOL_MAX", 1000, type_cast=int)

CLICKHOUSE_STABLE_HOST = get_from_env("CLICKHOUSE_STABLE_HOST", CLICKHOUSE_HOST)

_clickhouse_http_protocol = "http://"
_clickhouse_http_port = "8123"
if CLICKHOUSE_SECURE:
    _clickhouse_http_protocol = "https://"
    _clickhouse_http_port = "8443"

CLICKHOUSE_HTTP_URL = f"{_clickhouse_http_protocol}{CLICKHOUSE_HOST}:{_clickhouse_http_port}/"

# Kafka configs
KAFKA_URL = os.getenv("KAFKA_URL", "kafka://kafka")
KAFKA_HOSTS_LIST = [urlparse(host).netloc for host in KAFKA_URL.split(",")]
KAFKA_HOSTS = ",".join(KAFKA_HOSTS_LIST)
KAFKA_BASE64_KEYS = get_from_env("KAFKA_BASE64_KEYS", False, type_cast=str_to_bool)

_primary_db = os.getenv("PRIMARY_DB", "postgres")
PRIMARY_DB: AnalyticsDBMS
try:
    PRIMARY_DB = AnalyticsDBMS(_primary_db)
except ValueError:
    PRIMARY_DB = AnalyticsDBMS.POSTGRES

# The last case happens when someone upgrades Heroku but doesn't have Redis installed yet. Collectstatic gets called before we can provision Redis.
if TEST or DEBUG or IS_COLLECT_STATIC:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost/")
else:
    REDIS_URL = os.getenv("REDIS_URL", "")

if not REDIS_URL and get_from_env("POSTHOG_REDIS_HOST", ""):
    REDIS_URL = "redis://:{}@{}:{}/".format(
        os.getenv("POSTHOG_REDIS_PASSWORD", ""),
        os.getenv("POSTHOG_REDIS_HOST", ""),
        os.getenv("POSTHOG_REDIS_PORT", "6379"),
    )

if not REDIS_URL:
    raise ImproperlyConfigured(
        "Env var REDIS_URL or POSTHOG_REDIS_HOST is absolutely required to run this software.\n"
        "If upgrading from PostHog 1.0.10 or earlier, see here: "
        "https://posthog.com/docs/deployment/upgrading-posthog#upgrading-from-before-1011"
    )

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "posthog",
    }
}

if TEST:
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
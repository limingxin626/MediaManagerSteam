from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import models metadata
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 支持多个数据库，通过环境变量 DB_NAME 控制
import os
DB_NAME = os.getenv("DB_NAME", "default")

# 根据 DB_NAME 选择数据库 URL
if DB_NAME == "default":
    config.set_main_option("sqlalchemy.url", "sqlite:///./db_new.sqlite3")
    # 使用默认的版本目录
    config.set_main_option("version_locations", "%(here)s/versions")
elif DB_NAME == "notes2":
    config.set_main_option("sqlalchemy.url", "sqlite:///./db_notes2.sqlite3")
    # 使用专门的版本目录
    config.set_main_option("version_locations", "%(here)s/versions_notes2")
else:
    config.set_main_option("sqlalchemy.url", f"sqlite:///./db_{DB_NAME}.sqlite3")
    # 使用默认的版本目录
    config.set_main_option("version_locations", "%(here)s/versions")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

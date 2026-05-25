from logging.config import fileConfig

from sqlalchemy import create_engine
from alembic import context

from src.core.config import settings
from src.infrastructure.database.database import Base

from src.infrastructure.database.models import (
    user_models,
    category_models,
    comment_models,
    location_models,
    post_models,
)

config = context.config

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = create_engine(settings.DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()

else:
    run_migrations_online()
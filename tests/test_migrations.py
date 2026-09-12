from datetime import datetime, timezone
from uuid import uuid4

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import MetaData, Table, create_engine, select

from app.core.config import settings
from app.db.base import Base


def test_migration_preserves_patients_and_matches_models(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setattr(settings, "database_url", url)
    config = Config("alembic.ini")
    command.upgrade(config, "001_create_patients")
    engine = create_engine(url)
    patients = Table("patients", MetaData(), autoload_with=engine)
    with engine.begin() as connection:
        connection.execute(patients.insert().values(
            id=uuid4().hex, email="existing@example.com", password_hash="existing-hash",
            first_name="Existing", last_name="Patient", created_at=datetime.now(timezone.utc),
        ))
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.scalar(select(patients.c.email)) == "existing@example.com"
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    command.downgrade(config, "001_create_patients")
    with engine.connect() as connection:
        assert connection.scalar(select(patients.c.email)) == "existing@example.com"
    command.upgrade(config, "head")
    engine.dispose()

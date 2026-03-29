import pytest
from config import Settings, get_settings


def test_settings_default_values():
    """Test that settings have expected defaults"""
    settings = Settings()
    assert settings.neo4j_uri == "bolt://localhost:7687"
    assert settings.neo4j_user == "neo4j"
    assert settings.postgres_port == 5432


def test_postgres_dsn():
    """Test PostgreSQL DSN construction"""
    settings = Settings(
        postgres_host="testhost",
        postgres_port=5432,
        postgres_db="testdb",
        postgres_user="testuser",
        postgres_password="testpass"
    )
    assert settings.postgres_dsn == "postgresql://testuser:testpass@testhost:5432/testdb"


def test_get_settings_cached():
    """Test that get_settings is cached"""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2

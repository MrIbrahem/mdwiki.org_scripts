from __future__ import annotations

from datetime import datetime

from flask_app.main_app.extensions import db
from sqlalchemy import Column, DateTime, Integer, String


class MockModel(db.Model):
    __tablename__ = "mock_model"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    created_at = Column(DateTime)


def test_base_model_to_dict(app):
    with app.app_context():
        now = datetime(2025, 1, 1, 12, 0, 0)
        obj = MockModel(id=1, name="test", created_at=now)

        data = obj.to_dict()
        assert data["id"] == 1
        assert data["name"] == "test"
        assert data["created_at"] == "2025-01-01T12:00:00"

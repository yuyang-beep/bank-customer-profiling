"""数据访问层公共入口。"""

from pathlib import Path

from .base import DataRepository
from .csv_repository import CsvDataRepository
from .models import MetricQuery


def create_repository(project_root: str | Path) -> DataRepository:
    """创建当前的 CSV 仓储；未来可在此切换数据库适配器。"""
    return CsvDataRepository(Path(project_root) / "data")


__all__ = ["DataRepository", "MetricQuery", "create_repository"]

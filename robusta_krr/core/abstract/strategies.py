from __future__ import annotations

import abc
import datetime
from decimal import Decimal
from typing import Generic, Optional, TypeVar, get_args

import pydantic as pd

from robusta_krr.core.models.result import K8sObjectData, ResourceType
from robusta_krr.utils.display_name import add_display_name


class ResourceRecommendation(pd.BaseModel):
    request: Optional[Decimal]
    limit: Optional[Decimal]


class StrategySettings(pd.BaseModel):
    history_duration: float = pd.Field(
        24 * 7 * 2, ge=1, description="The duration of the history data to use (in hours)."
    )
    timeframe_duration: float = pd.Field(15, ge=1, description="The step for the history data (in minutes).")

    @property
    def history_timedelta(self) -> datetime.timedelta:
        return datetime.timedelta(hours=self.history_duration)

    @property
    def timeframe_timedelta(self) -> datetime.timedelta:
        return datetime.timedelta(minutes=self.timeframe_duration)


_StrategySettings = TypeVar("_StrategySettings", bound=StrategySettings)
ResourceHistoryData = dict[str, list[Decimal]]
HistoryData = dict[ResourceType, ResourceHistoryData]
RunResult = dict[ResourceType, ResourceRecommendation]

Self = TypeVar("Self", bound="BaseStrategy")


@add_display_name(postfix="Strategy")
class BaseStrategy(abc.ABC, Generic[_StrategySettings]):
    __display_name__: str

    settings: _StrategySettings

    def __init__(self, settings: _StrategySettings):
        self.settings = settings

    def __str__(self) -> str:
        return self.__display_name__.title()

    @abc.abstractmethod
    def run(self, history_data: HistoryData, object_data: K8sObjectData) -> RunResult:
        """Run the strategy to calculate the recommendation"""

    @classmethod
    def find(cls: type[Self], name: str) -> type[Self]:
        """Get a strategy from its name."""

        strategies = cls.get_all()
        if name.lower() in strategies:
            return strategies[name.lower()]

        raise ValueError(f"Unknown strategy name: {name}. Available strategies: {', '.join(strategies)}")

    @classmethod
    def get_all(cls: type[Self]) -> dict[str, type[Self]]:
        # NOTE: Load default formatters
        from robusta_krr import strategies as _  # noqa: F401

        return {sub_cls.__display_name__.lower(): sub_cls for sub_cls in cls.__subclasses__()}

    @classmethod
    def get_settings_type(cls) -> type[StrategySettings]:
        return get_args(cls.__orig_bases__[0])[0]  # type: ignore


AnyStrategy = BaseStrategy[StrategySettings]

__all__ = [
    "AnyStrategy",
    "BaseStrategy",
    "StrategySettings",
    "HistoryData",
    "K8sObjectData",
    "ResourceType",
]

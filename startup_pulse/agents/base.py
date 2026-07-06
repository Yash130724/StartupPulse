import abc
from datetime import datetime

from startup_pulse.core import storage


class BaseAgent(abc.ABC):
    """Base class for all collection agents."""

    @abc.abstractmethod
    def get_agent_name(self) -> str:
        """Return the agent identifier (e.g. 'news', 'papers')."""

    @abc.abstractmethod
    def collect(self) -> int:
        """Run a collection pass. Returns count of new items added."""

    def get_data_dir(self) -> str:
        return storage.agent_data_dir(self.get_agent_name())

    def save_items(self, items: list[dict], date: datetime | None = None):
        storage.save_articles(self.get_agent_name(), items, date)

    def load_items(self, date: datetime | None = None) -> list[dict]:
        return storage.load_articles(self.get_agent_name(), date)

    def add_items(self, new_items: list[dict], date: datetime | None = None) -> int:
        return storage.add_articles(self.get_agent_name(), new_items, date)

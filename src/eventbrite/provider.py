from pathlib import Path
from .client import Eventbrite
from .index import AttendeesIndex
from pybrd.auth.provider import BaseAuthenticationProvider
from loguru import logger


class EventbriteAuthenticationProvider(BaseAuthenticationProvider):
    def __init__(
        self, event_id: str, token: str, index_path: Path, cache_enabled: bool
    ):
        self.index = AttendeesIndex(index_path, cache_enabled)
        self.client = Eventbrite(event_id, token)

    async def refresh(self):
        last_update = self.index.updated_at
        try:
            new_attendees = await self.client.list_attendees(last_update)
        except Exception:
            logger.exception("Error while loading attendees from EventBrite")
            return

        if new_attendees:
            for attendee in new_attendees:
                self.index.add(attendee)
            logger.info(f"Attendees index updated. attendees={len(new_attendees)}")

    async def authenticate(self, email: str) -> bool:
        return self.index.search(email) is not None

    async def stats(self):
        return {
            "attendees": len(self.index._index),
            "updated_at": self.index.updated_at,
        }

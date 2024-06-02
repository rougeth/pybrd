import asyncio
from base64 import b64encode
from datetime import datetime
import json
from typing import Optional

from httpx import AsyncClient, ReadTimeout
from loguru import logger

from .data import Attendee


DEFAULT_RETRIES = 3
API_CALLS_LIMIT = asyncio.Semaphore(5)


class EventBriteAPIException(Exception):
    pass


class Eventbrite:
    BASE_URL = "https://www.eventbriteapi.com/v3"

    def __init__(self, event_id: str, token: str):
        self.event_id = event_id
        self.token = token
        self.client = AsyncClient()

    async def _request(self, url: str, params: dict, retries: int = DEFAULT_RETRIES):
        async with API_CALLS_LIMIT:
            try:
                response = await self.client.get(url, params=params, timeout=10)
            except ReadTimeout:
                if retries > 1:
                    seconds_to_wait = (DEFAULT_RETRIES - retries + 1) * 2
                    await asyncio.sleep(seconds_to_wait)
                    return await self._request(url, params, retries - 1)
                else:
                    raise
            try:
                response.raise_for_status()
            except:
                raise EventBriteAPIException(
                    f"Error when calling EventBrite API. content={response.text!r}, url={url}, status_code={response.status_code}"
                )

            return response.json()

    async def _list_attendees(self, params: dict) -> dict:
        url = f"{self.BASE_URL}/events/{self.event_id}/attendees/"

        response = await self._request(url, params)
        logger.debug(
            "List attendees request. attendees={attendees}, page_number={page_number}, page_count={page_count}, has_more_items={has_more_items}".format(
                attendees=len(response["attendees"]),
                page_number=response["pagination"]["page_number"],
                page_count=response["pagination"]["page_count"],
                has_more_items=response["pagination"]["has_more_items"],
            )
        )
        return response

    def _list_attendees_params(
        self, page: Optional[int] = None, changed_since: Optional[datetime] = None
    ) -> dict:
        params = {
            "token": self.token,
            "status": "attending",
        }
        if page:
            next_page = json.dumps({"page": page})
            next_page = b64encode(next_page.encode("utf-8")).decode("utf-8")
            params["continuation"] = next_page

        if changed_since:
            params["changed_since"] = changed_since.strftime("%Y-%m-%dT%H:%M:%SZ")

        return params

    def _prepare_list_attendees_all_pages(self, first_page: int, last_page: int):
        tasks = []
        for page_number in range(first_page, last_page + 1):
            params = self._list_attendees_params(page=page_number)
            tasks.append(self._list_attendees(params))

        return tasks

    async def _list_all_attendees(
        self, next_page: int, last_page: int
    ) -> list[Attendee]:
        tasks = self._prepare_list_attendees_all_pages(next_page, last_page)

        logger.debug(
            f"Tasks created for remaining pages of attendees list. tasks={len(tasks)}"
        )
        results = await asyncio.gather(*tasks)
        return [attendees for result in results for attendees in result["attendees"]]

    async def list_attendees(
        self, changed_since: Optional[datetime] = None
    ) -> list[Attendee]:
        params = self._list_attendees_params(changed_since=changed_since)
        response = await self._list_attendees(params)
        attendees = response.get("attendees", [])

        if response["pagination"]["has_more_items"]:
            next_page = response["pagination"]["page_number"] + 1
            last_page = response["pagination"]["page_count"]
            attendees.extend(await self._list_all_attendees(next_page, last_page))
        return [Attendee.from_eventbrite(attendee) for attendee in attendees]

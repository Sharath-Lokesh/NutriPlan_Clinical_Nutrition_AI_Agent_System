import asyncio
import httpx


# Timeout strategy:
# - search: lightweight, fast (15s)
# - get_food: single fetch, moderate (20s)
# - get_foods: bulk fetch, can be slow with 5+ ingredients (45s)
# - list_foods: lightweight (15s)
DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
BULK_TIMEOUT = httpx.Timeout(connect=10.0, read=45.0, write=10.0, pool=10.0)

# Retry strategy: one retry on transient failures (timeouts, 5xx).
# Most USDA timeouts clear on retry within seconds.
RETRY_ATTEMPTS = 2  # initial attempt + 1 retry
RETRY_BACKOFF_SECONDS = 2.0


class UsdaClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "https://api.nal.usda.gov/fdc/v1"

    def _build_url(self, path: str) -> str:
        path = path.lstrip("/")
        return f"{self.base_url}/{path}"

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> httpx.Response | None:
        """
        Execute an HTTP request with timeout and one retry on transient errors.
        Returns None for 404 (food not found). Raises for other errors.
        """
        last_exception: Exception | None = None

        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if method == "GET":
                        response = await client.get(url, params=params)
                    elif method == "POST":
                        response = await client.post(url, params=params, json=json)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                    if response.status_code == 404:
                        return None  # treat as "not found", not an error

                    # Retry on 5xx (server-side transient errors)
                    if 500 <= response.status_code < 600:
                        if attempt < RETRY_ATTEMPTS - 1:
                            await asyncio.sleep(RETRY_BACKOFF_SECONDS)
                            continue

                    response.raise_for_status()
                    return response

            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.PoolTimeout) as e:
                last_exception = e
                if attempt < RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS)
                    continue
                # final attempt failed — re-raise
                raise

            except httpx.HTTPStatusError:
                # 4xx (other than 404) — don't retry, just raise
                raise

        # Should not reach here, but defensive fallback
        if last_exception:
            raise last_exception
        return None

    async def search(
        self,
        query: str,
        page_size: int = 25,
        data_type: list[str] | None = None,
    ) -> dict | None:
        params: dict[str, str] = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": str(page_size),
        }
        if data_type:
            params["dataType"] = ",".join(data_type)
        url = self._build_url("foods/search")

        response = await self._request_with_retry("GET", url, params=params)
        return response.json() if response else None

    async def get_food(self, fdc_id: int, format: str = "abridged") -> dict | None:
        params = {"api_key": self.api_key, "format": format}
        url = self._build_url(f"food/{fdc_id}")

        response = await self._request_with_retry("GET", url, params=params)
        return response.json() if response else None

    async def get_foods(
        self,
        fdc_ids: list[int],
        format: str = "abridged",
    ) -> list[dict] | None:
        params = {"api_key": self.api_key}
        url = self._build_url("foods")
        body = {"fdcIds": fdc_ids, "format": format}

        # Bulk fetch needs longer timeout — multiple food panels in one response
        response = await self._request_with_retry(
            "POST", url, params=params, json=body, timeout=BULK_TIMEOUT
        )
        return response.json() if response else None

    async def list_foods(
        self,
        data_type: list[str] | None = None,
        page_size: int = 50,
    ) -> dict | None:
        params: dict[str, str] = {
            "api_key": self.api_key,
            "pageSize": str(page_size),
        }
        if data_type:
            params["dataType"] = ",".join(data_type)
        url = self._build_url("foods/list")

        response = await self._request_with_retry("GET", url, params=params)
        return response.json() if response else None
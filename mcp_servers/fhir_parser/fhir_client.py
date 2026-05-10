import httpx


class FhirClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _build_url(self, path: str) -> str:
        path = path.lstrip("/")
        return f"{self.base_url}/{path}"

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict | None:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        url = self._build_url(path)
        # # print(f"[FHIR_CLIENT] URL: {url}")
        # # print(f"[FHIR_CLIENT] Has token: {bool(self.token)}")
        # # print(f"[FHIR_CLIENT] Auth header: {headers.get('Authorization', 'NONE')[:60]}...")
        # # print(f"[FHIR_CLIENT] Token prefix: {self.token[:30] + '...' if self.token else 'NONE'}")
        # # print(f"[FHIR_CLIENT] Params: {params}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                # print(f"[FHIR_CLIENT] Status: {response.status_code}")
                # print(f"[FHIR_CLIENT] Response body: {response.text[:1000]}")
                # print(f"[FHIR_CLIENT] Headers: {response.headers}")
                if response.status_code == 404:
                    return None
                elif response.status_code == 403:
                    # print(f"[FHIR_CLIENT] 403 body: {response.text[:500]}")
                    return None
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError:
                raise

    async def read(self, path: str) -> dict | None:
        return await self._get(path)

    async def search(
        self,
        resource_type: str,
        search_parameters: dict[str, str] | None = None,
    ) -> dict | None:
        return await self._get(resource_type, params=search_parameters)

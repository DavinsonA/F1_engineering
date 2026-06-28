import time

import httpx

BASE_URL = "https://api.openf1.org/v1/"


class LiveSessionBlocked(Exception):
    """La API bloquea el acceso anónimo mientras hay una sesión de F1 en vivo."""


class OpenF1Client:
    def __init__(self, base_url=BASE_URL, max_per_minute=25, timeout=30.0, max_retries=3):
        self._client = httpx.Client(base_url=base_url, timeout=timeout)
        self._min_interval = 60.0 / max_per_minute
        self._max_retries = max_retries
        self._last_request = 0.0

    def _throttle(self):
        wait = self._min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def get(self, endpoint, params=None):
        for attempt in range(1, self._max_retries + 1):
            self._throttle()
            try:
                response = self._client.get(endpoint, params=params)
            except httpx.RequestError:
                if attempt == self._max_retries:
                    raise
                time.sleep(2 ** attempt)
                continue

            if response.status_code == 401:
                detail = response.json().get("detail", "401 Unauthorized")
                raise LiveSessionBlocked(detail)

            if response.status_code == 429 or response.status_code >= 500:
                if attempt == self._max_retries:
                    response.raise_for_status()
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()
            return response.json()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

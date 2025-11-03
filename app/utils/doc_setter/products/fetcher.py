import asyncio
import httpx
import random
from loguru import logger
from abc import ABC, abstractmethod

ELITE_DETAIL_BASE_URL = "https://api.zoommer.ge/v1/Products/details/"
ELITE_BULK_BASE_URL = "https://api.zoommer.ge/v1/Products/v3"


class BaseFetcher(ABC):
    def __init__(self, set_total_products_found_callback: callable = None, max_retries=2, concurrency=5, timeout=10.0):
        self.max_retries = max_retries
        self.concurrency = concurrency
        self.timeout = timeout
        self._client = None
        self._sem = None
        self.set_total_products_found_callback = set_total_products_found_callback

    async def __aenter__(self):
        self._sem = asyncio.Semaphore(self.concurrency)
        self._client = httpx.AsyncClient(timeout=self.timeout, http2=False, headers={"User-Agent": "python-httpx", "Accept-Language": "en"})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client is not None:
            await self._client.aclose()
        self._client = None
        self._sem = None

    @abstractmethod
    async def fetch_all_product_ids(self):
        pass

    @abstractmethod
    def build_product_detail_url(self, product_id):
        pass

    async def _fetch_one_product_detail(self, client, product_detail_url, sem):
        delay = 0.5
        for attempt in range(self.max_retries + 1):
            async with (self._sem or sem):
                try:
                    r = await (self._client or client).get(product_detail_url)
                    r.raise_for_status()
                    return r.json()
                except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteError, httpx.RemoteProtocolError) as e:
                    if attempt < self.max_retries:
                        await asyncio.sleep(delay + random.uniform(0, 0.5))
                        delay *= 2
                    else:
                        logger.warning(f"Failed to fetch {product_detail_url}: {e}")
                        return None
                except httpx.HTTPStatusError as e:
                    logger.warning(f"Bad status for {product_detail_url}: {e.response.status_code}")
                    return None
                except Exception as e:
                    if attempt < self.max_retries:
                        await asyncio.sleep(delay + random.uniform(0, 0.5))
                        delay *= 2
                    else:
                        logger.warning(f"Failed to fetch {product_detail_url}: {e}")
                        return None

    def build_product_detail_urls(self, product_ids: list) -> list:
        return [self.build_product_detail_url(product_id) for product_id in product_ids]

    async def _fetch_bulk_product_details(self, product_detail_urls: list[str]) -> dict:
        ans = []
        if self._client and self._sem:
            tasks = [self._fetch_one_product_detail(self._client, url, self._sem) for url in product_detail_urls]
            results = await asyncio.gather(*tasks)
            for result in results:
                if result is not None:
                    ans.append(result)
            return ans
        sem = asyncio.Semaphore(self.concurrency)
        async with httpx.AsyncClient(timeout=self.timeout, http2=False, headers={"User-Agent": "python-httpx", "Accept-Language": "en"}) as client:
            tasks = [self._fetch_one_product_detail(client, url, sem) for url in product_detail_urls]
            results = await asyncio.gather(*tasks)
            for result in results:
                if result is not None:
                    ans.append(result)
            return ans

    async def iterate_over_bulk_product_details(self, start_page: int, bulk_size: int, product_ids: None | list = None) -> dict:
        if product_ids is None:
            product_ids = await self.fetch_all_product_ids()
        if self.set_total_products_found_callback:
            await self.set_total_products_found_callback(len(product_ids))
        logger.info(f"iterating over {len(product_ids)} product ids")
        start_idx = (start_page - 1) * bulk_size
        for i in range(start_idx, len(product_ids), bulk_size):
            product_ids_batch = product_ids[i:i+bulk_size]
            product_detail_urls = self.build_product_detail_urls(product_ids_batch)
            details = await self._fetch_bulk_product_details(product_detail_urls)
            yield details


class ZoommerFetcher(BaseFetcher):
    def __init__(self, bulk_base_url: str = ELITE_BULK_BASE_URL, detail_base_url: str = ELITE_DETAIL_BASE_URL, set_total_products_found_callback: callable = None):
        super().__init__(set_total_products_found_callback=set_total_products_found_callback)
        self.bulk_base_url = bulk_base_url
        self.detail_base_url = detail_base_url

    async def fetch_all_product_ids(self) -> list[int]:
        res = []
        start_page = 1
        async with httpx.AsyncClient(timeout=self.timeout, http2=False, headers={"User-Agent": "python-httpx", "Accept-Language": "en"}) as client:
            while True:
                url = f"{self.bulk_base_url}?Limit=1000&Page={start_page}"
                r = await client.get(url)
                if r.status_code != 200:
                    break
                data = r.json()
                product_ids = [item["id"] for item in data.get("products", [])]
                if not product_ids:
                    break
                res.extend(product_ids)
                start_page += 1
        if self.set_total_products_found_callback:
            await self.set_total_products_found_callback(len(res))
        return res

    def build_product_detail_url(self, product_id):
        return f"{self.detail_base_url}?productId={product_id}"


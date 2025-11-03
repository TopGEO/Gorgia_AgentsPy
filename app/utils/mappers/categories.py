from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_xai import ChatXAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import asyncio
import aiofiles
import httpx
from httpx import Response
import json
import time

load_dotenv()

llm_semaphore = asyncio.Semaphore(70)


class CategoryCatalogue(BaseModel):
    category_name: str = Field(
        description="RAG friendly name of subcategory being analyzed."
    )
    summary: str = Field(
        description="Clear summary organized by series with id and prices in ₾."
    )


async def analyze_subcategory_products(
    products: str,
    subcategory_name: str = None,
    parent_category_name: str = None,
    timeout_seconds: int = 150,
    max_retries: int = 3,
) -> CategoryCatalogue:
    async with llm_semaphore:
        llm = ChatXAI(model="grok-4-fast-non-reasoning", temperature=0)
        structured_llm = llm.with_structured_output(CategoryCatalogue)

        system_message = """You are analyzing products from a SINGLE subcategory (e.g., all Apple iPhones, Samsung TVs, or Nike Shoes). Your goal is to identify and group distinct product models and their variants with their prices.

CRITICAL RULES:
1. **Analyze only the given subcategory** - All products are from the same category/brand
2. **Group by model** — identify unique models or generations and group all variants (sizes, colors, capacities, editions, whatever will be given).
3. **Include product IDs and prices** — CRUCIAL: ALWAYS show each product's [id:x] and price in ₾ next to its variant or detail.
4. **Show discounts clearly** — If a product has a previous price (shown as "was:X₾"), display it as "₾X (was ₾Y)" to highlight the discount.
5. **Readable summary** — produce a clear, human-friendly summary organized by model → variant → details with prices.
6. **Avoid repetition** — group similar variants together instead of listing duplicates.

FORMAT:
- Write naturally, using clear indentation or parentheses.
- Example style:
  "iPhone 17: Pro Max 256GB (Deep Blue [id:101] ₾3,299, Green [id:102] ₾3,299); Pro 512GB (Silver [id:103] ₾2,999)"
  "Samsung QLED TVs: 55" [id:201] ₾2,499, 65" [id:202] ₾3,599; Crystal UHD: 43" [id:203] ₾1,249 (was ₾1,499), 50" [id:204] ₾1,649"

Focus on what products/models are available and group them in summary"""

        user_message = f"Analyze these products from the {parent_category_name} category, subcategory: {subcategory_name}.\n\nProvide a RAG-friendly category name and identify what distinct models are available (below you see id:price:title for each product, discounted products show 'was:X₾' after the current price):\n\n{products}"

        messages = [("system", system_message), ("user", user_message)]

        for attempt in range(max_retries):
            try:
                start_time = time.perf_counter()
                print(
                    f"Started for {subcategory_name} (attempt {attempt + 1}/{max_retries})"
                )

                # Run with timeout
                result = await asyncio.wait_for(
                    structured_llm.ainvoke(messages), timeout=timeout_seconds
                )

                end_time = time.perf_counter()
                print(
                    f"✅ Finished for {subcategory_name} in {(end_time - start_time):.2f}s"
                )
                return result

            except asyncio.TimeoutError:
                print(
                    f"⏱️ TIMEOUT for {subcategory_name} after {timeout_seconds}s (attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying {subcategory_name}...")
                    await asyncio.sleep(2)  # Brief pause before retry
                else:
                    print(f"❌ FAILED for {subcategory_name} after {max_retries} attempts")
                    raise

            except Exception as e:
                print(
                    f"❌ ERROR for {subcategory_name}: {str(e)} (attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying {subcategory_name}...")
                    await asyncio.sleep(2)
                else:
                    print(f"❌ FAILED for {subcategory_name} after {max_retries} attempts")
                    raise


async def get_categories() -> Response:
    urlOfCategories = (
        "https://api.zoommer.ge/v1/Categories/all-categories"  # Get all categories
    )
    async with httpx.AsyncClient() as client:
        return await client.get(urlOfCategories)


async def get_subcategories():
    resp = await get_categories()
    childCategories = []
    if resp.status_code == 200:
        for category in resp.json():
            for childCategory in category.get(
                "childCategories", []
            ):  # Get child categories
                childCategory["parent_category_name"] = category["name"]
                childCategories.append(childCategory)
    return childCategories


async def summarize_subcategorie(
    childCategory: dict,
    client: httpx.AsyncClient,
    max_retries: int = 3,
):
    urlOfProducts = f"https://api.zoommer.ge/v1/Products/v3?CategoryId={childCategory['id']}&Limit=10000"

    for attempt in range(max_retries):
        try:
            response = await client.get(urlOfProducts)
            response.raise_for_status()
            break  # Success, exit retry loop
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                print(
                    f"⏱️ Timeout for {childCategory['name']}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(wait_time)
            else:
                print(
                    f"❌ HTTP error for {childCategory['name']} after {max_retries} attempts: {str(e)}"
                )
                return None
        except Exception as e:
            print(f"❌ HTTP error for {childCategory['name']}: {str(e)}")
            return None

    allProduct = ""
    products = response.json()["products"]

    if products:
        for product in products:
            if product["isInStock"] or True:
                price_info = f"{product['price']}₾"
                if product.get("previousPrice") and product["previousPrice"]:
                    price_info += f" (was:{product['previousPrice']}₾)"
                allProduct += (
                    f"{product['id']}:{price_info}:{product['name']}\n"
                )

    if not allProduct.strip():
        print(f"No in-stock products for {childCategory['name']}")
        return None

    try:
        result = await analyze_subcategory_products(
            allProduct, childCategory["name"], childCategory["parent_category_name"]
        )
        # Convert to dict and add parent category manually
        result_dict = result.model_dump()
        result_dict["parent_category_name"] = childCategory["parent_category_name"]
        return result_dict
    except Exception as e:
        print(f"llm analyzis failed for {childCategory['name']}:\n{str(e)}")
        return None


async def summarize_subcategories():
    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        tasks = []
        subcategories = await get_subcategories()

        for subcategory in subcategories:
            tasks.append(summarize_subcategorie(subcategory, client))

        results = [
            r
            for r in await asyncio.gather(*tasks, return_exceptions=True)
            if r and not isinstance(r, Exception)
        ]

        async with aiofiles.open("products.json", "w") as f:
            await f.write(json.dumps(results, indent=2, ensure_ascii=False))

        print(f"Finished! Processed {len(results)} categories successfully.")


if __name__ == "__main__":
    asyncio.run(summarize_subcategories())
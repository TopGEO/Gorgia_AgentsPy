from langchain.tools import tool
from pydantic import BaseModel, Field
import httpx
import logging


class CheckOrderStatusInput(BaseModel):
    order_id: str = Field(
        description="The unique identifier of the order to check. Write it verbatim as provided by the user."
    )


@tool(args_schema=CheckOrderStatusInput)
async def check_order_status(order_id: str) -> str:
    """
    Tool to check the status of an order given its order number.
    IMPORTANT: Use the EXACT order number as provided by the user. Do not modify, duplicate, or alter the number in any way.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://165.22.66.5/api/orders/{order_id}")

            if response.status_code == 404:
                logging.info(f"Order {order_id} not found (404)")
                return "ORDER_NOT_FOUND_TRANSFER_TO_OPERATOR"

            response.raise_for_status()
            data = response.json()

            order = data.get("order")
            if not order:
                logging.warning(f"Order {order_id} - No 'order' key in response")
                return "ORDER_NOT_FOUND_TRANSFER_TO_OPERATOR"

            item_collection_note = order.get("item_collection_note")
            delivery_type = order.get("delivery_type")
            delivery_status_2 = order.get("delivery_status_2")
            tracking_code = order.get("tracking_code")
            city = order.get("city")
            order_ready_status = (order.get("order_ready_status") or "").strip().lower()
            delivery_time = order.get("delivery_time")
            status_update = order.get("status_update")
            order_status_1 = order.get("order_status_1")

            order['order_date'] = (order.get('order_date') or "").replace(" 00:00:00 GMT", "")
            order['standard_deadline'] = (order.get('standard_deadline') or "").replace(" 00:00:00 GMT", "")
            standard_deadline = order['standard_deadline']

            if item_collection_note in [
                "გამონაწილებულია",
                "გასაგზავნია",
            ] and order_status_1 in ["", None, "განაწილებულია ფილიალში"] and status_update in ["", None, "გამზადებულია"]:
                return "ORDER_IN_PROCESS_TRANSFER_TO_OPERATOR"

            if status_update == "ჩაბარებული":
                return "ORDER_DELIVERED_TRANSFER_TO_OPERATOR"

            if (
            delivery_type in ["ფილიალიდან გატანა", "ადგილიდან გატანა"]
                and order_status_1 == "გამზადებულია შეკვეთა"
                and status_update == ""
            ):
                return f"ORDER_READY_FOR_PICKUP:{order_ready_status}"

            if (
                delivery_type in ["ფილიალიდან გატანა", "ადგილიდან გატანა"]
                and order_status_1 in ["განაწილებულია ფილიალში", "გამზადებულია შეკვეთა"]
                and status_update == "ჩაბარებული"
            ):
                return "ORDER_DELIVERED_TRANSFER_TO_OPERATOR"

            if (
                delivery_type in ["ფილიალიდან გატანა", "ადგილიდან გატანა"]
                and order_status_1
                in ["გამზადებულია შეკვეთა", "განაწილებულია ფილიალში"]
                and status_update == ""
            ):
                return "ORDER_CANCELLED_TRANSFER_TO_OPERATOR"

            if (
                delivery_type in ["სწრაფი მიწოდება", "სწრაფი მიწოდება ფილიალიდან"]
                and tracking_code
                and standard_deadline
                and order_status_1 == "გამზადებულია შეკვეთა"
                and status_update == ""
            ):
                return f"ORDER_FAST_DELIVERY:{standard_deadline}"

            if (
                delivery_type in ["დაგეგმილი მიწოდება", "დაგეგმილი მიწოდება ფილიალიდან"]
                and tracking_code
                and delivery_time
                and order_status_1 == "გამზადებულია შეკვეთა"
                and status_update == ""
            ):
                logging.info("ORDER_SCHEDULED_DELIVERY")
                return f"ORDER_SCHEDULED_DELIVERY:{delivery_time}"

            if (
                delivery_type == "მიწოდება"
                and tracking_code
                and standard_deadline
                and city
                and city.lower() != "თბილისი"
                and order_ready_status in ["georgian post", "tnt"]
                and order_status_1 == "გამზადებულია შეკვეთა"
                and status_update == ""
                and delivery_status_2 in ["გაგზავნილია ფოსტაში", ""]
            ):
                return f"ORDER_STANDARD_DELIVERY_REGIONS:{order_ready_status}:{standard_deadline}:{tracking_code}"

            if (
                delivery_type == "მიწოდება"
                and tracking_code
                and standard_deadline
                and city
                and city.lower() == "თბილისი"
                and order_ready_status in ["georgian post", "tnt"]
                and order_status_1 == "გამზადებულია შეკვეთა"
                and status_update == ""
                and delivery_status_2 in ["გაგზავნილია ფოსტაში", ""]
            ):
                return f"ORDER_STANDARD_DELIVERY_TBILISI:{order_ready_status}:{standard_deadline}:{tracking_code}"
            
            del order['product_name']
            del order['customer_name']
            del order['location_details']
            del order['personal_id']
            del order['phone_number']
            del order['branch']
            del order['comment_1']
            del order['source_sheet']
            del order['item_carrier']
            del order['issue_date']
            
            return str(order)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logging.info(f"Order {order_id} not found (404)")
            return "ORDER_NOT_FOUND_TRANSFER_TO_OPERATOR"
        logging.error(f"HTTP status error while checking order {order_id}: {e}")
        return "ORDER_NOT_FOUND_TRANSFER_TO_OPERATOR"
    except httpx.HTTPError as e:
        logging.error(f"HTTP error while checking order status: {e}")
        return f"Error checking order status: Unable to connect to the order system."
    except Exception as e:
        logging.error(f"Error checking order status: {e}")
        return f"Error checking order status: {str(e)}"


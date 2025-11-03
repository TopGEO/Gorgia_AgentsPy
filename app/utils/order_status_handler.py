import logging
from typing import Optional, Tuple
from langchain_core.messages import ToolMessage


class OrderStatusHandler:
    """Handles order status checking logic and response generation for operator transfers."""

    @staticmethod
    def handle_order_status_result(
        result: str, tool_call_id: str
    ) -> Tuple[Optional[str], Optional[ToolMessage], bool]:
        """
        Process order status result and determine appropriate action.

        Args:
            result: The order status result string from check_order_status tool
            tool_call_id: The ID of the tool call for message tracking

        Returns:
            Tuple of (transfer_message, tool_message, should_transfer):
                - transfer_message: Message to show when transferring to operator
                - tool_message: ToolMessage to add to conversation (if not transferring)
                - should_transfer: Whether to transfer to operator immediately
        """

        if result == "ORDER_NOT_FOUND_TRANSFER_TO_OPERATOR":
            logging.info("📦 Order not found, transferring to operator")
            return (
                "თქვენი შეკვეთის შესახებ ინფორმაციის დასაზუსტებლად გაკავშირებთ ოპერატორთან🫶",
                None,
                True
            )

        if result == "ORDER_IN_PROCESS_TRANSFER_TO_OPERATOR":
            logging.info("📦 Order in process, transferring to operator")
            return (
                "თქვენი შეკვეთა მუშავდება📦✨. დეტალური ინფორმაციისთვის გაკავშირებთ ოპერატორს 🚀",
                None,
                True
            )

        if result.startswith("ORDER_READY_FOR_PICKUP:"):
            branch = result.split(":", 1)[1] if ":" in result else ""
            logging.info(f"📦 Order ready for pickup at branch: {branch}")
            pickup_message = f"თქვენი შეკვეთა გამზადებულია {branch} ფილიალში 📦✨. შეკვეთის გასატანად თან გქონდეთ პირადობის დამადასტურებელი მოწმობა ფიზიკური ან ელექტრონული სახით 🚀"

            return (
                None,
                ToolMessage(
                    content=f"Respond with this message verbatim (do not change the wording): {pickup_message}",
                    tool_call_id=tool_call_id,
                    name="check_order_status",
                ),
                False
            )

        if result == "ORDER_DELIVERED_TRANSFER_TO_OPERATOR":
            logging.info("📦 Order delivered, transferring to operator")
            return (
                "თქვენი შეკვეთა გაცემულია 📦✅ დამატებითი ინფორმაციის დასაზუსტებლად გაკავშირებთ ოპერატორს 🫶",
                None,
                True
            )
        
        if result == "ORDER_DELIVERED":
            logging.info("📦 Order delivered")
            return (
                "თქვენი შეკვეთა ჩაბარებულია📦✨თუ დამატებით გსურთ დეტალების დაზუსტება, დაგაკავშირებთ ოპერატორს 🚀",
                None,
                True
            )

        if result == "ORDER_CANCELLED_TRANSFER_TO_OPERATOR":
            logging.info("📦 Order cancelled, transferring to operator")
            return (
                "თქვენი შეკვეთა გაუქმებულია 📦❌ დამატებითი ინფორმაციის დასაზუსტებლად გაკავშირებთ ოპერატორს 🫶",
                None,
                True
            )

        if result.startswith("ORDER_FAST_DELIVERY:"):
            standard_deadline = result.split(":", 1)[1] if ":" in result else ""
            logging.info(f"📦 Order has fast delivery with deadline: {standard_deadline}")
            fast_delivery_message = f"თქვენ გაფორმებული გაქვთ სწრაფი მიწოდება. შეკვეთას მიიღებთ {standard_deadline} დღის განმავლობაში. შეტყობინებას მიიღებთ SMS-ის სახით, მიწოდებამდე დაგიკავშირდებათ კურიერი 📦 🚀"

            return (
                None,
                ToolMessage(
                    content=f"Respond with this message verbatim (do not change the wording): {fast_delivery_message}",
                    tool_call_id=tool_call_id,
                    name="check_order_status",
                ),
                False
            )

        if result == "ORDER_SCHEDULED_NOT_READY_TRANSFER_TO_OPERATOR":
            logging.info("📦 Scheduled delivery order not ready yet, transferring to operator")
            return (
                "თქვენი შეკვეთა მუშავდება 📦✅ დამატებითი ინფორმაციის დასაზუსტებლად გაკავშირებთ ოპერატორს 🫶",
                None,
                True
            )

        if result.startswith("ORDER_SCHEDULED_DELIVERY:"):
            delivery_time = result.split(":", 1)[1] if ":" in result else ""
            logging.info(f"📦 Order has scheduled delivery with time: {delivery_time}")
            scheduled_delivery_message = f"თქვენ გაფორმებული გაქვთ დაგეგმილი მიწოდება. შეკვეთას მიიღებთ {delivery_time} თქვენს მიერ შერჩეულ ვადაში. შეტყობინებას მიიღებთ SMS-ის სახით, მიწოდებამდე დაგიკავშირდებათ კურიერი 📦 🚀"

            return (
                None,
                ToolMessage(
                    content=f"Respond with this message verbatim (do not change the wording): {scheduled_delivery_message}",
                    tool_call_id=tool_call_id,
                    name="check_order_status",
                ),
                False
            )

        if result.startswith("ORDER_STANDARD_DELIVERY_REGIONS:"):
            parts = result.split(":", 3)
            if len(parts) >= 4:
                order_ready_status = parts[1]
                standard_deadline = parts[2]
                tracking_code = parts[3]

                logging.info(f"📦 Order has standard delivery to regions via {order_ready_status}")

                if order_ready_status == "georgian post":
                    standard_delivery_message = f"თქვენ გაფორმებული გაქვთ სტანდარტული მიწოდება. შეკვეთის მიიღების ბოლო ვადა გახლავთ {standard_deadline}. მიღების ვადებზე დეტალური ინფორმაციისთვის შეგიძლიათ დაუკავშირდეთ საქართველოს ფოსტას ან თრექინგ კოდის საშუალებით გადაამოწმოთ მათ ვებ-გვერდზე: https://www.gpost.ge/. შეკვეთის თრექინგ კოდია: {tracking_code}. გაითვალისწინეთ, რომ სტანდარტული მიწოდების ვადა საქართველოს მასშტაბით 3-6 სამუშაო დღეა 📦 🚀"
                elif order_ready_status == "tnt":
                    standard_delivery_message = f"თქვენ გაფორმებული გაქვთ სტანდარტული მიწოდება. შეკვეთის მიიღების ბოლო ვადა გახლავთ {standard_deadline}. მიღების ვადებზე დეტალური ინფორმაციისთვის შეგიძლიათ დაუკავშირდეთ FedEx-სს ნომერზე 032 291 02 20. თქვენი შეკვეთის თრექინგ კოდია: {tracking_code}. გაითვალისწინეთ, რომ სტანდარტული მიწოდების ვადა საქართველოს მასშტაბით 3-6 სამუშაო დღეა 📦 🚀"
                else:
                    standard_delivery_message = f"თქვენ გაფორმებული გაქვთ სტანდარტული მიწოდება. შეკვეთის მიიღების ბოლო ვადა გახლავთ {standard_deadline}. თრექინგ კოდი: {tracking_code} 📦 🚀"

                return (
                    None,
                    ToolMessage(
                        content=f"Respond with this message verbatim (do not change the wording): {standard_delivery_message}",
                        tool_call_id=tool_call_id,
                        name="check_order_status",
                    ),
                    False
                )

        if result.startswith("ORDER_STANDARD_DELIVERY_TBILISI:"):
            parts = result.split(":", 3)
            if len(parts) >= 4:
                order_ready_status = parts[1]
                standard_deadline = parts[2]
                tracking_code = parts[3]

                logging.info(f"📦 Order has standard delivery to Tbilisi via {order_ready_status}")

                if order_ready_status == "georgian post":
                    standard_delivery_message = f"თქვენ გაფორმებული გაქვთ სტანდარტული მიწოდება. შეკვეთის მიიღების ბოლო ვადა გახლავთ {standard_deadline}. მიღების ვადებზე დეტალური ინფორმაციისთვის შეგიძლიათ დაუკავშირდეთ საქართველოს ფოსტას ან თრექინგ კოდის საშუალებით გადაამოწმოთ მათ ვებ-გვერდზე: https://www.gpost.ge/. შეკვეთის თრექინგ კოდია: {tracking_code}. გაითვალისწინეთ, რომ სტანდარტული მიწოდების ვადა თბილისში 2-5 სამუშაო დღეა 📦 🚀"
                elif order_ready_status == "tnt":
                    standard_delivery_message = f"თქვენ გაფორმებული გაქვთ სტანდარტული მიწოდება. შეკვეთის მიიღების ბოლო ვადა გახლავთ {standard_deadline}. მიღების ვადებზე დეტალური ინფორმაციისთვის შეგიძლიათ დაუკავშირდეთ FedEx-სს ნომერზე 032 291 02 20. თქვენი შეკვეთის თრექინგ კოდია: {tracking_code}. გაითვალისწინეთ, რომ სტანდარტული მიწოდების ვადა თბილისში 2-5 სამუშაო დღეა 📦 🚀"
                else:
                    standard_delivery_message = f"თქვენ გაფორმებული გაქვთ სტანდარტული მიწოდება. შეკვეთის მიიღების ბოლო ვადა გახლავთ {standard_deadline}. თრექინგ კოდი: {tracking_code} 📦 🚀"

                return (
                    None,
                    ToolMessage(
                        content=f"Respond with this message verbatim (do not change the wording): {standard_delivery_message}",
                        tool_call_id=tool_call_id,
                        name="check_order_status",
                    ),
                    False
                )

        return (
            None,
            ToolMessage(
                content=f"Order status information: {str(result)}",
                tool_call_id=tool_call_id,
                name="check_order_status",
            ),
            False
        )


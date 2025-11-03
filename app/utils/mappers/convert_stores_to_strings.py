from typing import List, Optional

try:
    from app.models.product import StoreAvailability
except ImportError:
    StoreAvailability = object  # fallback for standalone utils

def convert_stores_to_strings(stores: Optional[List[StoreAvailability]]) -> Optional[List[str]]:
    """
    Convert list of StoreAvailability objects into compact human-readable strings.
    Example output:
        ["Tbilisi - Tsereteli branch (A. Tsereteli Ave N1, +995 591 967 601, 10:00-20:00, Sun 10:00-19:00)"]
    """
    if not stores:
        return None

    formatted = []
    for store in stores:
        if not store.inStock:
            continue

        parts = []

        # Base label: city + branch
        label = f"{store.city or ''} - {store.branchName or ''}".strip(" -")

        # Optional details inside parentheses
        details = []
        if store.address:
            details.append(store.address)
        if store.phoneNumber:
            details.append(store.phoneNumber)
        if store.workingHoursMonToSat:
            details.append(store.workingHoursMonToSat)
        if store.workingHoursSun:
            details.append(f"Sun {store.workingHoursSun}")

        if details:
            label += f" ({', '.join(details)})"

        formatted.append(label)

    return formatted or None
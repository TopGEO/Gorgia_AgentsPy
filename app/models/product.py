from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, model_validator, field_validator


class Product(BaseModel):
    id: Optional[int] = None
    product_id: Optional[int] = None
    product: Optional[str] = None
    product_code: Optional[str] = None
    bar_code: Optional[str] = None
    item: Optional[str] = None
    price: Optional[Union[str, float]] = None
    product_unit: Optional[str] = None
    wholesale_price: Optional[Union[str, float]] = None
    product_meta_keywords: Optional[str] = None
    category_meta_keywords: Optional[str] = None
    category_meta_description: Optional[str] = None
    category_page_title: Optional[str] = None
    characteristics: Optional[str] = None
    branch_availability: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        extra = "allow"
        populate_by_name = True
        validate_assignment = False

    @field_validator('price', 'wholesale_price', mode='before')
    @classmethod
    def convert_price_to_string(cls, v):
        """Convert price values to strings for consistent handling"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @model_validator(mode='before')
    @classmethod
    def extract_from_metadata(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(data, dict) and 'metadata' in data:
            return data['metadata']
        return data

    @staticmethod
    def _map_characteristics_to_string(characteristics: list) -> Optional[str]:
        """
        Convert characteristics list to a pipe-separated string.

        Args:
            characteristics: List of characteristic objects with 'characteristic' and 'value' keys

        Returns:
            Formatted string like "სიგრძე: 0.8 | სიგანე: 0.032", or None if empty
        """
        if not characteristics:
            return None

        char_strings = []
        for char in characteristics:
            characteristic = char.get('characteristic', '')
            value = char.get('value', '')
            if characteristic and value:
                char_strings.append(f"{characteristic}: {value}")

        return ' | '.join(char_strings) if char_strings else None

    @staticmethod
    def _map_store_availability_to_string(branch_availability: list) -> Optional[str]:
        """
        Convert branch availability list to a formatted string.
        Filters out stores with no stock and concatenates name and address.

        Args:
            branch_availability: List of store objects with stock information

        Returns:
            Formatted string with available stores, or None if no stores have stock
        """
        if not branch_availability:
            return None

        available_stores = []
        for store in branch_availability:
            stock = store.get('stock', 0)
            if stock and stock > 0:
                name = store.get('name', '')
                address = store.get('address', '')
                available_stores.append(f"{name} - {address}")

        return '; '.join(available_stores) if available_stores else None

    @staticmethod
    def from_search_result(search_result) -> 'Product':
        """
        Create a Product instance from a vector store search result.

        Args:
            search_result: Search result object from vector_store.hybrid_search()
                          Expected to have a .payload attribute containing product data

        Returns:
            Product: A Product instance populated with data from the search result
        """
        if hasattr(search_result, 'payload'):
            payload = search_result.payload
        else:
            payload = search_result

        # Extract metadata if present
        if isinstance(payload, dict) and 'metadata' in payload:
            data = payload['metadata']
        else:
            data = payload

        # Manually assemble attributes
        attributes = {
            'id': data.get('id'),
            'product_id': data.get('product_id'),
            'product': data.get('product'),
            'product_code': data.get('product_code'),
            'bar_code': data.get('bar_code'),
            'item': data.get('item'),
            'price': data.get('price'),
            'product_unit': data.get('product_unit'),
            'wholesale_price': data.get('wholesale_price'),
            'product_meta_keywords': data.get('product_meta_keywords'),
            'category_meta_keywords': data.get('category_meta_keywords'),
            'category_meta_description': data.get('category_meta_description'),
            'category_page_title': data.get('category_page_title'),
            'image_url': data.get('image_url'),
        }

        # Handle characteristics conversion
        characteristics = data.get('characteristics')
        if isinstance(characteristics, list):
            attributes['characteristics'] = Product._map_characteristics_to_string(characteristics)
        elif isinstance(characteristics, str):
            attributes['characteristics'] = characteristics
        else:
            attributes['characteristics'] = None

        # Handle branch_availability conversion
        branch_availability = data.get('branch_availability')
        if isinstance(branch_availability, list):
            attributes['branch_availability'] = Product._map_store_availability_to_string(branch_availability)
        elif isinstance(branch_availability, str):
            attributes['branch_availability'] = branch_availability
        else:
            attributes['branch_availability'] = None

        return Product(**attributes)

    def to_dict_for_ai(self) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'productId': self.product_id,
            'product': self.product,
            'productCode': self.product_code,
            'barCode': self.bar_code,
            'price': self.price,
            'productUnit': self.product_unit,
            'wholesalePrice': self.wholesale_price,
        }

        if self.characteristics:
            result['characteristics'] = self.characteristics

        if self.branch_availability:
            result['branchAvailability'] = self.branch_availability

        return {k: v for k, v in result.items() if v is not None}

    def to_minimal_dict_for_ai(self) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'product': self.product,
            'barCode': self.bar_code,
            'price': self.price,
            'productUnit': self.product_unit,
        }

        return {k: v for k, v in result.items() if v is not None}
    
    def to_search_result_dict(self, need_location: bool = False) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'product': self.product,
            'productCode': self.product_code,
            'barCode': self.bar_code,
            'price': self.price,
            'productUnit': self.product_unit,
        }

        if self.wholesale_price:
            result['wholesalePrice'] = self.wholesale_price

        if need_location and self.branch_availability:
            result['branchAvailability'] = self.branch_availability

        return {k: v for k, v in result.items() if v is not None}
    
    def to_detailed_search_dict(self) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'product': self.product,
            'productCode': self.product_code,
            'barCode': self.bar_code,
            'price': self.price,
            'productUnit': self.product_unit,
            'wholesalePrice': self.wholesale_price,
        }

        if self.characteristics:
            result['characteristics'] = self.characteristics

        if self.branch_availability:
            result['branchAvailability'] = self.branch_availability

        return {k: v for k, v in result.items() if v is not None}
    
    def to_frontend_dict(self) -> Dict[str, Any]:
        if not self.product:
            return {}

        result = {
            'id': self.id,
            'title': self.product,
            'price': self.price,
            'imageUrl': self.image_url
        }

        return {k: v for k, v in result.items() if v is not None}

from typing import Any, Dict, Optional
from pydantic import BaseModel, model_validator


class Product(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    product_code: Optional[str] = None
    bar_code: Optional[str] = None
    price: Optional[float] = None
    product_unit: Optional[str] = None
    wholesale_price: Optional[float] = None
    characteristics: Optional[str] = None
    branch_availability: Optional[str] = None
    image_url: Optional[str] = None
    
    class Config:
        extra = "allow"
        populate_by_name = True
        validate_assignment = False

    @model_validator(mode='before')
    @classmethod
    def extract_from_metadata(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(data, dict) and 'metadata' in data:
            return data['metadata']
        return data

    def to_dict_for_ai(self) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'title': self.title,
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
            'title': self.title,
            'barCode': self.bar_code,
            'price': self.price,
            'productUnit': self.product_unit,
        }

        return {k: v for k, v in result.items() if v is not None}
    
    def to_search_result_dict(self, need_location: bool = False) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'title': self.title,
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
            'title': self.title,
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
            'title': self.title,
            'price': self.price,
            'imageUrl': self.image_url
        }
        
        return {k: v for k, v in result.items() if v is not None}

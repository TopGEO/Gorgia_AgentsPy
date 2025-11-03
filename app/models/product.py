from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator, model_validator
from app.utils.mappers.convert_stores_to_strings import convert_stores_to_strings


class StoreAvailability(BaseModel):
    id: Optional[int] = None
    branchName: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    inStock: Optional[bool] = None
    phoneNumber: Optional[str] = None
    workingHoursMonToSat: Optional[str] = None
    workingHoursSun: Optional[str] = None

    class Config:
        extra = "allow"


class ProductData(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    barCode: Optional[str] = None
    description: Optional[str] = None
    sellType: Optional[str] = None
    price: Optional[float] = None
    previousPrice: Optional[float] = None
    categoryId: Optional[int] = None
    doNotRecordStock: Optional[bool] = None
    categoryIds: Optional[List[int]] = None
    parentCategoryName: Optional[str] = None
    categoryName: Optional[str] = None
    subCategoryId: Optional[int] = None
    releaseDate: Optional[str] = None
    isInStock: Optional[bool] = None
    requestedQuantity: Optional[int] = None
    promotionQuantity: Optional[int] = None
    imageUrl: Optional[str] = None
    shopId: Optional[int] = None
    shopName: Optional[str] = None
    images: Optional[List[str]] = None
    isPurchased: Optional[bool] = None
    orderNo: Optional[int] = None
    discountPercent: Optional[float] = None
    hasDiscount: Optional[bool] = None
    discountAmount: Optional[float] = None
    discountType: Optional[str] = None
    isFavorite: Optional[bool] = None
    preSalePrice: Optional[float] = None
    onSale: Optional[bool] = None

    class Config:
        extra = "allow"
        populate_by_name = True

    @field_validator('price', 'previousPrice', 'discountAmount', 'preSalePrice', mode='before')
    @classmethod
    def parse_price(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            cleaned = v.replace(',', '').replace('₾', '').replace('€', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None


class Product(BaseModel):
    product: Optional[ProductData] = None
    availabilityInStores: Optional[List[StoreAvailability]] = None
    httpStatusCode: Optional[int] = None
    userMessage: Optional[str] = None
    developerMessage: Optional[str] = None
    success: Optional[bool] = None
    errors: Optional[List[Any]] = None
    id: Optional[int] = None
    dense_text: Optional[str] = None
    sparse_text: Optional[str] = None

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
        if not self.product:
            return {}
        
        product_data = self.product.model_dump(exclude_none=True, exclude_unset=True)
        
        result = {
            'id': product_data.get('id'),
            'name': product_data.get('name'),
            'barCode': product_data.get('barCode'),
            'price': self._format_currency(product_data.get('price')),
            'categoryName': product_data.get('categoryName'),
            'parentCategoryName': product_data.get('parentCategoryName'),
            'inStock': product_data.get('isInStock'),
        }
        
        if product_data.get('previousPrice'):
            result['previousPrice'] = self._format_currency(product_data['previousPrice'])
        
        if product_data.get('hasDiscount'):
            result['discountPercent'] = product_data.get('discountPercent')
        
        if product_data.get('description'):
            result['description'] = product_data['description']
        
        if self.availabilityInStores:
            available_stores = convert_stores_to_strings(self.availabilityInStores)
            if available_stores:
                result['availableStores'] = available_stores

        return {k: v for k, v in result.items() if v is not None}

    def to_minimal_dict_for_ai(self) -> Dict[str, Any]:
        if not self.product:
            return {}
        
        product_data = self.product.model_dump(exclude_none=True, exclude_unset=True)
        
        result = {
            'id': product_data.get('id'),
            'name': product_data.get('name'),
            'barCode': product_data.get('barCode'),
            'price': self._format_currency(product_data.get('price')),
            'categoryName': product_data.get('categoryName'),
        }
        
        if product_data.get('previousPrice'):
            result['originalPrice'] = product_data.get('previousPrice')
        
        if product_data.get('discountPercent'):
            result['discount'] = product_data.get('discountPercent')

        return {k: v for k, v in result.items() if v is not None}
    
    def to_search_result_dict(self, need_location: bool = False) -> Dict[str, Any]:
        if not self.product:
            return {}
        
        product_data = self.product.model_dump(exclude_none=True, exclude_unset=True)
        
        result = {
            'id': product_data.get('id'),
            'title': product_data.get('name'),
            'barCode': product_data.get('barCode'),
            'price': self._format_currency(product_data.get('price')),
            'categoryName': product_data.get('categoryName'),
            'imageUrl': product_data.get('imageUrl'),
            'inStock': product_data.get('isInStock'),
            'url': f"https://zoommer.ge/{product_data.get('route')}",
        }
        
        if product_data.get('previousPrice'):
            result['originalPrice'] = product_data.get('previousPrice')
        
        if product_data.get('discountPercent'):
            result['discount'] = product_data.get('discountPercent')
        
        if product_data.get('hasDiscount'):
            result['hasDiscount'] = True
        
        if need_location and self.availabilityInStores:
            result['availableStores'] = convert_stores_to_strings(self.availabilityInStores)

        return {k: v for k, v in result.items() if v is not None}
    
    def to_detailed_search_dict(self) -> Dict[str, Any]:
        if not self.product:
            return {}
        
        product_data = self.product.model_dump(exclude_none=True, exclude_unset=True)
        
        result = {
            'id': product_data.get('id'),
            'name': product_data.get('name'),
            'barCode': product_data.get('barCode'),
            'price': self._format_currency(product_data.get('price')),
            'categoryName': product_data.get('categoryName'),
            'parentCategoryName': product_data.get('parentCategoryName'),
            'inStock': product_data.get('isInStock'),
        }
        
        if product_data.get('previousPrice'):
            result['previousPrice'] = self._format_currency(product_data['previousPrice'])
        
        if product_data.get('hasDiscount'):
            result['discountPercent'] = product_data.get('discountPercent')
        
        if product_data.get('description'):
            result['description'] = product_data['description']
        
        if self.availabilityInStores:
            result['availableStores'] = convert_stores_to_strings(self.availabilityInStores)

        return {k: v for k, v in result.items() if v is not None}
    
    def to_frontend_dict(self) -> Dict[str, Any]:
        if not self.product:
            return {}
        
        product_data = self.product.model_dump(exclude_none=True, exclude_unset=True)
        
        result = {
            'id': product_data.get('id'),
            'title': product_data.get('name'),
            'price': self._format_currency(product_data.get('price')),
            'imageUrl': product_data.get('imageUrl'),
        }
        
        if product_data.get('previousPrice'):
            result['originalPrice'] = product_data.get('previousPrice')
        
        if product_data.get('discountPercent'):
            result['discount'] = product_data.get('discountPercent')

        return {k: v for k, v in result.items() if v is not None}

    @staticmethod
    def _format_currency(value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        try:
            val = float(value)
            if val != val:  # NaN check
                return None
            return f"{val:.2f} ₾"
        except Exception:
            return None


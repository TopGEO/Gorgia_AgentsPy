from abc import ABC, abstractmethod
from loguru import logger


class Mapper(ABC):
    
    @abstractmethod
    def map_fetched_detail_to_product_metadata(self, fetched_detail: dict) -> dict:
        pass
    
    @abstractmethod
    def map_metadata_to_embedding_text(self, metadata: dict) -> str:
        pass

    @abstractmethod
    def map_metadata_to_sparse_embedding_text(self, metadata: dict) -> str:
        pass

    def map_fetched_details_to_product_metadatas(self, fetched_details: list[dict]) -> list[dict]:
        return [metadata for metadata in (self.map_fetched_detail_to_product_metadata(fetched_detail) for fetched_detail in fetched_details) if metadata is not None]

    def map_metadatas_to_embedding_texts(self, metadatas: list[dict]) -> list[str]:
        return [self.map_metadata_to_embedding_text(metadata) for metadata in metadatas]

    def map_metadatas_to_sparse_embedding_texts(self, metadatas: list[dict]) -> list[str]:
        return [self.map_metadata_to_sparse_embedding_text(metadata) for metadata in metadatas]


class ZoommerMapper(Mapper):
    def map_fetched_detail_to_product_metadata(self, fetched_detail: dict) -> dict:
        mapped = {**fetched_detail}
        product = fetched_detail.get('product', {})
        mapped['id'] = product.get('id')
        if mapped['id'] is None:
            logger.warning(f"Product without ID found, skipping")
            return None
        mapped['dense_text'] = self.map_metadata_to_embedding_text(mapped)
        mapped['sparse_text'] = self.map_metadata_to_sparse_embedding_text(mapped)
        return mapped
    
    def map_metadata_to_sparse_embedding_text(self, metadata: dict) -> str:
        product_dict = metadata.get("product", {})
        text_parts = []
        text_parts.append(product_dict.get("name") or "")
        text_parts.append(product_dict.get("barCode") or "")
        
        specGroup = product_dict.get("specificationGroup", []) or []
        for spec in specGroup:
            for spec in spec.get("specifications", []):
                if 'specificationMeaning' in spec and spec.get("specificationMeaning", ""):
                    text_parts.append(spec.get("specificationMeaning"))

        mainSpecification = product_dict.get("mainSpecification", []) or []
        for spec in mainSpecification:
            if 'specificationMeaning' in spec and spec.get("specificationMeaning", ""):
                text_parts.append(spec.get("specificationMeaning"))

        keySpecification = product_dict.get("keySpecification", []) or []
        for spec in keySpecification:
            if 'specificationMeaning' in spec and spec.get("specificationMeaning", ""):
                text_parts.append(spec.get("specificationMeaning"))
        
        text_parts = [part for part in text_parts if part]
        return ",".join(text_parts)

    
    def map_metadata_to_embedding_text(self, metadata: dict) -> str:
        product_dict = metadata.get("product", {})
        product = {
            "name": product_dict.get("name", ""),
            "description": product_dict.get("description", ""),
            "sellType": product_dict.get("sellType", ""),
            "price": product_dict.get("price", ""),
            "previousPrice": product_dict.get("previousPrice", ""),
            "parentCategoryName": product_dict.get("parentCategoryName", ""),
            "categoryName": product_dict.get("categoryName", ""),
            "isInStock": product_dict.get("isInStock", False),
            "discountPercent": product_dict.get("discountPercent", ""),
            "hasDiscount": product_dict.get("hasDiscount", False),
            "discountAmount": product_dict.get("discountAmount", ""),
            "discountType": product_dict.get("discountType", ""),
            "metaTitle": product_dict.get("metaTitle", ""),
            "route": product_dict.get("route", ""),
            "availabilityInStores": self._map_availability_in_stores(metadata.get("availabilityInStores")),
            "specificationGroup": self._map_specification_group(product_dict.get("specificationGroup")),
            "mainSpecification": self._map_main_specification(product_dict.get("mainSpecification")),
            "keySpecification": self._map_key_specification(product_dict.get("keySpecification"))
        }
        text_parts = []
        not_regular_keys = ["id", "isInStock", "hasDiscount"]
        for key in product.keys():
            if key in not_regular_keys:
                continue
            text_parts.append(f"{key}: {product[key]}")
        
        if product['isInStock']:
            text_parts.append(f" In Stock ")
        else:
            text_parts.append(f" Out of Stock ")
        
        if product['hasDiscount']:
            text_parts.append(f" On Discount ")
        else:
            text_parts.append(f" Not On Discount ")
            
        return "\n".join(text_parts)


    def _map_key_specification(self, key_specification) -> str:
        if not key_specification:
            return ""
        try:
            if isinstance(key_specification, str):
                return key_specification

            if isinstance(key_specification, list):
                parts = []
                for spec in key_specification:
                    name = spec.get("specificationName")
                    meaning = spec.get("specificationMeaning")
                    if name and meaning:
                        parts.append(f"{name}: {meaning}")
                return " | ".join(parts)

            if isinstance(key_specification, dict):
                name = key_specification.get("specificationName")
                meaning = key_specification.get("specificationMeaning")
                if name and meaning:
                    return f"{name}: {meaning}"
                return ""

            return ""
        except Exception as e:
            logger.error(f"Error mapping key specification: {e}")
            return ""
    
    def _map_specification_group(self, specification_group: dict) -> str:
        if not specification_group:
            return ""
        try:
            spec_group_text_builder = []
            for specification in specification_group:
                group_name = specification["groupName"]
                specification_text_builder = []
                for specification in specification["specifications"]:
                    specification_name = specification["specificationName"]
                    specification_meaning = specification["specificationMeaning"]
                    specification_text_builder.append(f"{specification_name}: {specification_meaning}")
                specification_text = " | ".join(specification_text_builder)
                group_text = f" # {group_name} \n {specification_text}"
                spec_group_text_builder.append(group_text)
            return "\n \n ".join(spec_group_text_builder)
        except Exception as e:
            logger.error(f"Error mapping specification group: {e}")
            return ""


    def _map_main_specification(self, main_specification: list) -> str:
        if not main_specification:
            return ""
        try:
            specification_text_builder = []
            for specification in main_specification:
                specification_name = specification["specificationName"]
                specification_meaning = specification["specificationMeaning"]
                specification_text_builder.append(f"{specification_name}: {specification_meaning}")
            txt =  " | ".join(specification_text_builder)
            return f" # Main Specifications \n {txt}"
        except Exception as e:
            logger.error(f"Error mapping main specification: {e}")
            return ""


    def _map_availability_in_stores(self, availability_in_stores: list) -> str:
        if not availability_in_stores:
            return ""
        try:
            available_stores = []
            not_available_stores = []
            
            for store in availability_in_stores:
                branch_name = store.get("branchName", "")
                city = store.get("city", "")
                address = store.get("address", "")
                in_stock = store.get("inStock", False)
                
                store_info = f"branchname: {branch_name}, city: {city}, address: {address}"
                
                if in_stock:
                    available_stores.append(f"## Available In {store_info}")
                else:
                    not_available_stores.append(f"## Not available in {store_info}")
            
            result_parts = []
            if available_stores:
                result_parts.append("# Availability in stores")
                result_parts.extend(available_stores)
            
            if not_available_stores:
                if not result_parts:
                    result_parts.append("# Availability in stores")
                result_parts.extend(not_available_stores)
            
            return "\n".join(result_parts)
        except Exception as e:
            logger.error(f"Error mapping availability in stores: {e}")
            return ""


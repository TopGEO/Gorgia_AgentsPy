import logging

class ZoommerMapper:
    def _map_key_specification(self, key_specification) -> str:
        if not key_specification:
            return ""
        try:
            # If already string, return as-is
            if isinstance(key_specification, str):
                return key_specification

            # Expect list of {specificationName, specificationMeaning}
            if isinstance(key_specification, list):
                parts = []
                for spec in key_specification:
                    name = spec.get("specificationName")
                    meaning = spec.get("specificationMeaning")
                    if name and meaning:
                        parts.append(f"{name}: {meaning}")
                return " | ".join(parts)

            # Fallback for dict
            if isinstance(key_specification, dict):
                name = key_specification.get("specificationName")
                meaning = key_specification.get("specificationMeaning")
                if name and meaning:
                    return f"{name}: {meaning}"
                return ""

            return ""
        except Exception as e:
            print(f"Error mapping key specification: {e}")
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
            print(f"Error mapping specification group: {e}")
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
            print(f"Error mapping main specification: {e}")
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
            print(f"Error mapping availability in stores: {e}")
            return ""
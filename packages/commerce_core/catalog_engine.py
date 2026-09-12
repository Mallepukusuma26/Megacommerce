"""
MegaCommerce Core Catalog Engine
Domain taxonomy, variant matrix generation, attribute validation, and brand registry management.
"""

from typing import List, Dict, Any, Optional, Set
import re
import datetime
from dataclasses import dataclass, field


@dataclass
class CatalogAttributeSchema:
    attribute_name: str
    data_type: str  # STRING, NUMBER, BOOLEAN, ENUM
    is_required: bool = False
    allowed_values: List[str] = field(default_factory=list)


@dataclass
class VariantMatrixItem:
    sku: str
    title: str
    price: float
    cost_price: float
    stock_quantity: int
    attribute_combination: Dict[str, str]


class CatalogTaxonomyEngine:
    """Manages hierarchical category taxonomy and attribute schema enforcement."""

    def __init__(self):
        self.categories: Dict[str, Dict[str, Any]] = {}
        self.brands: Dict[str, Dict[str, Any]] = {}
        self.schemas: Dict[str, List[CatalogAttributeSchema]] = {}

    def register_category(self, category_id: str, name: str, slug: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        cat = {
            "id": category_id,
            "name": name,
            "slug": slug,
            "parent_id": parent_id,
            "children": [],
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        self.categories[category_id] = cat
        if parent_id and parent_id in self.categories:
            self.categories[parent_id]["children"].append(category_id)
        return cat

    def register_attribute_schema(self, category_id: str, schema_list: List[CatalogAttributeSchema]) -> None:
        self.schemas[category_id] = schema_list

    def validate_product_attributes(self, category_id: str, attributes: Dict[str, Any]) -> List[str]:
        errors = []
        schema_list = self.schemas.get(category_id, [])
        for schema in schema_list:
            val = attributes.get(schema.attribute_name)
            if schema.is_required and val is None:
                errors.append(f"Missing required attribute: '{schema.attribute_name}'")
            elif val is not None:
                if schema.allowed_values and str(val) not in schema.allowed_values:
                    errors.append(f"Attribute '{schema.attribute_name}' value '{val}' not in allowed set: {schema.allowed_values}")
        return errors


class VariantMatrixGenerator:
    """Generates Cartesian product of variant combinations for product listings."""

    @staticmethod
    def generate_matrix(
        base_sku_prefix: str,
        base_price: float,
        base_cost: float,
        attribute_options: Dict[str, List[str]]
    ) -> List[VariantMatrixItem]:
        """
        Example input:
        base_sku_prefix = "SHIRT"
        attribute_options = {"size": ["S", "M", "L"], "color": ["Red", "Blue"]}
        """
        if not attribute_options:
            return []

        attr_keys = list(attribute_options.keys())
        combinations: List[Dict[str, str]] = [{}]

        for key in attr_keys:
            vals = attribute_options[key]
            temp = []
            for combo in combinations:
                for v in vals:
                    new_c = dict(combo)
                    new_c[key] = v
                    temp.append(new_c)
            combinations = temp

        matrix = []
        for combo in combinations:
            sku_parts = [base_sku_prefix] + [str(v).upper() for v in combo.values()]
            sku = "-".join(sku_parts)
            title_parts = [str(v) for v in combo.values()]
            title = f"{base_sku_prefix} (" + ", ".join(title_parts) + ")"

            matrix.append(VariantMatrixItem(
                sku=sku,
                title=title,
                price=base_price,
                cost_price=base_cost,
                stock_quantity=0,
                attribute_combination=combo
            ))

        return matrix

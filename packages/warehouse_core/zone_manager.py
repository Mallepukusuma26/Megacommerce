"""
MegaCommerce Warehouse Core — Zone & Bin Capacity Management Engine
"""

from typing import Dict, Any, List, Optional
from shared.enums import WarehouseZone


class WarehouseZoneManager:
    """Manages warehouse zone assignments (RECEIVING, BULK, PICKING, PACKING, DISPATCH, RETURNS) and bin capacity."""

    @staticmethod
    def calculate_bin_code(zone: WarehouseZone, aisle: int, rack: int, shelf: int) -> str:
        """Generates standard warehouse bin location code (e.g. 'BULK-A02-R05-S03')."""
        z_name = zone.value if isinstance(zone, WarehouseZone) else str(zone)
        return f"{z_name}-A{aisle:02d}-R{rack:02d}-S{shelf:02d}"

    @staticmethod
    def recommend_storage_zone(item_volume_cubic_ft: float, turnover_frequency: str) -> WarehouseZone:
        """Determines optimal warehouse zone based on product dimensions and velocity."""
        if turnover_frequency.upper() == "HIGH":
            return WarehouseZone.PICKING
        elif item_volume_cubic_ft > 10.0:
            return WarehouseZone.BULK_STORAGE
        else:
            return WarehouseZone.RECEIVING

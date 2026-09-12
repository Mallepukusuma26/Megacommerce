"""
MegaCommerce Inventory & Multi-Warehouse Stock Management Service
"""

from typing import List, Optional, Dict, Any
import datetime
from sqlalchemy.orm import Session
from database.models.inventory import Warehouse, InventoryItem, StockMovement, StockReservation
from database.models.catalog import Product, ProductVariant
from database.repositories.domain_repositories import InventoryRepository, BaseRepository
from shared.enums import WarehouseZone, AuditAction
from shared.exceptions import InsufficientStockError, ResourceNotFoundError


class InventoryService:
    """Core domain service for stock allocation, reorder threshold alerts, and reservations."""

    def __init__(self, db: Session):
        self.db = db
        self.inventory_repo = InventoryRepository(db)
        self.warehouse_repo = BaseRepository(Warehouse, db)
        self.movement_repo = BaseRepository(StockMovement, db)
        self.reservation_repo = BaseRepository(StockReservation, db)

    def create_warehouse(
        self, name: str, code: str, street_address: str, city: str,
        state_province: str, postal_code: str, capacity_units: int = 100000
    ) -> Warehouse:
        """Registers a new warehouse facility."""
        warehouse = Warehouse(
            name=name,
            code=code,
            street_address=street_address,
            city=city,
            state_province=state_province,
            postal_code=postal_code,
            capacity_units=capacity_units
        )
        self.db.add(warehouse)
        self.db.commit()
        return warehouse

    def add_stock(self, warehouse_id: str, product_id: str, sku: str, quantity: int, bin_location: str = "A-1") -> InventoryItem:
        """Inbound stock movement adding available units to warehouse."""
        item = self.db.query(InventoryItem).filter(
            InventoryItem.warehouse_id == warehouse_id,
            InventoryItem.sku == sku
        ).first()

        if item:
            item.quantity_available += quantity
        else:
            item = InventoryItem(
                warehouse_id=warehouse_id,
                product_id=product_id,
                sku=sku,
                quantity_available=quantity,
                bin_location=bin_location,
                zone=WarehouseZone.BULK_STORAGE.value
            )
            self.db.add(item)

        # Update root product/variant stock_quantity
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.stock_quantity += quantity
        
        variant = self.db.query(ProductVariant).filter(ProductVariant.sku == sku).first()
        if variant:
            variant.stock_quantity += quantity

        # Log movement
        movement = StockMovement(
            sku=sku,
            to_warehouse_id=warehouse_id,
            quantity=quantity,
            movement_type="INBOUND",
            notes=f"Stock added to {bin_location}"
        )
        self.db.add(movement)
        self.db.commit()
        return item

    def reserve_stock(self, order_id: str, sku: str, quantity: int, expiry_minutes: int = 30) -> StockReservation:
        """Reserves stock across available warehouses for pending checkout."""
        items = self.db.query(InventoryItem).filter(
            InventoryItem.sku == sku,
            InventoryItem.quantity_available >= quantity
        ).all()

        if not items:
            total_avail = sum([i.quantity_available for i in self.db.query(InventoryItem).filter(InventoryItem.sku == sku).all()])
            raise InsufficientStockError(sku=sku, requested=quantity, available=total_avail)

        target_item = items[0]
        target_item.quantity_available -= quantity
        target_item.quantity_reserved += quantity

        expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiry_minutes)
        reservation = StockReservation(
            order_id=order_id,
            sku=sku,
            warehouse_id=target_item.warehouse_id,
            quantity=quantity,
            expires_at=expiry_time
        )
        self.db.add(reservation)
        self.db.commit()
        return reservation

    def release_or_fulfill_reservation(self, reservation_id: str, fulfill: bool = True) -> None:
        """Fulfills reservation into outbound shipment or releases back to available pool."""
        res = self.reservation_repo.get_by_id_or_raise(reservation_id)
        item = self.inventory_repo.get_by_sku(res.sku, res.warehouse_id)

        if item:
            item.quantity_reserved -= res.quantity
            if not fulfill:
                item.quantity_available += res.quantity

        res.is_fulfilled = fulfill
        self.db.commit()

    def get_low_stock_alerts(self) -> List[Dict[str, Any]]:
        """Scans inventory items falling below reorder threshold."""
        items = self.inventory_repo.get_low_stock_items()
        alerts = []
        for i in items:
            alerts.append({
                "inventory_id": i.id,
                "warehouse_id": i.warehouse_id,
                "sku": i.sku,
                "quantity_available": i.quantity_available,
                "reorder_threshold": i.reorder_threshold,
                "reorder_quantity": i.reorder_quantity
            })
        return alerts

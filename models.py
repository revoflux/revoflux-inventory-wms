from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class StockMovementType(str, Enum):
    INBOUND_PURCHASE = "INBOUND_PURCHASE"
    OUTBOUND_SALE = "OUTBOUND_SALE"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    CYCLE_COUNT_ADJUSTMENT = "CYCLE_COUNT_ADJUSTMENT"
    SCRAP_DAMAGE = "SCRAP_DAMAGE"

class WarehouseLocation(BaseModel):
    warehouse_id: str
    warehouse_name: str
    zone: str
    aisle: str
    shelf: str
    bin: str

class InventoryItem(BaseModel):
    sku: str
    barcode: str
    title: str
    category: str
    current_stock: int
    reserved_stock: int = 0
    reorder_point: int
    safety_stock: int
    unit_cost: float
    selling_price: float
    location: WarehouseLocation
    is_low_stock: bool = False

class StockMovementRequest(BaseModel):
    sku: str
    movement_type: StockMovementType
    quantity: int = Field(gt=0)
    source_warehouse_id: Optional[str] = None
    destination_warehouse_id: Optional[str] = None
    reference_id: str
    notes: Optional[str] = None

class StockMovementRecord(BaseModel):
    movement_id: str
    timestamp: datetime
    sku: str
    movement_type: StockMovementType
    quantity_changed: int
    balance_after: int
    reference_id: str

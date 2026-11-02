"""
RevoFlux Inventory & Warehouse Management System (WMS)
Production REST API Core
"""
from fastapi import FastAPI, HTTPException, status
from typing import Dict, List
import uuid
from datetime import datetime

from models import (
    InventoryItem,
    WarehouseLocation,
    StockMovementRequest,
    StockMovementRecord,
    StockMovementType
)

app = FastAPI(
    title="RevoFlux WMS & Inventory API",
    description="Multi-warehouse stock control, automated reorder triggers, and movement ledger.",
    version="1.0.0"
)

# In-memory storage for demonstration / standalone deployment
inventory_db: Dict[str, InventoryItem] = {}
movement_ledger: List[StockMovementRecord] = []

@app.on_event("startup")
def seed_initial_inventory():
    sample = InventoryItem(
        sku="RF-LOG-001",
        barcode="8901234567890",
        title="Industrial Heavy-Duty Pallet Wrap (500m)",
        category="Packaging & Logistics",
        current_stock=120,
        reserved_stock=15,
        reorder_point=40,
        safety_stock=20,
        unit_cost=14.50,
        selling_price=24.99,
        location=WarehouseLocation(
            warehouse_id="WH-CENTRAL-01",
            warehouse_name="Main Distribution Hub",
            zone="Zone-B",
            aisle="A-04",
            shelf="S-02",
            bin="B-12"
        ),
        is_low_stock=False
    )
    inventory_db[sample.sku] = sample

@app.get("/api/v1/inventory", response_model=List[InventoryItem])
def list_inventory():
    """Retrieve all stock items across warehouses with low-stock flags."""
    for item in inventory_db.values():
        item.is_low_stock = (item.current_stock - item.reserved_stock) <= item.reorder_point
    return list(inventory_db.values())

@app.get("/api/v1/inventory/{sku}", response_model=InventoryItem)
def get_item_by_sku(sku: str):
    """Fetch real-time stock levels for a specific SKU."""
    if sku not in inventory_db:
        raise HTTPException(status_code=404, detail=f"SKU {sku} not found")
    item = inventory_db[sku]
    item.is_low_stock = (item.current_stock - item.reserved_stock) <= item.reorder_point
    return item

@app.post("/api/v1/movements", response_model=StockMovementRecord, status_code=status.HTTP_201_CREATED)
def record_stock_movement(req: StockMovementRequest):
    """Execute stock movements (inbound receipts, outbound sales, transfers, or write-offs)."""
    if req.sku not in inventory_db:
        raise HTTPException(status_code=404, detail=f"SKU {req.sku} not registered in catalog")
    
    item = inventory_db[req.sku]
    
    if req.movement_type in [StockMovementType.OUTBOUND_SALE, StockMovementType.SCRAP_DAMAGE]:
        if item.current_stock < req.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient physical stock for {req.sku}. Available: {item.current_stock}, requested: {req.quantity}"
            )
        item.current_stock -= req.quantity
        delta = -req.quantity
    elif req.movement_type == StockMovementType.INBOUND_PURCHASE:
        item.current_stock += req.quantity
        delta = req.quantity
    else:
        delta = 0

    record = StockMovementRecord(
        movement_id=f"MOV-{uuid.uuid4().hex[:8].upper()}",
        timestamp=datetime.utcnow(),
        sku=req.sku,
        movement_type=req.movement_type,
        quantity_changed=delta,
        balance_after=item.current_stock,
        reference_id=req.reference_id
    )
    movement_ledger.append(record)
    return record

@app.get("/api/v1/alerts/reorder", response_model=List[InventoryItem])
def get_reorder_alerts():
    """Returns all items that have reached or breached their automated reorder point."""
    alerts = []
    for item in inventory_db.values():
        available = item.current_stock - item.reserved_stock
        if available <= item.reorder_point:
            item.is_low_stock = True
            alerts.append(item)
    return alerts

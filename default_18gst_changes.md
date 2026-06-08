# Default 18% GST Changes

## Summary
Added default 18% GST (`18% GST P`) to all manual-input `tax_id` fields across the zigma_erp module.

---

## Files Changed

### 1. `/opt/odoo17/odoo17/custom-addons/zigma_erp/models/item_details.py`

**Change 1 — `ItemDetails.tax_id` (line ~117)**
- Added `_default_tax_id()` method
- Added `default=_default_tax_id` to the `tax_id` Many2many field
- Model: `item.details`

**Change 2 — `ProductTemplate.taxes_id` (line ~6)**
- Inherited `taxes_id` field from `product.template`
- Added `_default_taxes_id()` method returning 18% GST P
- Applies when creating a new product

---

### 2. `/opt/odoo17/odoo17/custom-addons/zigma_erp/models/stock_picking_items.py`

**Change 3 — `StockPickingItemLine.tax_id` (line ~214)**
- Added `_default_tax_id()` method inside `StockPickingItemLine` class
- Added `default=_default_tax_id` to the `tax_id` Many2many field
- Model: `stock.picking.item.line`

**Change 4 — `StockMove.tax_id` (line ~1836)**
- Added `_default_tax_id()` method inside inherited `StockMove` class
- Added `default=_default_tax_id` to the `tax_id` Many2many field
- Model: `stock.move` (_inherit)

---

## Tax Search Logic Used (all files)
```python
def _default_tax_id(self):
    return self.env['account.tax'].search([('name', '=', '18% GST P')], limit=1)
```

---

## How to Apply
```bash
./odoo-bin -u zigma_erp -d <your_database_name>
```

---

## Notes
- Computed `tax_id` fields (quotation lines, sale order item lines, consignee lines) were NOT changed — they auto-fill from business logic.
- If a user manually changes the tax, the changed value is saved (default only applies on new record creation).
- The tax name `18% GST P` must exist in `account.tax` table for this to work.

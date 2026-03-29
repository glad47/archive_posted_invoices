from . import models


def _pre_init_add_active_field(cr):
    """Add the 'active' field to account.move BEFORE views are validated.

    Odoo validates views before ORM fields are fully registered during install.
    We must add both the DB column AND the ir_model_fields record so Odoo's
    view validator recognizes the field.
    """
    # Step 1: Add the DB column
    cr.execute("""
        ALTER TABLE account_move
        ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;
    """)
    cr.execute("""
        UPDATE account_move SET active = TRUE WHERE active IS NULL;
    """)

    # Step 2: Register in ir_model_fields so view validation passes
    cr.execute("SELECT id FROM ir_model WHERE model = 'account.move'")
    model_row = cr.fetchone()
    if model_row:
        model_id = model_row[0]
        cr.execute(
            "SELECT id FROM ir_model_fields WHERE model_id = %s AND name = 'active'",
            (model_id,)
        )
        if not cr.fetchone():
            cr.execute("""
                INSERT INTO ir_model_fields
                    (model_id, model, name, field_description, ttype, state, store, readonly, copied)
                VALUES
                    (%s, 'account.move', 'active', 'Active', 'boolean', 'base', TRUE, FALSE, FALSE)
            """, (model_id,))

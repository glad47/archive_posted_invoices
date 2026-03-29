from . import models


def _pre_init_add_active_field(cr):
    """Add the 'active' column to account_move BEFORE views are validated.

    This prevents the 'Field active does not exist' error during install,
    since Odoo validates inherited views before the ORM creates new fields.
    """
    cr.execute("""
        ALTER TABLE account_move
        ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;
    """)
    cr.execute("""
        UPDATE account_move SET active = TRUE WHERE active IS NULL;
    """)

"""add profile detail check constraints

Revision ID: f3c9a2d8b741
Revises: ebbc15959847
Create Date: 2026-06-02

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f3c9a2d8b741"
down_revision: Union[str, Sequence[str], None] = "ebbc15959847"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_daily_profile_production_ton_non_negative",
        "daily_profile_details",
        "production_ton >= 0",
    )

    op.create_check_constraint(
        "ck_daily_profile_raw_material_ton_non_negative",
        "daily_profile_details",
        "raw_material_ton >= 0",
    )

    op.create_check_constraint(
        "ck_daily_profile_predicted_wip_ton_non_negative",
        "daily_profile_details",
        "predicted_wip_ton IS NULL OR predicted_wip_ton >= 0",
    )

    op.create_check_constraint(
        "ck_daily_profile_actual_wip_ton_non_negative",
        "daily_profile_details",
        "actual_wip_ton IS NULL OR actual_wip_ton >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_daily_profile_actual_wip_ton_non_negative",
        "daily_profile_details",
        type_="check",
    )

    op.drop_constraint(
        "ck_daily_profile_predicted_wip_ton_non_negative",
        "daily_profile_details",
        type_="check",
    )

    op.drop_constraint(
        "ck_daily_profile_raw_material_ton_non_negative",
        "daily_profile_details",
        type_="check",
    )

    op.drop_constraint(
        "ck_daily_profile_production_ton_non_negative",
        "daily_profile_details",
        type_="check",
    )
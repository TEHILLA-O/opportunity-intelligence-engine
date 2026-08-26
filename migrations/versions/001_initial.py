"""Initial schema.

Revision ID: 001_initial
Revises:
Create Date: 2026-08-26

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("last_successful_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failed_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("avg_response_ms", sa.Float(), nullable=True),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("records_discovered", sa.Integer(), nullable=False),
        sa.Column("records_accepted", sa.Integer(), nullable=False),
        sa.Column("records_rejected", sa.Integer(), nullable=False),
        sa.Column("health_status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sources_name", "sources", ["name"], unique=True)
    op.create_index("ix_sources_health_status", "sources", ["health_status"])

    op.create_table(
        "automation_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("trigger", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("source_filter", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_runs_status_started", "automation_runs", ["status", "started_at"])
    op.create_index("ix_runs_trigger", "automation_runs", ["trigger"])

    op.create_table(
        "automation_run_steps",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.Uuid(as_uuid=True), sa.ForeignKey("automation_runs.id"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_run_steps_run_name", "automation_run_steps", ["run_id", "name"])
    op.create_index("ix_automation_run_steps_run_id", "automation_run_steps", ["run_id"])

    op.create_table(
        "raw_opportunities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.Uuid(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("run_id", sa.Uuid(as_uuid=True), sa.ForeignKey("automation_runs.id"), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_title", sa.Text(), nullable=True),
        sa.Column("raw_description", sa.Text(), nullable=True),
        sa.Column("raw_organisation", sa.Text(), nullable=True),
        sa.Column("raw_location", sa.Text(), nullable=True),
        sa.Column("raw_value", sa.String(255), nullable=True),
        sa.Column("raw_deadline", sa.String(255), nullable=True),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("http_headers", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_raw_source_external", "raw_opportunities", ["source_id", "external_id"])
    op.create_index("ix_raw_content_hash", "raw_opportunities", ["content_hash"])
    op.create_index("ix_raw_run_id", "raw_opportunities", ["run_id"])
    op.create_index("ix_raw_opportunities_source_id", "raw_opportunities", ["source_id"])

    op.create_table(
        "opportunities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.Uuid(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("raw_opportunity_id", sa.Uuid(as_uuid=True), sa.ForeignKey("raw_opportunities.id"), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("organisation", sa.String(300), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(120), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("remote_status", sa.String(20), nullable=False),
        sa.Column("procurement_type", sa.String(30), nullable=False),
        sa.Column("contract_type", sa.String(40), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("minimum_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("maximum_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("estimated_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("contact_email", sa.String(254), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("score_rating", sa.String(20), nullable=False),
        sa.Column("score_reasons", sa.JSON(), nullable=False),
        sa.Column("deadline_status", sa.String(20), nullable=False),
        sa.Column("days_remaining", sa.Integer(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("normalised_title", sa.String(500), nullable=True),
        sa.Column("normalised_organisation", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_id", "external_id", name="uq_opportunity_source_external"),
    )
    op.create_index("ix_opportunity_score", "opportunities", ["score"])
    op.create_index("ix_opportunity_deadline", "opportunities", ["deadline_at"])
    op.create_index("ix_opportunity_status", "opportunities", ["status"])
    op.create_index("ix_opportunity_rating", "opportunities", ["score_rating"])
    op.create_index("ix_opportunity_first_seen", "opportunities", ["first_seen_at"])
    op.create_index("ix_opportunity_org", "opportunities", ["organisation"])
    op.create_index("ix_opportunity_hash", "opportunities", ["content_hash"])
    op.create_index("ix_opportunity_canonical_url", "opportunities", ["canonical_url"])
    op.create_index("ix_opportunity_fingerprint", "opportunities", ["fingerprint"])
    op.create_index("ix_opportunities_source_id", "opportunities", ["source_id"])
    op.create_index("ix_opportunities_category", "opportunities", ["category"])

    op.create_table(
        "opportunity_history",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", sa.Uuid(as_uuid=True), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("run_id", sa.Uuid(as_uuid=True), sa.ForeignKey("automation_runs.id"), nullable=True),
        sa.Column("field_name", sa.String(80), nullable=False),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_history_opportunity_detected", "opportunity_history", ["opportunity_id", "detected_at"])
    op.create_index("ix_opportunity_history_opportunity_id", "opportunity_history", ["opportunity_id"])

    op.create_table(
        "duplicate_candidates",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", sa.Uuid(as_uuid=True), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("candidate_id", sa.Uuid(as_uuid=True), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("opportunity_id", "candidate_id", name="uq_duplicate_pair"),
    )
    op.create_index("ix_dup_left_right", "duplicate_candidates", ["opportunity_id", "candidate_id"])

    op.create_table(
        "ingestion_errors",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.Uuid(as_uuid=True), sa.ForeignKey("automation_runs.id"), nullable=True),
        sa.Column("source_id", sa.Uuid(as_uuid=True), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("error_type", sa.String(80), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ingestion_errors_run_source", "ingestion_errors", ["run_id", "source_id"])
    op.create_index("ix_ingestion_errors_run_id", "ingestion_errors", ["run_id"])
    op.create_index("ix_ingestion_errors_source_id", "ingestion_errors", ["source_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(as_uuid=True), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("run_id", sa.Uuid(as_uuid=True), sa.ForeignKey("automation_runs.id"), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_event_type", "notifications", ["event_type"])

    op.create_table(
        "exports",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("format", sa.String(10), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Uuid(as_uuid=True), sa.ForeignKey("automation_runs.id"), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "exports",
        "notifications",
        "ingestion_errors",
        "duplicate_candidates",
        "opportunity_history",
        "opportunities",
        "raw_opportunities",
        "automation_run_steps",
        "automation_runs",
        "sources",
    ]:
        op.drop_table(table)

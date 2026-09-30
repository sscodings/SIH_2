import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="investigator")  # investigator, supervisor, admin
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(100), unique=True, index=True, nullable=False)
    revoked_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

class UserRefreshToken(Base):
    __tablename__ = "user_refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    complaint_number = Column(String(100), unique=True, index=True, nullable=False)
    source = Column(String(50), default="NCRP")  # NCRP, SAHYOG, Manual, Bulk
    victim_name = Column(String(255), nullable=False)
    victim_state = Column(String(100), default="Maharashtra")
    fraud_type = Column(String(100), default="Investment Scam")
    reported_wallets = Column(Text, nullable=False)  # JSON list of addresses
    chain = Column(String(50), default="tron")
    amount_lost_inr = Column(Float, default=0.0)
    amount_lost_usd = Column(Float, default=0.0)
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="New")  # New, Assigned, Tracing, Actioned, Closed
    priority = Column(String(50), default="High")  # Critical, High, Medium, Low
    raw_payload = Column(Text, default="{}")  # JSON

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(100), unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    primary_chain = Column(String(50), default="tron")
    primary_address = Column(String(255), index=True, nullable=False)
    status = Column(String(50), default="Active")  # Active, In Review, Frozen, Closed
    priority = Column(String(50), default="High")
    time_to_vasp_seconds = Column(Float, nullable=True)
    created_by = Column(String(255), default="system", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class CaseComplaint(Base):
    __tablename__ = "case_complaints"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), index=True)
    linked_at = Column(DateTime, default=datetime.datetime.utcnow)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(255), index=True, nullable=False)
    chain = Column(String(50), index=True, nullable=False)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    balance_usd = Column(Float, default=0.0)
    total_received_usd = Column(Float, default=0.0)
    total_sent_usd = Column(Float, default=0.0)
    tx_count = Column(Integer, default=0)
    risk_score = Column(Float, default=15.0)  # 0 to 100
    risk_level = Column(String(50), default="Low")  # Low, Medium, High, Critical
    category = Column(String(100), default="Unknown")  # Mule, Collector, Intermediary, Peel, VASP Deposit, Mixer
    is_monitored = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Transfer(Base):
    __tablename__ = "transfers"
    id = Column(Integer, primary_key=True, index=True)
    chain = Column(String(50), index=True, nullable=False)
    tx_hash = Column(String(255), index=True, nullable=False)
    block_number = Column(Integer, default=0)
    timestamp = Column(DateTime, nullable=False, index=True)
    from_address = Column(String(255), index=True, nullable=False)
    to_address = Column(String(255), index=True, nullable=False)
    token = Column(String(50), default="USDT")
    amount = Column(Float, nullable=False)
    amount_usd = Column(Float, nullable=False)
    is_contract_call = Column(Boolean, default=False)
    method_name = Column(String(100), nullable=True)
    log_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_transfers_chain_from_ts", "chain", "from_address", "timestamp"),
        Index("ix_transfers_chain_to_ts", "chain", "to_address", "timestamp"),
    )

class Label(Base):
    __tablename__ = "labels"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(255), index=True, nullable=False)
    chain = Column(String(50), index=True, nullable=False)
    entity = Column(String(255), nullable=False)
    category = Column(String(100), default="VASP")  # VASP, Mixer, Bridge, Scam, High-Risk, sanctioned
    source = Column(String(100), default="Manual")  # In-House, FIU-IND, OFAC, Exchange CSV
    source_url = Column(String(500), nullable=True)
    license = Column(String(255), nullable=True)
    weight_tier = Column(String(50), default="unverified_official")
    wallet_type = Column(String(50), default="unknown")  # hot, cold, unknown, deposit
    raw_wallet_type = Column(String(255), nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    superseded_by = Column(String(255), nullable=True)
    record_status = Column(String(50), default="active")  # active, pending, revoked, inactive
    snapshot_date = Column(String(100), nullable=True)
    confidence = Column(Float, default=0.90)  # 0.0 to 1.0
    verified_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_labels_chain_address", "chain", "address"),
        Index("ix_labels_status", "record_status"),
    )

class LabelSource(Base):
    __tablename__ = "label_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    weight = Column(Float, default=0.85)  # Mathematical weight W_label
    description = Column(String(255), default="")

class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), default="VASP")  # VASP, Mixer, Bridge, DEX, Payment Gateway
    jurisdiction = Column(String(100), default="Global")
    compliance_contact = Column(String(255), default="")
    response_sla = Column(String(100), default="24 Hours")
    description = Column(Text, default="")
    registered_in_india = Column(Boolean, default=False)
    as_of = Column(String(50), nullable=True)
    trade_names = Column(Text, default="[]")  # JSON list of aliases
    entity_type = Column(String(100), nullable=True)
    registration_date = Column(String(100), nullable=True)
    nodal_officer_email = Column(String(255), nullable=True)
    nodal_officer_phone = Column(String(100), nullable=True)
    source = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EntityAddress(Base):
    __tablename__ = "entity_addresses"
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)
    address = Column(String(255), index=True, nullable=False)
    chain = Column(String(50), nullable=False)
    address_type = Column(String(50), default="Hot Wallet")  # Hot Wallet, Cold Wallet, Deposit Sweeper, Router Contract

    __table_args__ = (
        Index("ix_entity_addresses_chain_address", "chain", "address"),
    )

class Cluster(Base):
    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    primary_entity = Column(String(255), default="Suspect Syndicate")
    cluster_type = Column(String(100), default="Common Sweep")
    member_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ClusterMember(Base):
    __tablename__ = "cluster_members"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), index=True)
    address = Column(String(255), index=True, nullable=False)
    chain = Column(String(50), nullable=False)
    rule_formed = Column(String(100), default="same_sweep_target")
    confidence = Column(Float, default=0.85)
    evidence_tx_hashes = Column(Text, default="[]")

    __table_args__ = (
        Index("ix_cluster_members_chain_address", "chain", "address"),
        UniqueConstraint("cluster_id", "chain", "address", name="uq_cluster_members_id_chain_addr"),
    )

class TraceJob(Base):
    __tablename__ = "trace_jobs"
    id = Column(String(100), primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    status = Column(String(50), default="running")  # running, completed, failed, cancelled
    params = Column(Text, default="{}")  # JSON
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    elapsed_seconds = Column(Float, default=0.0)

class TraceSnapshot(Base):
    __tablename__ = "trace_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    snapshot_json = Column(Text, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class GraphNode(Base):
    __tablename__ = "graph_nodes"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    node_id = Column(String(255), nullable=False)
    address = Column(String(255), index=True, nullable=False)
    chain = Column(String(50), default="tron")
    entity_type = Column(String(100), default="Unknown")
    label = Column(String(255), nullable=True)
    risk_level = Column(String(50), default="Low")
    value_usd = Column(Float, default=0.0)
    metadata_json = Column(Text, default="{}")

class GraphEdge(Base):
    __tablename__ = "graph_edges"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    source = Column(String(255), nullable=False)
    target = Column(String(255), nullable=False)
    tx_hash = Column(String(255), nullable=False)
    amount = Column(Float, default=0.0)
    amount_usd = Column(Float, default=0.0)
    token = Column(String(50), default="USDT")
    timestamp = Column(DateTime, nullable=False)
    is_cross_chain = Column(Boolean, default=False)
    confidence = Column(Float, default=1.0)

class Attribution(Base):
    __tablename__ = "attributions"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    vasp_name = Column(String(255), nullable=False)
    vasp_category = Column(String(100), default="Exchange")
    deposit_address = Column(String(255), nullable=False)
    tx_hash = Column(String(255), nullable=False)
    amount = Column(Float, default=0.0)
    timestamp = Column(DateTime, nullable=False)
    hops_from_suspect = Column(Integer, default=1)
    confidence_score = Column(Float, default=90.0)
    evidence_breakdown = Column(Text, default="{}")  # JSON

class FundsStatus(Base):
    __tablename__ = "funds_status"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    total_traced_usd = Column(Float, default=0.0)
    vasp_amount_usd = Column(Float, default=0.0)
    mixer_amount_usd = Column(Float, default=0.0)
    dormant_amount_usd = Column(Float, default=0.0)
    unaccounted_usd = Column(Float, default=0.0)

class CrossChainBridgeEvent(Base):
    __tablename__ = "cross_chain_bridge_events"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    source_chain = Column(String(50), nullable=False)
    source_tx_hash = Column(String(255), nullable=False)
    source_wallet = Column(String(255), nullable=False)
    destination_chain = Column(String(50), nullable=False)
    destination_tx_hash = Column(String(255), nullable=False)
    destination_wallet = Column(String(255), nullable=False)
    bridge_name = Column(String(100), default="Cross-Chain Router")
    amount = Column(Float, default=0.0)
    token = Column(String(50), default="USDT")
    confidence = Column(Float, default=0.88)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class MixerEvent(Base):
    __tablename__ = "mixer_events"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    chain = Column(String(50), nullable=False)
    mixer_name = Column(String(100), default="VeilMix / Privacy Tumbler")
    deposit_address = Column(String(255), nullable=False)
    deposit_tx_hash = Column(String(255), nullable=False)
    amount_usd = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    candidates = Column(Text, default="[]")  # JSON list of candidate withdrawals with probabilities

class TypologyMatch(Base):
    __tablename__ = "typology_matches"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    typology_name = Column(String(100), nullable=False)  # Pig-Butchering, Task Fraud, Sextortion, Ransomware
    confidence_score = Column(Float, default=0.85)
    indicators = Column(Text, default="[]")  # JSON

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    priority = Column(String(50), default="High")  # Critical, High, Medium
    action_type = Column(String(100), default="FREEZE")
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    rationale = Column(Text, default="")
    target_address = Column(String(255), nullable=True)
    target_vasp = Column(String(255), nullable=True)
    is_actioned = Column(Boolean, default=False)

class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(255), index=True, nullable=False)
    chain = Column(String(50), nullable=False)
    label = Column(String(255), default="")
    reason = Column(String(255), default="High-risk suspect holding")
    alert_on_outflow = Column(Boolean, default=True)
    min_threshold_usd = Column(Float, default=50.0)
    alert_on_vasp = Column(Boolean, default=True)
    alert_on_mixer = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), default="FUNDS_MOVED")
    severity = Column(String(50), default="High")  # Critical, High, Medium, Info
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    address = Column(String(255), nullable=True)
    chain = Column(String(50), nullable=True)
    case_id = Column(Integer, nullable=True)
    tx_hash = Column(String(255), nullable=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class FreezeRequest(Base):
    __tablename__ = "freeze_requests"
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(100), unique=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    vasp_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    vasp_name = Column(String(255), nullable=False)
    deposit_address = Column(String(255), nullable=False)
    suspect_wallet = Column(String(255), nullable=False)
    victim_loss_inr = Column(Float, default=0.0)
    victim_loss_usd = Column(Float, default=0.0)
    tx_hashes = Column(Text, default="[]")  # JSON
    status = Column(String(50), default="Draft")  # Draft, Pending Approval, Approved, Sent, Acknowledged, Frozen, Rejected
    legal_order_ref = Column(String(255), default="Cr.No 402/2026 U/S 66D IT Act & 420 IPC")
    created_by = Column(String(255), default="system", nullable=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    frozen_amount_usd = Column(Float, default=0.0)
    pdf_path = Column(String(500), nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    report_number = Column(String(100), unique=True, index=True)
    pdf_path = Column(String(500), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    snapshot_sha256 = Column(String(64), nullable=False)
    generated_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CaseNote(Base):
    __tablename__ = "case_notes"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    author_email = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    target_url = Column(String(500), nullable=False)
    events = Column(Text, default='["trace_complete", "vasp_found", "freeze_alert"]')  # JSON list
    is_active = Column(Boolean, default=True)
    secret = Column(String(255), nullable=False)  # Stored hashed secret
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, default="{}")
    status_code = Column(Integer, default=0)
    response_body = Column(Text, default="")
    latency_ms = Column(Integer, default=0)
    success = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(16), nullable=False)
    hashed_key = Column(String(255), nullable=False)
    role = Column(String(50), default="investigator")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    user_email = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    details = Column(Text, default="{}")  # JSON
    prev_hash = Column(String(64), nullable=False, unique=True)
    entry_hash = Column(String(64), nullable=False)
    signature = Column(String(128), nullable=True)  # HMAC-SHA256 signature with AUDIT_HMAC_KEY

class AuditCheckpoint(Base):
    __tablename__ = "audit_checkpoints"
    id = Column(Integer, primary_key=True, index=True)
    last_audit_id = Column(Integer, nullable=False)
    last_entry_hash = Column(String(64), nullable=False)
    checkpoint_signature = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AppSetting(Base):
    __tablename__ = "app_settings"
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), default="")

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="User")  # Admin, Analyst, User
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    activities = relationship("ActivityLog", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    action_type = Column(String, nullable=False)  # LOGIN, FILE_ACCESS, DATA_TRANSFER, PRIVILEGE_USE
    resource_id = Column(String, nullable=True)
    bytes_transferred = Column(Float, default=0.0)
    is_sensitive_file = Column(Boolean, default=False)
    failed_attempts = Column(Integer, default=0)
    privilege_level = Column(Integer, default=0)
    session_duration_sec = Column(Float, default=0.0)
    source_ip = Column(String, default="127.0.0.1")

    user = relationship("User", back_populates="activities")

class ThreatAnalysisRecord(Base):
    __tablename__ = "threat_analysis_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    raw_features = Column(JSON, nullable=False)
    iforest_score = Column(Float, nullable=False)
    ocsvm_score = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    shap_attributions = Column(JSON, nullable=False)

    # --- NEW: PART 2 RESEARCH METRICS ---
    attacker_state_probs = Column(JSON, nullable=True)     # Step 3
    adaptation_score = Column(Float, default=0.0)          # Step 4: AAS
    response_effectiveness = Column(Float, default=0.0)    # Step 5: RES
    attacker_state = Column(String, default="UNKNOWN")     # Dominant State
    # ------------------------------------

    game_action = Column(String, nullable=False)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    severity = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Float, nullable=False)
    triggering_factors = Column(JSON, nullable=False)
    recommended_action = Column(String, nullable=False)
    is_resolved = Column(Boolean, default=False)

    user = relationship("User", back_populates="alerts")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    risk_score = Column(Float, nullable=False)
    threat_type = Column(String, default="Adaptive Malicious Insider Threat with Data Exfiltration")
    shap_summary = Column(JSON, nullable=False)
    enforced_action = Column(String, nullable=False)
    status = Column(String, default="OPEN")  # OPEN, INVESTIGATING, MITIGATED

class SecureAuditLog(Base):
    """
    Stage 8: Cryptographically sealed ledger for all RASRO decisions.
    """
    __tablename__ = "secure_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    event_payload = Column(JSON, nullable=False)
    cryptographic_hash = Column(String(256), nullable=False)
    previous_hash = Column(String(256), nullable=False, default="GENESIS_BLOCK")

class ResearchInteraction(Base):
    """Immutable metric inputs captured at decision time; added as a new table.

    create_all creates this table without altering existing historical tables.
    """
    __tablename__ = "research_interactions"
    id = Column(Integer, primary_key=True)
    threat_record_id = Column(Integer, ForeignKey("threat_analysis_records.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    previous_behaviour = Column(JSON, nullable=False)
    current_behaviour = Column(JSON, nullable=False)
    previous_defence = Column(String, nullable=False)
    previous_risk = Column(Float, nullable=False)
    current_risk = Column(Float, nullable=False)
    current_attacker_state = Column(String, nullable=False)
    aas = Column(Float, nullable=False)
    res = Column(Float, nullable=False)
    res_available = Column(Boolean, nullable=False)
    res_components = Column(JSON, nullable=False)
    game_details = Column(JSON, nullable=False)

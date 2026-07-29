"""
models/__init__.py — ForenSync Database Models.

Defines SQLAlchemy ORM models matching the ForenSync domain:
- Organization (organizations)
- User / Investigator (users)
- Case (cases)
- LogFile (log_files)
- Plugin (plugins)
- TimelineEvent (timeline_events)
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    org_head_id = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Relationships
    users = db.relationship("User", backref="organization", lazy=True, cascade="all, delete-orphan")
    cases = db.relationship("Case", backref="organization", lazy=True, cascade="all, delete-orphan")
    plugins = db.relationship("Plugin", backref="organization", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "orgId": self.org_id,
            "orgName": self.name,
            "orgHeadId": self.org_head_id,
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)  # INV-xxxx or HEAD-xxxx
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="investigator")  # investigator | head
    org_id = db.Column(db.String(64), db.ForeignKey("organizations.org_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.user_id,
            "name": self.name,
            "role": self.role,
            "orgId": self.org_id,
        }


class Case(db.Model):
    __tablename__ = "cases"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(64), unique=True, nullable=False, index=True)  # CASE-xxxx
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True, default="")
    date_from = db.Column(db.String(32), nullable=True, default="")
    date_to = db.Column(db.String(32), nullable=True, default="")
    timeframe = db.Column(db.String(128), nullable=False, default="—")
    status = db.Column(db.String(32), nullable=False, default="Active")  # Active | Under Review | Closed
    action = db.Column(db.String(32), nullable=False, default="Open")    # Open | View
    org_id = db.Column(db.String(64), db.ForeignKey("organizations.org_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    last_modified = db.Column(db.String(64), nullable=False, default="just now")

    # Relationships
    log_files = db.relationship("LogFile", backref="case", lazy=True, cascade="all, delete-orphan")
    timeline_events = db.relationship("TimelineEvent", backref="case", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "caseId": self.case_id,
            "name": self.name,
            "description": self.description or "",
            "timeframe": self.timeframe,
            "lastModified": self.last_modified,
            "status": self.status,
            "action": self.action,
        }


class LogFile(db.Model):
    __tablename__ = "log_files"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=False, default=0)
    job_id = db.Column(db.String(64), nullable=True)
    parse_status = db.Column(db.String(32), nullable=False, default="queued")  # queued | processing | parsed | failed
    case_id = db.Column(db.String(64), db.ForeignKey("cases.case_id"), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "size": self.file_size,
            "caseId": self.case_id,
            "jobId": self.job_id,
            "parseStatus": self.parse_status,
            "uploadedAt": self.uploaded_at.strftime("%Y-%m-%d %H:%M") if self.uploaded_at else "",
        }


class Plugin(db.Model):
    __tablename__ = "plugins"

    id = db.Column(db.Integer, primary_key=True)
    plugin_id = db.Column(db.String(64), nullable=False, index=True)  # linux-auth | apache-access | custom
    label = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    org_id = db.Column(db.String(64), db.ForeignKey("organizations.org_id"), nullable=True)
    added_on = db.Column(db.String(64), nullable=False, default="today")

    def to_dict(self):
        return {
            "id": self.plugin_id,
            "label": self.label,
            "isActive": self.is_active,
            "name": self.label,
            "addedOn": self.added_on,
        }


class TimelineEvent(db.Model):
    __tablename__ = "timeline_events"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(64), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    log_file_id = db.Column(db.Integer, db.ForeignKey("log_files.id"), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True, default=utcnow)
    timestamp_str = db.Column(db.String(64), nullable=True)
    source = db.Column(db.String(128), nullable=False, default="system")
    event_type = db.Column(db.String(128), nullable=False, default="Log Entry")
    severity = db.Column(db.String(32), nullable=False, default="Info")  # Info | Warning | Critical
    description = db.Column(db.Text, nullable=False)
    raw_log = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "caseId": self.case_id,
            "timestamp": self.timestamp_str or (self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else ""),
            "source": self.source,
            "eventType": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "rawLog": self.raw_log or "",
        }


def init_db(app):
    """Initialize database extension and create tables if they do not exist."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        seed_initial_data()


def seed_initial_data():
    """Seed default organization, users, plugins, and cases if database is empty."""
    # Seed default Organization if missing
    org = Organization.query.filter_by(org_id="ORG-4410").first()
    if not org:
        org = Organization(
            org_id="ORG-4410",
            name="Sentinel Cyber Forensics",
            org_head_id="HEAD-0001",
        )
        db.session.add(org)
        db.session.commit()

    # Seed default Users if missing
    if not User.query.filter_by(org_id="ORG-4410").first():
        users = [
            User(user_id="HEAD-0001", name="Organization Head", role="head", org_id="ORG-4410"),
            User(user_id="INV-2291", name="Aditi Rao", role="investigator", org_id="ORG-4410"),
            User(user_id="INV-2287", name="Rohan Mehta", role="investigator", org_id="ORG-4410"),
        ]
        db.session.add_all(users)
        db.session.commit()

    # Seed default Plugins if missing
    if not Plugin.query.filter_by(org_id="ORG-4410").first():
        plugins = [
            Plugin(plugin_id="linux-auth", label="Linux Auth Log Parser", is_active=False, org_id="ORG-4410"),
            Plugin(plugin_id="apache-access", label="Apache Access Log Parser", is_active=False, org_id="ORG-4410"),
            Plugin(plugin_id="custom", label="Develop Custom Plugin", is_active=False, org_id="ORG-4410"),
        ]
        db.session.add_all(plugins)
        db.session.commit()

    # Seed default Cases if missing
    if not Case.query.filter_by(org_id="ORG-4410").first():
        cases = [
            Case(
                case_id="CASE-1042",
                name="Unauthorized SSH Access — prod-web-03",
                description="Investigation into unauthorized root shell access on production web server 03.",
                timeframe="02 Jul – 05 Jul 2026",
                last_modified="2026-07-09 18:22",
                status="Active",
                action="Open",
                org_id="ORG-4410",
            ),
            Case(
                case_id="CASE-1041",
                name="Suspicious Apache Traffic Spike",
                description="High volume anomalous HTTP GET requests from external IP subnet.",
                timeframe="28 Jun – 30 Jun 2026",
                last_modified="2026-07-08 11:05",
                status="Under Review",
                action="Open",
                org_id="ORG-4410",
            ),
            Case(
                case_id="CASE-1038",
                name="Failed Login Brute Force — auth-gateway",
                description="Brute force login attempts detected targeting admin accounts.",
                timeframe="18 Jun – 20 Jun 2026",
                last_modified="2026-07-02 09:40",
                status="Active",
                action="Open",
                org_id="ORG-4410",
            ),
            Case(
                case_id="CASE-1031",
                name="Data Exfiltration Attempt — file-srv-01",
                description="Large outbound file transfers detected during off-peak hours.",
                timeframe="01 Jun – 04 Jun 2026",
                last_modified="2026-06-25 16:12",
                status="Closed",
                action="View",
                org_id="ORG-4410",
            ),
            Case(
                case_id="CASE-1027",
                name="Privilege Escalation — internal CI runner",
                description="Container escape attempt on secondary integration node.",
                timeframe="14 May – 16 May 2026",
                last_modified="2026-06-10 08:55",
                status="Closed",
                action="View",
                org_id="ORG-4410",
            ),
        ]
        db.session.add_all(cases)
        db.session.commit()

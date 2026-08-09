"""API pública del subsistema de monitorización.

Los símbolos se exportan de forma explícita para que los cambios internos no
alteren accidentalmente el contrato que consumen plugins e integraciones.
"""

from .models import (
    AUTHORITIES,
    HEALTH,
    MODES,
    PRESENCE,
    SESSION_STATES,
    AssignmentProvider,
    CheckResult,
    CheckSpec,
    ConfigProvider,
    DeviceState,
    Incident,
    IncidentRepository,
    MetricsStore,
    MonitorProfile,
    MonitorSession,
    MonitorTargetPlan,
    ReportBuilder,
    SessionRepository,
    now_iso,
)
from .service import MonitorService

__all__ = [
    "AUTHORITIES",
    "HEALTH",
    "MODES",
    "PRESENCE",
    "SESSION_STATES",
    "AssignmentProvider",
    "CheckResult",
    "CheckSpec",
    "ConfigProvider",
    "DeviceState",
    "Incident",
    "IncidentRepository",
    "MetricsStore",
    "MonitorProfile",
    "MonitorService",
    "MonitorSession",
    "MonitorTargetPlan",
    "ReportBuilder",
    "SessionRepository",
    "now_iso",
]

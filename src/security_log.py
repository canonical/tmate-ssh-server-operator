# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""OWASP-compliant security event logger for the tmate-ssh-server charm.

Single source of truth for the ``appid`` used in every security event. Import
``owasp_log`` wherever a security event occurs; never re-instantiate it.
"""

import logging
from datetime import datetime, timezone

from owasp_logger import OWASPLogger
from owasp_logger.model import NESTED_JSON_KEY, OWASPLogEvent, OWASPLogMetadata

APPID = "canonical.tmate-ssh-server"


class _UTCOWASPLogger(OWASPLogger):
    """OWASP logger that renders event timestamps in UTC.

    The upstream logger stamps events with ``datetime.now(timezone.utc).astimezone()``,
    which renders in the host's local UTC offset. OWASP requires UTC-aligned security
    timestamps, so emit RFC3339 UTC ("...Z") regardless of the host timezone.
    """

    def _log_event(self, event: str, level: int, metadata: OWASPLogMetadata) -> None:
        """Emit an OWASP event envelope with a UTC-rendered timestamp.

        Args:
            event: The OWASP event identifier (e.g. ``sys_startup:<userid>``).
            level: The log level to emit the event at.
            metadata: Extra OWASP metadata fields to attach to the envelope.
        """
        log = OWASPLogEvent(
            datetime=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            type="security",
            appid=self.appid,
            event=event,
            level=logging.getLevelName(level),
            **metadata,
        )
        self.logger.log(
            level,
            log.to_json(nested_json_key=NESTED_JSON_KEY),
            extra={NESTED_JSON_KEY: log.to_dict()},
        )


owasp_log = _UTCOWASPLogger(appid=APPID)

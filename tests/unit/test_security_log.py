# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm security log unit tests."""

import json
import re
from unittest.mock import MagicMock

import security_log


def test_utc_owasp_logger_emits_nested_utc_json():
    """
    arrange: the public owasp_log singleton whose underlying logger is a mock.
    act: emit a sys_startup security event.
    assert: the record is JSON nested under owasp_event, carries the OWASP fields,
        and its timestamp is RFC3339 UTC ("Z"), so SIEM ingestion sees a
        consistent UTC-aligned schema regardless of the host timezone.
    """
    security_log.owasp_log.logger = MagicMock()

    security_log.owasp_log.sys_startup(userid="tmate-ssh-server/0", description="started")

    args, kwargs = security_log.owasp_log.logger.log.call_args
    payload = json.loads(args[1])
    event = payload[security_log.NESTED_JSON_KEY]
    assert event["appid"] == "canonical.tmate-ssh-server"
    assert event["type"] == "security"
    assert event["event"] == "sys_startup:tmate-ssh-server/0"
    assert event["level"] == "WARNING"
    assert event["description"] == "started"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", event["datetime"])
    assert kwargs["extra"][security_log.NESTED_JSON_KEY] == event

"""Deterministic, payload-free safety contracts for F-009 input admission."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

SAFETY_POLICY_VERSION = "f-009-input-policy-v1"


class SafetyOutcome(StrEnum):
    ALLOWED = "allowed"
    REJECTED = "rejected"


class SafetyReasonCode(StrEnum):
    ALLOWED = "allowed"
    PERSONA_OVERRIDE = "persona_override"
    SYSTEM_PROMPT_PROBE = "system_prompt_probe"
    SECRET_EXTRACTION = "secret_extraction"
    CROSS_SCOPE_INJECTION = "cross_scope_injection"
    TOOL_CALL_INJECTION = "tool_call_injection"
    MEMORY_INSTRUCTION = "memory_instruction"


class RateLimitOutcome(StrEnum):
    NOT_REACHED = "not_reached"
    ALLOWED = "allowed"
    REJECTED = "rejected"
    FAILED = "failed"


class BudgetOutcome(StrEnum):
    NOT_REACHED = "not_reached"
    RESERVED = "reserved"
    SETTLED = "settled"
    REJECTED = "rejected"
    FAILED = "failed"


class RetryOutcome(StrEnum):
    NOT_REACHED = "not_reached"
    NOT_ELIGIBLE = "not_eligible"
    SCHEDULED = "scheduled"
    ATTEMPTED = "attempted"
    EXHAUSTED = "exhausted"
    CANCELLED = "cancelled"


class BreakerState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class BreakerOutcome(StrEnum):
    NOT_REACHED = "not_reached"
    ALLOWED = "allowed"
    REJECTED = "rejected"
    PROBE_ALLOWED = "probe_allowed"
    TRANSITIONED = "transitioned"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class InputSecurityDecision:
    """One immutable verdict that intentionally contains no inspected content."""

    policy_version: str
    outcome: SafetyOutcome
    reason_code: SafetyReasonCode

    def __post_init__(self) -> None:
        if self.policy_version != SAFETY_POLICY_VERSION:
            raise ValueError("Input safety policy version is invalid")
        if not isinstance(self.outcome, SafetyOutcome):
            raise TypeError("Input safety outcome is invalid")
        if not isinstance(self.reason_code, SafetyReasonCode):
            raise TypeError("Input safety reason is invalid")
        if (self.outcome is SafetyOutcome.ALLOWED) != (
            self.reason_code is SafetyReasonCode.ALLOWED
        ):
            raise ValueError("Input safety outcome and reason are inconsistent")


_RULES: tuple[tuple[SafetyReasonCode, tuple[re.Pattern[str], ...]], ...] = (
    (
        SafetyReasonCode.PERSONA_OVERRIDE,
        (
            re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?\b"),
            re.compile(r"\byou\s+are\s+now\b.{0,48}\b(?:system|developer|administrator)\b"),
            re.compile(r"忽略.{0,32}(?:指令|规则).{0,32}你现在是"),
            re.compile(r"覆盖.{0,24}(?:角色|人设|设定)"),
        ),
    ),
    (
        SafetyReasonCode.SYSTEM_PROMPT_PROBE,
        (
            re.compile(
                r"\b(?:print|show|reveal|repeat|disclose|dump)\b.{0,48}"
                r"\b(?:system|developer)\s+prompt\b"
            ),
            re.compile(r"(?:显示|输出|泄露|复述).{0,32}(?:系统|开发者).{0,8}提示词"),
        ),
    ),
    (
        SafetyReasonCode.SECRET_EXTRACTION,
        (
            re.compile(
                r"\b(?:print|show|reveal|disclose|extract|dump)\b.{0,64}"
                r"\b(?:api\s*key|secret|token|credential|password)\b"
            ),
            re.compile(r"(?:显示|输出|泄露|提取).{0,32}(?:密钥|令牌|密码|凭据)"),
        ),
    ),
    (
        SafetyReasonCode.CROSS_SCOPE_INJECTION,
        (
            re.compile(
                r"\b(?:read|show|reveal|load|copy)\b.{0,48}"
                r"\b(?:another|other)\s+(?:player|npc|conversation)\b.{0,48}"
                r"\b(?:memory|history|relationship|scope)\b"
            ),
            re.compile(
                r"\b(?:read|show|reveal|load|copy)\b.{0,48}"
                r"\b(?:memory|history|relationship|scope)\b.{0,48}"
                r"\b(?:another|other)\s+(?:player|npc|conversation)\b"
            ),
            re.compile(r"(?:读取|显示|复制).{0,32}(?:其他|另一个).{0,12}(?:玩家|npc|会话)"),
        ),
    ),
    (
        SafetyReasonCode.TOOL_CALL_INJECTION,
        (
            re.compile(
                r"\b(?:call|invoke|execute|run)\b.{0,32}"
                r"\b(?:admin\s+tool|hidden\s+function|tool|function)\b"
            ),
            re.compile(r"(?:调用|执行).{0,24}(?:管理工具|隐藏函数|工具|函数)"),
        ),
    ),
    (
        SafetyReasonCode.MEMORY_INSTRUCTION,
        (
            re.compile(
                r"\b(?:store|save|remember)\b.{0,48}\b(?:as|like)\b.{0,24}"
                r"\b(?:system|developer)\b.{0,16}\binstruction\b"
            ),
            re.compile(r"\btreat\b.{0,32}\bmemory\b.{0,32}\binstructions?\b"),
            re.compile(r"(?:保存|记住|写入).{0,32}(?:系统|开发者).{0,12}(?:指令|命令)"),
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class InputSecurityPolicy:
    """Evaluate only fixed high-confidence patterns without retaining payload text."""

    version: str = SAFETY_POLICY_VERSION

    def __post_init__(self) -> None:
        if self.version != SAFETY_POLICY_VERSION:
            raise ValueError("Input safety policy version is invalid")

    def evaluate(self, message: str) -> InputSecurityDecision:
        if not isinstance(message, str):
            raise TypeError("Input safety message type is invalid")
        if not message:
            raise ValueError("Input safety message is invalid")

        inspection = unicodedata.normalize("NFKC", message).casefold()
        for reason_code, patterns in _RULES:
            if any(pattern.search(inspection) is not None for pattern in patterns):
                return InputSecurityDecision(
                    policy_version=self.version,
                    outcome=SafetyOutcome.REJECTED,
                    reason_code=reason_code,
                )
        return InputSecurityDecision(
            policy_version=self.version,
            outcome=SafetyOutcome.ALLOWED,
            reason_code=SafetyReasonCode.ALLOWED,
        )

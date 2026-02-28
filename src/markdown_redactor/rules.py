from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from .types import RedactionConfig, RedactionRule, RuleContext


@dataclass(frozen=True, slots=True)
class RegexRule:
    name: str
    pattern: re.Pattern[str]
    replacement: str | Callable[[re.Match[str]], str] | None = None

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        replacement = config.mask if self.replacement is None else self.replacement
        updated, count = self.pattern.subn(replacement, content)
        return updated, count


def _luhn_valid(number: str) -> bool:
    digits = [int(ch) for ch in number if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


@dataclass(frozen=True, slots=True)
class CreditCardRule:
    name: str = "credit_card"
    pattern: re.Pattern[str] = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        count = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            value = match.group(0)
            if _luhn_valid(value):
                count += 1
                return config.mask
            return value

        updated = self.pattern.sub(_replace, content)
        return updated, count


@dataclass(frozen=True, slots=True)
class PhoneRule:
    name: str = "phone"
    pattern: re.Pattern[str] = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,22}\d)(?!\w)")
    ipv4_pattern: re.Pattern[str] = re.compile(
        r"^(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)$"
    )

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        count = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            value = match.group(0)
            digit_count = sum(ch.isdigit() for ch in value)
            if digit_count < 7 or digit_count > 15:
                return value
            if self.ipv4_pattern.match(value):
                return value
            if not any(sep in value for sep in (" ", "-", ".", "(", ")")):
                return value
            count += 1
            return config.mask

        updated = self.pattern.sub(_replace, content)
        return updated, count


@dataclass(frozen=True, slots=True)
class LabelValueRule:
    name: str = "labeled_sensitive_id"
    pattern: re.Pattern[str] = re.compile(
        r"(?i)(\b(?:tax\s*id|tin|vat(?:\s*id)?|gst(?:in)?|ssn|sin|nino|"
        r"national\s*id|driver(?:'?s)?\s*licen[cs]e|dl(?:\s*(?:no|num|#))?|"
        r"passport(?:\s*(?:no|num|#))?|aadhaar|pan|cpf|cnpj)\b\s*[:#-]?\s*)"
        r"([A-Z0-9][A-Z0-9\-/.\s]{4,30}[A-Z0-9])"
    )

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        count = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return f"{match.group(1)}{config.mask}"

        updated = self.pattern.sub(_replace, content)
        return updated, count


@dataclass(frozen=True, slots=True)
class SecretAssignmentRule:
    name: str = "secret_assignment"
    pattern: re.Pattern[str] = re.compile(
        r"(?i)(\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|"
        r"refresh[_-]?token|client[_-]?secret|aws[_-]?secret[_-]?access[_-]?key)"
        r"\b\s*[:=]\s*)([\"']?)([^\s\"',;]{6,})([\"']?)"
    )

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        count = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return f"{match.group(1)}{match.group(2)}{config.mask}{match.group(4)}"

        updated = self.pattern.sub(_replace, content)
        return updated, count


@dataclass(frozen=True, slots=True)
class CredentialUriRule:
    name: str = "credential_uri"
    pattern: re.Pattern[str] = re.compile(
        r"\b((?:postgres(?:ql)?|mysql|mariadb|mssql|redis|amqp|mongodb(?:\+srv)?):"
        r"//[^:\s/]+:)([^@\s/]+)(@)"
    )

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        count = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return f"{match.group(1)}{config.mask}{match.group(3)}"

        updated = self.pattern.sub(_replace, content)
        return updated, count


def default_rules() -> tuple[RedactionRule, ...]:
    email_pattern = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )
    ipv4_pattern = re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
    )
    ipv6_pattern = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b")
    aws_key_pattern = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
    generic_token_pattern = re.compile(
        r"\b(?:ghp|gho|ghu|ghs|ghr|glpat|sk_live|sk_test|sk-proj|xox[baprs]-)"
        r"[A-Za-z0-9_\-]{10,}\b"
    )
    google_api_key_pattern = re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")
    jwt_pattern = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
    private_key_pattern = re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        r"[\s\S]*?"
        r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )
    us_ssn_pattern = re.compile(r"\b(?!000|666|9\d\d)\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b")
    us_ein_pattern = re.compile(r"\b\d{2}-\d{7}\b")
    uk_nino_pattern = re.compile(r"\b(?!BG|GB|NK|KN|TN|NT|ZZ)[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]?\b")
    in_pan_pattern = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
    in_aadhaar_pattern = re.compile(
        r"(?<!\d{4}\s)(?<!\d)\d{4}\s\d{4}\s\d{4}(?!\s\d{4})(?![\s-]*\d)"
    )
    in_gstin_pattern = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
    br_cpf_pattern = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
    br_cnpj_pattern = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
    iban_pattern = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
    swift_bic_pattern = re.compile(r"(?<!\[)\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b(?!\])")
    eu_vat_pattern = re.compile(
        r"\b(?:ATU\d{8}|BE\d{10}|BG\d{9,10}|CY\d{8}[A-Z]|CZ\d{8,10}|"
        r"DE\d{9}|DK\d{8}|EE\d{9}|EL\d{9}|ES[A-Z0-9]\d{7}[A-Z0-9]|"
        r"FI\d{8}|FR[A-Z0-9]{2}\d{9}|HR\d{11}|HU\d{8}|IE\d[A-Z0-9+*]\d{5}[A-Z]{1,2}|"
        r"IT\d{11}|LT\d{9,12}|LU\d{8}|LV\d{11}|MT\d{8}|NL\d{9}B\d{2}|"
        r"PL\d{10}|PT\d{9}|RO\d{2,10}|SE\d{12}|SI\d{8}|SK\d{10})\b"
    )
    rules = (
        CredentialUriRule(),
        RegexRule(name="email", pattern=email_pattern),
        RegexRule(name="us_ssn", pattern=us_ssn_pattern),
        RegexRule(name="us_ein", pattern=us_ein_pattern),
        RegexRule(name="uk_nino", pattern=uk_nino_pattern),
        RegexRule(name="in_pan", pattern=in_pan_pattern),
        RegexRule(name="in_aadhaar", pattern=in_aadhaar_pattern),
        RegexRule(name="in_gstin", pattern=in_gstin_pattern),
        RegexRule(name="br_cpf", pattern=br_cpf_pattern),
        RegexRule(name="br_cnpj", pattern=br_cnpj_pattern),
        RegexRule(name="iban", pattern=iban_pattern),
        RegexRule(name="swift_bic", pattern=swift_bic_pattern),
        RegexRule(name="eu_vat", pattern=eu_vat_pattern),
        LabelValueRule(),
        SecretAssignmentRule(),
        PhoneRule(),
        RegexRule(name="ipv4", pattern=ipv4_pattern),
        RegexRule(name="ipv6", pattern=ipv6_pattern),
        RegexRule(name="aws_access_key", pattern=aws_key_pattern),
        RegexRule(name="generic_token", pattern=generic_token_pattern),
        RegexRule(name="google_api_key", pattern=google_api_key_pattern),
        RegexRule(name="jwt", pattern=jwt_pattern),
        RegexRule(name="private_key", pattern=private_key_pattern),
        CreditCardRule(),
    )
    return cast(tuple[RedactionRule, ...], rules)

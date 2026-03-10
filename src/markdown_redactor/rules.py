from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from .types import RedactionConfig, RedactionRule, RuleContext


def _replacement_value(value: str, config: RedactionConfig) -> str:
    if config.replacement_mode == "full":
        return config.mask

    if config.replacement_mode == "preserve_format":
        return "".join("X" if char.isalnum() else char for char in value)

    significant_positions = [index for index, char in enumerate(value) if char.isalnum()]
    if len(significant_positions) <= 4:
        return config.mask

    keep_positions = set(significant_positions[-4:])
    return "".join(
        char if (not char.isalnum() or index in keep_positions) else "X"
        for index, char in enumerate(value)
    )


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
        replacement = (
            (lambda match: _replacement_value(match.group(0), config))
            if self.replacement is None
            else self.replacement
        )
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
                return _replacement_value(value, config)
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
            return _replacement_value(value, config)

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
            return f"{match.group(1)}{_replacement_value(match.group(2), config)}"

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
            replacement = _replacement_value(match.group(3), config)
            return f"{match.group(1)}{match.group(2)}{replacement}{match.group(4)}"

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
            return f"{match.group(1)}{_replacement_value(match.group(2), config)}{match.group(3)}"

        updated = self.pattern.sub(_replace, content)
        return updated, count


_EMAIL_PATTERN = re.compile(r"(?<!://)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_IPV4_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
_IPV6_PATTERN = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b")
_AWS_KEY_PATTERN = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
_GENERIC_TOKEN_PATTERN = re.compile(
    r"\b(?:ghp|gho|ghu|ghs|ghr|glpat|sk_live|sk_test|sk-proj|xox[baprs]-)[A-Za-z0-9_\-]{10,}\b"
)
_GOOGLE_API_KEY_PATTERN = re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")
_JWT_PATTERN = re.compile(
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
)
_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"[\s\S]*?"
    r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
)
_US_SSN_PATTERN = re.compile(r"\b(?!000|666|9\d\d)\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b")
_US_EIN_PATTERN = re.compile(r"\b\d{2}-\d{7}\b")
_UK_NINO_PATTERN = re.compile(r"\b(?!BG|GB|NK|KN|TN|NT|ZZ)[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]?\b")
_IN_PAN_PATTERN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_IN_AADHAAR_PATTERN = re.compile(
    r"(?<!\d{4}\s)(?<!\d)\d{4}\s\d{4}\s\d{4}(?!\s\d{4})(?![\s-]*\d)"
)
_IN_GSTIN_PATTERN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
_BR_CPF_PATTERN = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
_BR_CNPJ_PATTERN = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
_IBAN_CC = (
    "AD|AE|AL|AT|AZ|BA|BE|BG|BH|BR|BY|CH|CR|CY|CZ|DE|DK|DO|EE|EG|ES|FI|FO|FR|GB|"
    "GE|GI|GL|GR|GT|HR|HU|IE|IL|IQ|IS|IT|JO|KW|KZ|LB|LC|LI|LT|LU|LV|MA|MC|MD|ME|"
    "MK|MR|MT|MU|NL|NO|PK|PL|PS|PT|QA|RO|RS|SA|SC|SE|SI|SK|SM|ST|SV|TL|TN|TR|UA|"
    "VA|VG|XK"
)
_IBAN_PATTERN = re.compile(rf"\b(?:{_IBAN_CC})\d{{2}}[A-Z0-9]{{11,30}}\b")
_SWIFT_BIC_PATTERN = re.compile(
    r"(?<!\[)\b[A-Z]{6}(?=[A-Z0-9]*\d)[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b(?!\])"
)
_EU_VAT_PATTERN = re.compile(
    r"\b(?:ATU\d{8}|BE\d{10}|BG\d{9,10}|CY\d{8}[A-Z]|CZ\d{8,10}|"
    r"DE\d{9}|DK\d{8}|EE\d{9}|EL\d{9}|ES[A-Z0-9]\d{7}[A-Z0-9]|"
    r"FI\d{8}|FR[A-Z0-9]{2}\d{9}|HR\d{11}|HU\d{8}|IE\d[A-Z0-9+*]\d{5}[A-Z]{1,2}|"
    r"IT\d{11}|LT\d{9,12}|LU\d{8}|LV\d{11}|MT\d{8}|NL\d{9}B\d{2}|"
    r"PL\d{10}|PT\d{9}|RO\d{2,10}|SE\d{12}|SI\d{8}|SK\d{10})\b"
)


def default_rules() -> tuple[RedactionRule, ...]:
    return cast(
        tuple[RedactionRule, ...],
        (
            CredentialUriRule(),
            RegexRule(name="email", pattern=_EMAIL_PATTERN),
            RegexRule(name="us_ssn", pattern=_US_SSN_PATTERN),
            RegexRule(name="us_ein", pattern=_US_EIN_PATTERN),
            RegexRule(name="uk_nino", pattern=_UK_NINO_PATTERN),
            RegexRule(name="in_pan", pattern=_IN_PAN_PATTERN),
            RegexRule(name="in_aadhaar", pattern=_IN_AADHAAR_PATTERN),
            RegexRule(name="in_gstin", pattern=_IN_GSTIN_PATTERN),
            RegexRule(name="br_cpf", pattern=_BR_CPF_PATTERN),
            RegexRule(name="br_cnpj", pattern=_BR_CNPJ_PATTERN),
            RegexRule(name="iban", pattern=_IBAN_PATTERN),
            RegexRule(name="swift_bic", pattern=_SWIFT_BIC_PATTERN),
            RegexRule(name="eu_vat", pattern=_EU_VAT_PATTERN),
            LabelValueRule(),
            SecretAssignmentRule(),
            PhoneRule(),
            RegexRule(name="ipv4", pattern=_IPV4_PATTERN),
            RegexRule(name="ipv6", pattern=_IPV6_PATTERN),
            RegexRule(name="aws_access_key", pattern=_AWS_KEY_PATTERN),
            RegexRule(name="generic_token", pattern=_GENERIC_TOKEN_PATTERN),
            RegexRule(name="google_api_key", pattern=_GOOGLE_API_KEY_PATTERN),
            RegexRule(name="jwt", pattern=_JWT_PATTERN),
            RegexRule(name="private_key", pattern=_PRIVATE_KEY_PATTERN),
            CreditCardRule(),
        ),
    )

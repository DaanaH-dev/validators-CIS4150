"""ISP and Logic Coverage tests for validators.card."""

import pytest

from validators.card import (
    amex,
    card_number,
    diners,
    discover,
    jcb,
    mastercard,
    mir,
    unionpay,
    visa,
)
from validators.utils import ValidationError


# ---------------------------------------------------------------------------
# Test Oracles
# ---------------------------------------------------------------------------
def assert_valid(result) -> None:
    """Assert strict boolean True for valid inputs."""
    assert result is True


def assert_invalid(result) -> None:
    """Assert falsy ValidationError object for invalid inputs."""
    assert not result
    assert isinstance(result, ValidationError)


ALL_VALIDATORS = [
    card_number,
    visa,
    mastercard,
    amex,
    unionpay,
    diners,
    jcb,
    discover,
    mir,
]

ISSUER_VALIDATORS = [
    visa,
    mastercard,
    amex,
    unionpay,
    diners,
    jcb,
    discover,
    mir,
]


# ---------------------------------------------------------------------------
# 1. ISP: Argument Type (ECC across all validators) + card_number Edge Cases
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("func", ALL_VALIDATORS, ids=lambda f: f.__name__)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(None, id="ISP-CARD-TYPE-NONE"),
        pytest.param(123, id="ISP-CARD-TYPE-INT"),
        pytest.param(4242424242424242, id="ISP-CARD-TYPE-VALID-LUHN-INT"),
        pytest.param(b"4242424242424242", id="ISP-CARD-TYPE-BYTES"),
        pytest.param(b"", id="ISP-CARD-TYPE-EMPTY-BYTES"),
        pytest.param("", id="ISP-CARD-TYPE-EMPTY-STR"),
    ],
)
def test_non_string_and_empty_argument_types(func, value):
    """Non-str argument types and empty strings must return ValidationError."""
    assert_invalid(func(value))


@pytest.mark.parametrize(
    "value, expected_valid",
    [
        # Luhn passes (str)
        pytest.param("4242424242424242", True, id="ISP-CARDNUM-LUHN-PASS-16"),
        pytest.param("0", True, id="ISP-CARDNUM-LUHN-PASS-SINGLE-ZERO"),
        pytest.param("42", True, id="ISP-CARDNUM-LUHN-PASS-2DIGIT"),
        # Luhn fails (str)
        pytest.param("4242424242424241", False, id="ISP-CARDNUM-LUHN-FAIL-16"),
        pytest.param("7", False, id="ISP-CARDNUM-LUHN-FAIL-SINGLE"),
        pytest.param("41", False, id="ISP-CARDNUM-LUHN-FAIL-2DIGIT"),
        # ValueError branch inside card_number (non-digit characters)
        pytest.param("424242424242424a", False, id="ISP-CARDNUM-NONDIGIT-ALPHA"),
        pytest.param("4242-4242-4242-4242", False, id="ISP-CARDNUM-NONDIGIT-HYPHEN"),
        pytest.param("4242 4242 4242 4242", False, id="ISP-CARDNUM-NONDIGIT-SPACE"),
        pytest.param("42.42", False, id="ISP-CARDNUM-NONDIGIT-DOT"),
    ],
)
def test_card_number_luhn_and_format(value, expected_valid):
    """Test card_number valid/invalid Luhn checksums and ValueError exception path."""
    result = card_number(value)
    assert_valid(result) if expected_valid else assert_invalid(result)


# ---------------------------------------------------------------------------
# 2. ISP (ACoC) + Logic Coverage (CACC) for Compound Predicates in Issuers
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "func, value, expected_valid",
    [
        # ---- visa (len=16, ^4) ----
        pytest.param(visa, "4242424242424242", True, id="LC-VISA-CACC-TTT_ISP-ACOC-PASS-OK"),
        pytest.param(visa, "4242424242424241", False, id="LC-VISA-CACC-FTT_ISP-ACOC-FAIL-OK"),
        pytest.param(visa, "400000000000006", False, id="LC-VISA-CACC-TFT_ISP-ACOC-PASS-WRONGLEN15"),
        pytest.param(visa, "5100000000000008", False, id="LC-VISA-CACC-TTF_ISP-ACOC-PASS-WRONGPFX"),
        pytest.param(visa, "400000000000005", False, id="ISP-VISA-ACOC-FAIL-WRONGLEN15"),
        pytest.param(visa, "5100000000000007", False, id="ISP-VISA-ACOC-FAIL-WRONGPFX"),
        pytest.param(visa, "510000000000000", False, id="ISP-VISA-FAIL-WRONGLEN-WRONGPFX"),
        # ---- mastercard (len=16, ^(5[1-5]|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)) ----
        pytest.param(mastercard, "5555555555554444", True, id="LC-MC-CACC-TTT_ISP-ACOC-PASS-OK"),
        pytest.param(mastercard, "5555555555554443", False, id="LC-MC-CACC-FTT_ISP-ACOC-FAIL-OK"),
        pytest.param(mastercard, "510000000000003", False, id="LC-MC-CACC-TFT_ISP-ACOC-PASS-WRONGLEN15"),
        pytest.param(mastercard, "4242424242424242", False, id="LC-MC-CACC-TTF_ISP-ACOC-PASS-WRONGPFX"),
        pytest.param(mastercard, "510000000000002", False, id="ISP-MC-ACOC-FAIL-WRONGLEN15"),
        pytest.param(mastercard, "4242424242424241", False, id="ISP-MC-ACOC-FAIL-WRONGPFX"),
        pytest.param(mastercard, "400000000000000", False, id="ISP-MC-FAIL-WRONGLEN-WRONGPFX"),
        # ---- amex (len=15, ^(34|37)) ----
        pytest.param(amex, "378282246310005", True, id="LC-AMEX-CACC-TTT_ISP-ACOC-PASS-OK"),
        pytest.param(amex, "378282246310004", False, id="LC-AMEX-CACC-FTT_ISP-ACOC-FAIL-OK"),
        pytest.param(amex, "34000000000000", False, id="LC-AMEX-CACC-TFT_ISP-ACOC-PASS-WRONGLEN14"),
        pytest.param(amex, "350000000000006", False, id="LC-AMEX-CACC-TTF_ISP-ACOC-PASS-WRONGPFX"),
        pytest.param(amex, "34000000000001", False, id="ISP-AMEX-ACOC-FAIL-WRONGLEN14"),
        pytest.param(amex, "350000000000005", False, id="ISP-AMEX-ACOC-FAIL-WRONGPFX"),
        pytest.param(amex, "4242424242424241", False, id="ISP-AMEX-FAIL-WRONGLEN-WRONGPFX"),
        # ---- unionpay (len=16, ^62) ----
        pytest.param(unionpay, "6200000000000005", True, id="LC-UP-CACC-TTT_ISP-ACOC-PASS-OK"),
        pytest.param(unionpay, "6200000000000004", False, id="LC-UP-CACC-FTT_ISP-ACOC-FAIL-OK"),
        pytest.param(unionpay, "620000000000000", False, id="LC-UP-CACC-TFT_ISP-ACOC-PASS-WRONGLEN15"),
        pytest.param(unionpay, "4242424242424242", False, id="LC-UP-CACC-TTF_ISP-ACOC-PASS-WRONGPFX"),
        pytest.param(unionpay, "620000000000001", False, id="ISP-UP-ACOC-FAIL-WRONGLEN15"),
        pytest.param(unionpay, "4242424242424241", False, id="ISP-UP-ACOC-FAIL-WRONGPFX"),
        pytest.param(unionpay, "400000000000000", False, id="ISP-UP-FAIL-WRONGLEN-WRONGPFX"),
        # ---- diners (len in {14, 16}, ^(30|36|38|39)) ----
        pytest.param(diners, "3056930009020004", True, id="LC-DINERS-CACC-TTT_ISP-ACOC-PASS-OK"),
        pytest.param(diners, "3056930009020003", False, id="LC-DINERS-CACC-FTT_ISP-ACOC-FAIL-OK"),
        pytest.param(diners, "300000000000007", False, id="LC-DINERS-CACC-TFT_ISP-ACOC-PASS-WRONGLEN15"),
        pytest.param(diners, "4242424242424242", False, id="LC-DINERS-CACC-TTF_ISP-ACOC-PASS-WRONGPFX"),
        pytest.param(diners, "300000000000006", False, id="ISP-DINERS-ACOC-FAIL-WRONGLEN15"),
        pytest.param(diners, "4242424242424241", False, id="ISP-DINERS-ACOC-FAIL-WRONGPFX"),
        pytest.param(diners, "400000000000000", False, id="ISP-DINERS-FAIL-WRONGLEN-WRONGPFX"),
        # ---- jcb (len=16, ^35) ----
        pytest.param(jcb, "3566002020360505", True, id="LC-JCB-CACC-TTT_ISP-ACOC-PASS-OK"),
        pytest.param(jcb, "3566002020360504", False, id="LC-JCB-CACC-FTT_ISP-ACOC-FAIL-OK"),
        pytest.param(jcb, "350000000000006", False, id="LC-JCB-CACC-TFT_ISP-ACOC-PASS-WRONGLEN15"),
        pytest.param(jcb, "4242424242424242", False, id="LC-JCB-CACC-TTF_ISP-ACOC-PASS-WRONGPFX"),
        pytest.param(jcb, "350000000000005", False, id="ISP-JCB-ACOC-FAIL-WRONGLEN15"),
        pytest.param(jcb, "4242424242424241", False, id="ISP-JCB-ACOC-FAIL-WRONGPFX"),
        pytest.param(jcb, "400000000000000", False, id="ISP-JCB-FAIL-WRONGLEN-WRONGPFX"),
        # ---- discover (len=16, ^(60|64|65)) ----
        pytest.param(discover, "6011111111111117", True, id="LC-DISC-CACC-TTT_ISP-ACOC-PASS-OK"),
        pytest.param(discover, "6011111111111116", False, id="LC-DISC-CACC-FTT_ISP-ACOC-FAIL-OK"),
        pytest.param(discover, "600000000000004", False, id="LC-DISC-CACC-TFT_ISP-ACOC-PASS-WRONGLEN15"),
        pytest.param(discover, "4242424242424242", False, id="LC-DISC-CACC-TTF_ISP-ACOC-PASS-WRONGPFX"),
        pytest.param(discover, "600000000000003", False, id="ISP-DISC-ACOC-FAIL-WRONGLEN15"),
        pytest.param(discover, "4242424242424241", False, id="ISP-DISC-ACOC-FAIL-WRONGPFX"),
        pytest.param(discover, "400000000000000", False, id="ISP-DISC-FAIL-WRONGLEN-WRONGPFX"),
        # ---- mir (len=16, ^(220[0-4])) ----
        pytest.param(mir, "2200123456789019", True, id="LC-MIR-CACC-TTT_ISP-ACOC-PASS-OK"),
        pytest.param(mir, "2200123456789018", False, id="LC-MIR-CACC-FTT_ISP-ACOC-FAIL-OK"),
        pytest.param(mir, "220000000000004", False, id="LC-MIR-CACC-TFT_ISP-ACOC-PASS-WRONGLEN15"),
        pytest.param(mir, "4242424242424242", False, id="LC-MIR-CACC-TTF_ISP-ACOC-PASS-WRONGPFX"),
        pytest.param(mir, "220000000000003", False, id="ISP-MIR-ACOC-FAIL-WRONGLEN15"),
        pytest.param(mir, "4242424242424241", False, id="ISP-MIR-ACOC-FAIL-WRONGPFX"),
        pytest.param(mir, "400000000000000", False, id="ISP-MIR-FAIL-WRONGLEN-WRONGPFX"),
    ],
)
def test_issuer_acoc_and_cacc(func, value, expected_valid):
    """Verify ACoC and CACC requirements for each issuer validator."""
    result = func(value)
    assert_valid(result) if expected_valid else assert_invalid(result)


# ---------------------------------------------------------------------------
# 3. Boundary & Regex Alternative Coverage
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "func, value, expected_valid",
    [
        # visa length upper boundary (17) and prefix boundary (3, 5)
        pytest.param(visa, "4000000000000002", True, id="BND-VISA-LEN16"),
        pytest.param(visa, "40000000000000006", False, id="BND-VISA-LEN17"),
        pytest.param(visa, "3500000000000009", False, id="BND-VISA-PFX35"),
        # mastercard BIN alternatives & boundaries (51-55, 2221-2720)
        pytest.param(mastercard, "5100000000000008", True, id="BND-MC-51-LOWER"),
        pytest.param(mastercard, "5500000000000004", True, id="BND-MC-55-UPPER"),
        pytest.param(mastercard, "5000000000000009", False, id="BND-MC-50-BELOW"),
        pytest.param(mastercard, "5600000000000003", False, id="BND-MC-56-ABOVE"),
        pytest.param(mastercard, "2221000000000009", True, id="BND-MC-2221-LOWER"),
        pytest.param(mastercard, "2220000000000000", False, id="BND-MC-2220-BELOW"),
        pytest.param(mastercard, "2230000000000008", True, id="BND-MC-223X"),
        pytest.param(mastercard, "2300000000000003", True, id="BND-MC-23XX"),
        pytest.param(mastercard, "2710000000000007", True, id="BND-MC-271X"),
        pytest.param(mastercard, "2720000000000005", True, id="BND-MC-2720-UPPER"),
        pytest.param(mastercard, "2721000000000004", False, id="BND-MC-2721-ABOVE"),
        pytest.param(mastercard, "51000000000000003", False, id="BND-MC-LEN17"),
        # amex alternatives (34, 37) and boundaries (33, 38, len 16)
        pytest.param(amex, "340000000000009", True, id="BND-AMEX-PFX34"),
        pytest.param(amex, "380000000000000", False, id="BND-AMEX-PFX38"),
        pytest.param(amex, "3400000000000000", False, id="BND-AMEX-LEN16"),
        # unionpay boundaries (61, 63, len 17)
        pytest.param(unionpay, "6100000000000006", False, id="BND-UP-PFX61"),
        pytest.param(unionpay, "6300000000000004", False, id="BND-UP-PFX63"),
        pytest.param(unionpay, "62000000000000000", False, id="BND-UP-LEN17"),
        # diners lengths {14, 16} + boundaries {13, 15, 17} + prefixes {30, 36, 38, 39}
        pytest.param(diners, "30000000000004", True, id="BND-DINERS-LEN14-PFX30"),
        pytest.param(diners, "36000000000008", True, id="BND-DINERS-LEN14-PFX36"),
        pytest.param(diners, "38000000000006", True, id="BND-DINERS-LEN14-PFX38"),
        pytest.param(diners, "39000000000005", True, id="BND-DINERS-LEN14-PFX39"),
        pytest.param(diners, "3600000000000008", True, id="BND-DINERS-LEN16-PFX36"),
        pytest.param(diners, "30000000000003", False, id="BND-DINERS-LEN14-FAILLUHN"),
        pytest.param(diners, "3000000000007", False, id="BND-DINERS-LEN13"),
        pytest.param(diners, "30000000000000007", False, id="BND-DINERS-LEN17"),
        pytest.param(diners, "35000000000009", False, id="BND-DINERS-LEN14-PFX35"),
        pytest.param(diners, "3700000000000007", False, id="BND-DINERS-LEN16-PFX37"),
        # jcb boundaries (34, 36, len 17)
        pytest.param(jcb, "3400000000000000", False, id="BND-JCB-PFX34"),
        pytest.param(jcb, "3600000000000008", False, id="BND-JCB-PFX36"),
        pytest.param(jcb, "35000000000000006", False, id="BND-JCB-LEN17"),
        # discover alternatives (60, 64, 65) and misses (62, 63, 66, len 17)
        pytest.param(discover, "6400000000000003", True, id="BND-DISC-PFX64"),
        pytest.param(discover, "6500000000000002", True, id="BND-DISC-PFX65"),
        pytest.param(discover, "6200000000000005", False, id="BND-DISC-PFX62"),
        pytest.param(discover, "6300000000000004", False, id="BND-DISC-PFX63"),
        pytest.param(discover, "6600000000000001", False, id="BND-DISC-PFX66"),
        pytest.param(discover, "60000000000000004", False, id="BND-DISC-LEN17"),
        # mir boundaries (2199, 2200, 2204, 2205, len 17)
        pytest.param(mir, "2200000000000004", True, id="BND-MIR-2200-LOWER"),
        pytest.param(mir, "2204000000000000", True, id="BND-MIR-2204-UPPER"),
        pytest.param(mir, "2199000000000007", False, id="BND-MIR-2199-BELOW"),
        pytest.param(mir, "2205000000000009", False, id="BND-MIR-2205-ABOVE"),
        pytest.param(mir, "22000000000000004", False, id="BND-MIR-LEN17"),
    ],
)
def test_issuer_boundaries(func, value, expected_valid):
    """Verify exact length and BIN/prefix boundaries for all issuers."""
    result = func(value)
    assert_valid(result) if expected_valid else assert_invalid(result)

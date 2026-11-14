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
        pytest.param(None, id="ISP type: None"),
        pytest.param(123, id="ISP type: int (small number)"),
        pytest.param(4242424242424242, id="ISP type: int (16-digit valid Luhn)"),
        pytest.param(b"4242424242424242", id="ISP type: bytes (non-empty)"),
        pytest.param(b"", id="ISP type: bytes (empty)"),
        pytest.param("", id="ISP type: str (empty)"),
    ],
)
def test_non_string_and_empty_argument_types(func, value):
    """Non-str argument types and empty strings must return ValidationError."""
    assert_invalid(func(value))


@pytest.mark.parametrize(
    "value, expected_valid",
    [
        # Luhn passes (str)
        pytest.param("4242424242424242", True, id="valid Luhn: 16 digits"),
        pytest.param("0", True, id="valid Luhn: single zero"),
        pytest.param("42", True, id="valid Luhn: 2 digits"),
        # Luhn fails (str)
        pytest.param("4242424242424241", False, id="invalid Luhn: 16 digits"),
        pytest.param("7", False, id="invalid Luhn: single digit"),
        pytest.param("41", False, id="invalid Luhn: 2 digits"),
        # ValueError branch inside card_number (non-digit characters)
        pytest.param("424242424242424a", False, id="non-digit char: letter"),
        pytest.param("4242-4242-4242-4242", False, id="non-digit char: hyphen"),
        pytest.param("4242 4242 4242 4242", False, id="non-digit char: space"),
        pytest.param("42.42", False, id="non-digit char: decimal dot"),
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
        # ---- visa ----
        pytest.param(visa, "4242424242424242", True, id="visa: valid card (CACC TTT, ACoC)"),
        pytest.param(visa, "4242424242424241", False, id="visa: fails Luhn (CACC FTT, ACoC)"),
        pytest.param(visa, "400000000000006", False, id="visa: wrong length 15 (CACC TFT, ACoC)"),
        pytest.param(visa, "5100000000000008", False, id="visa: wrong prefix 51 (CACC TTF, ACoC)"),
        pytest.param(visa, "400000000000005", False, id="visa: fails Luhn and wrong length 15 (ACoC)"),
        pytest.param(visa, "5100000000000007", False, id="visa: fails Luhn and wrong prefix 51 (ACoC)"),
        pytest.param(visa, "510000000000000", False, id="visa: fails Luhn, wrong length 15, wrong prefix 51"),
        # ---- mastercard ----
        pytest.param(mastercard, "5555555555554444", True, id="mastercard: valid card (CACC TTT, ACoC)"),
        pytest.param(mastercard, "5555555555554443", False, id="mastercard: fails Luhn (CACC FTT, ACoC)"),
        pytest.param(mastercard, "510000000000003", False, id="mastercard: wrong length 15 (CACC TFT, ACoC)"),
        pytest.param(mastercard, "4242424242424242", False, id="mastercard: wrong prefix 42 (CACC TTF, ACoC)"),
        pytest.param(mastercard, "510000000000002", False, id="mastercard: fails Luhn and wrong length 15 (ACoC)"),
        pytest.param(mastercard, "4242424242424241", False, id="mastercard: fails Luhn and wrong prefix 42 (ACoC)"),
        pytest.param(mastercard, "400000000000000", False, id="mastercard: fails Luhn, wrong length 15, wrong prefix 40"),
        # ---- amex ----
        pytest.param(amex, "378282246310005", True, id="amex: valid card (CACC TTT, ACoC)"),
        pytest.param(amex, "378282246310004", False, id="amex: fails Luhn (CACC FTT, ACoC)"),
        pytest.param(amex, "34000000000000", False, id="amex: wrong length 14 (CACC TFT, ACoC)"),
        pytest.param(amex, "350000000000006", False, id="amex: wrong prefix 35 (CACC TTF, ACoC)"),
        pytest.param(amex, "34000000000001", False, id="amex: fails Luhn and wrong length 14 (ACoC)"),
        pytest.param(amex, "350000000000005", False, id="amex: fails Luhn and wrong prefix 35 (ACoC)"),
        pytest.param(amex, "4242424242424241", False, id="amex: fails Luhn, wrong length 16, wrong prefix 42"),
        # ---- unionpay ----
        pytest.param(unionpay, "6200000000000005", True, id="unionpay: valid card (CACC TTT, ACoC)"),
        pytest.param(unionpay, "6200000000000004", False, id="unionpay: fails Luhn (CACC FTT, ACoC)"),
        pytest.param(unionpay, "620000000000000", False, id="unionpay: wrong length 15 (CACC TFT, ACoC)"),
        pytest.param(unionpay, "4242424242424242", False, id="unionpay: wrong prefix 42 (CACC TTF, ACoC)"),
        pytest.param(unionpay, "620000000000001", False, id="unionpay: fails Luhn and wrong length 15 (ACoC)"),
        pytest.param(unionpay, "4242424242424241", False, id="unionpay: fails Luhn and wrong prefix 42 (ACoC)"),
        pytest.param(unionpay, "400000000000000", False, id="unionpay: fails Luhn, wrong length 15, wrong prefix 40"),
        # ---- diners ----
        pytest.param(diners, "3056930009020004", True, id="diners: valid card (CACC TTT, ACoC)"),
        pytest.param(diners, "3056930009020003", False, id="diners: fails Luhn (CACC FTT, ACoC)"),
        pytest.param(diners, "300000000000007", False, id="diners: wrong length 15 (CACC TFT, ACoC)"),
        pytest.param(diners, "4242424242424242", False, id="diners: wrong prefix 42 (CACC TTF, ACoC)"),
        pytest.param(diners, "300000000000006", False, id="diners: fails Luhn and wrong length 15 (ACoC)"),
        pytest.param(diners, "4242424242424241", False, id="diners: fails Luhn and wrong prefix 42 (ACoC)"),
        pytest.param(diners, "400000000000000", False, id="diners: fails Luhn, wrong length 15, wrong prefix 40"),
        # ---- jcb ----
        pytest.param(jcb, "3566002020360505", True, id="jcb: valid card (CACC TTT, ACoC)"),
        pytest.param(jcb, "3566002020360504", False, id="jcb: fails Luhn (CACC FTT, ACoC)"),
        pytest.param(jcb, "350000000000006", False, id="jcb: wrong length 15 (CACC TFT, ACoC)"),
        pytest.param(jcb, "4242424242424242", False, id="jcb: wrong prefix 42 (CACC TTF, ACoC)"),
        pytest.param(jcb, "350000000000005", False, id="jcb: fails Luhn and wrong length 15 (ACoC)"),
        pytest.param(jcb, "4242424242424241", False, id="jcb: fails Luhn and wrong prefix 42 (ACoC)"),
        pytest.param(jcb, "400000000000000", False, id="jcb: fails Luhn, wrong length 15, wrong prefix 40"),
        # ---- discover ----
        pytest.param(discover, "6011111111111117", True, id="discover: valid card (CACC TTT, ACoC)"),
        pytest.param(discover, "6011111111111116", False, id="discover: fails Luhn (CACC FTT, ACoC)"),
        pytest.param(discover, "600000000000004", False, id="discover: wrong length 15 (CACC TFT, ACoC)"),
        pytest.param(discover, "4242424242424242", False, id="discover: wrong prefix 42 (CACC TTF, ACoC)"),
        pytest.param(discover, "600000000000003", False, id="discover: fails Luhn and wrong length 15 (ACoC)"),
        pytest.param(discover, "4242424242424241", False, id="discover: fails Luhn and wrong prefix 42 (ACoC)"),
        pytest.param(discover, "400000000000000", False, id="discover: fails Luhn, wrong length 15, wrong prefix 40"),
        # ---- mir ----
        pytest.param(mir, "2200123456789019", True, id="mir: valid card (CACC TTT, ACoC)"),
        pytest.param(mir, "2200123456789018", False, id="mir: fails Luhn (CACC FTT, ACoC)"),
        pytest.param(mir, "220000000000004", False, id="mir: wrong length 15 (CACC TFT, ACoC)"),
        pytest.param(mir, "4242424242424242", False, id="mir: wrong prefix 42 (CACC TTF, ACoC)"),
        pytest.param(mir, "220000000000003", False, id="mir: fails Luhn and wrong length 15 (ACoC)"),
        pytest.param(mir, "4242424242424241", False, id="mir: fails Luhn and wrong prefix 42 (ACoC)"),
        pytest.param(mir, "400000000000000", False, id="mir: fails Luhn, wrong length 15, wrong prefix 40"),
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
        # visa length upper boundary and prefix boundary
        pytest.param(visa, "4000000000000002", True, id="visa: valid length 16"),
        pytest.param(visa, "40000000000000006", False, id="visa: wrong length 17 (too long)"),
        pytest.param(visa, "3500000000000009", False, id="visa: wrong prefix 35"),
        # mastercard BIN alternatives and boundaries
        pytest.param(mastercard, "5100000000000008", True, id="mastercard: prefix 51 lower bound (valid)"),
        pytest.param(mastercard, "5500000000000004", True, id="mastercard: prefix 55 upper bound (valid)"),
        pytest.param(mastercard, "5000000000000009", False, id="mastercard: prefix 50 below range (invalid)"),
        pytest.param(mastercard, "5600000000000003", False, id="mastercard: prefix 56 above range (invalid)"),
        pytest.param(mastercard, "2221000000000009", True, id="mastercard: prefix 2221 lower bound (valid)"),
        pytest.param(mastercard, "2220000000000000", False, id="mastercard: prefix 2220 below range (invalid)"),
        pytest.param(mastercard, "2230000000000008", True, id="mastercard: prefix 2230 mid-range (valid)"),
        pytest.param(mastercard, "2300000000000003", True, id="mastercard: prefix 2300 mid-range (valid)"),
        pytest.param(mastercard, "2710000000000007", True, id="mastercard: prefix 2710 mid-range (valid)"),
        pytest.param(mastercard, "2720000000000005", True, id="mastercard: prefix 2720 upper bound (valid)"),
        pytest.param(mastercard, "2721000000000004", False, id="mastercard: prefix 2721 above range (invalid)"),
        pytest.param(mastercard, "51000000000000003", False, id="mastercard: wrong length 17 (too long)"),
        # amex alternatives and boundaries
        pytest.param(amex, "340000000000009", True, id="amex: valid prefix 34"),
        pytest.param(amex, "380000000000000", False, id="amex: wrong prefix 38"),
        pytest.param(amex, "3400000000000000", False, id="amex: wrong length 16 (too long)"),
        # unionpay boundaries
        pytest.param(unionpay, "6100000000000006", False, id="unionpay: wrong prefix 61 (below 62)"),
        pytest.param(unionpay, "6300000000000004", False, id="unionpay: wrong prefix 63 (above 62)"),
        pytest.param(unionpay, "62000000000000000", False, id="unionpay: wrong length 17 (too long)"),
        # diners lengths, boundaries, and prefixes
        pytest.param(diners, "30000000000004", True, id="diners: valid length 14 with prefix 30"),
        pytest.param(diners, "36000000000008", True, id="diners: valid length 14 with prefix 36"),
        pytest.param(diners, "38000000000006", True, id="diners: valid length 14 with prefix 38"),
        pytest.param(diners, "39000000000005", True, id="diners: valid length 14 with prefix 39"),
        pytest.param(diners, "3600000000000008", True, id="diners: valid length 16 with prefix 36"),
        pytest.param(diners, "30000000000003", False, id="diners: length 14 failing Luhn (invalid)"),
        pytest.param(diners, "3000000000007", False, id="diners: wrong length 13 (too short)"),
        pytest.param(diners, "30000000000000007", False, id="diners: wrong length 17 (too long)"),
        pytest.param(diners, "35000000000009", False, id="diners: length 14 wrong prefix 35"),
        pytest.param(diners, "3700000000000007", False, id="diners: length 16 wrong prefix 37"),
        # jcb boundaries
        pytest.param(jcb, "3400000000000000", False, id="jcb: wrong prefix 34 (below 35)"),
        pytest.param(jcb, "3600000000000008", False, id="jcb: wrong prefix 36 (above 35)"),
        pytest.param(jcb, "35000000000000006", False, id="jcb: wrong length 17 (too long)"),
        # discover alternatives and misses
        pytest.param(discover, "6400000000000003", True, id="discover: valid prefix 64"),
        pytest.param(discover, "6500000000000002", True, id="discover: valid prefix 65"),
        pytest.param(discover, "6200000000000005", False, id="discover: wrong prefix 62"),
        pytest.param(discover, "6300000000000004", False, id="discover: wrong prefix 63"),
        pytest.param(discover, "6600000000000001", False, id="discover: wrong prefix 66"),
        pytest.param(discover, "60000000000000004", False, id="discover: wrong length 17 (too long)"),
        # mir boundaries
        pytest.param(mir, "2200000000000004", True, id="mir: prefix 2200 lower bound (valid)"),
        pytest.param(mir, "2204000000000000", True, id="mir: prefix 2204 upper bound (valid)"),
        pytest.param(mir, "2199000000000007", False, id="mir: prefix 2199 below range (invalid)"),
        pytest.param(mir, "2205000000000009", False, id="mir: prefix 2205 above range (invalid)"),
        pytest.param(mir, "22000000000000004", False, id="mir: wrong length 17 (too long)"),
    ],
)
def test_issuer_boundaries(func, value, expected_valid):
    """Verify exact length and BIN/prefix boundaries for all issuers."""
    result = func(value)
    assert_valid(result) if expected_valid else assert_invalid(result)
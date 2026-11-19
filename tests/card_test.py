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

_BYTES_LUHN_TRUE_XFAIL = pytest.mark.xfail(
    raises=AssertionError,
    strict=True,
    reason=(
        "Defect in validators.card.card_number: map(int, bytes) converts ASCII "
        "byte values into ints, allowing bytes whose ASCII Luhn sum % 10 == 0 "
        "to return True instead of ValidationError."
    ),
)


def _assert_result(result, expected_valid: bool) -> None:
    if expected_valid:
        assert result is True
    else:
        assert isinstance(result, ValidationError)
        assert bool(result) is False


# ===========================================================================
# 1. Input Space Partitioning (ISP) - Section 2.3 & Table 2
# ===========================================================================


@pytest.mark.parametrize(
    ("func", "value", "expected_valid"),
    [
        # Table 2: All validators -> Argument type (str; None; int; bytes)
        pytest.param(card_number, "4242424242424242", True, id="card_number-str_valid"),
        pytest.param(card_number, None, False, id="card_number-none"),
        pytest.param(card_number, 4242424242424242, False, id="card_number-int"),
        pytest.param(card_number, b"4242424242424242", False, id="card_number-bytes"),
        pytest.param(visa, "4242424242424242", True, id="visa-str_valid"),
        pytest.param(visa, None, False, id="visa-none"),
        pytest.param(visa, 123, False, id="visa-int"),
        pytest.param(visa, b"4242424242424242", False, id="visa-bytes"),
        pytest.param(mastercard, "5555555555554444", True, id="mastercard-str_valid"),
        pytest.param(mastercard, None, False, id="mastercard-none"),
        pytest.param(mastercard, 123, False, id="mastercard-int"),
        pytest.param(mastercard, b"5555555555554444", False, id="mastercard-bytes"),
        pytest.param(amex, "378282246310005", True, id="amex-str_valid"),
        pytest.param(amex, None, False, id="amex-none"),
        pytest.param(amex, 123, False, id="amex-int"),
        pytest.param(amex, b"378282246310005", False, id="amex-bytes"),
        pytest.param(unionpay, "6200000000000005", True, id="unionpay-str_valid"),
        pytest.param(unionpay, None, False, id="unionpay-none"),
        pytest.param(unionpay, 123, False, id="unionpay-int"),
        pytest.param(unionpay, b"6200000000000005", False, id="unionpay-bytes"),
        pytest.param(diners, "3056930009020004", True, id="diners-str_valid"),
        pytest.param(diners, None, False, id="diners-none"),
        pytest.param(diners, 123, False, id="diners-int"),
        pytest.param(diners, b"3056930009020004", False, id="diners-bytes"),
        pytest.param(jcb, "3566002020360505", True, id="jcb-str_valid"),
        pytest.param(jcb, None, False, id="jcb-none"),
        pytest.param(jcb, 123, False, id="jcb-int"),
        pytest.param(jcb, b"3566002020360505", False, id="jcb-bytes"),
        pytest.param(discover, "6011111111111117", True, id="discover-str_valid"),
        pytest.param(discover, None, False, id="discover-none"),
        pytest.param(discover, 123, False, id="discover-int"),
        pytest.param(discover, b"6011111111111117", False, id="discover-bytes"),
        pytest.param(mir, "2200123456789019", True, id="mir-str_valid"),
        pytest.param(mir, None, False, id="mir-none"),
        pytest.param(mir, 123, False, id="mir-int"),
        pytest.param(mir, b"2200123456789019", False, id="mir-bytes"),
    ],
)
def test_all_card_validators_argument_types(func, value, expected_valid: bool) -> None:
    """TR-ISP-TYPE: Verify str, None, int, and bytes across all card validators."""
    _assert_result(func(value), expected_valid)


@pytest.mark.parametrize(
    ("value", "expected_valid"),
    [
        # card_number -> ACoC (<= 20 tests)
        # Table 2 characteristic: Luhn checksum (Passes; fails) + emptiness/non-digits
        pytest.param("", False, id="str-empty"),
        pytest.param("0", True, id="str-single_zero_luhn_pass"),
        pytest.param("5", False, id="str-single_nonzero_luhn_fail"),
        pytest.param("18", True, id="str-two_digits_luhn_pass"),
        pytest.param("81", False, id="str-two_digits_luhn_fail"),
        pytest.param("4242424242424242", True, id="str-16_digits_luhn_pass"),
        pytest.param("4242424242424241", False, id="str-16_digits_luhn_fail"),
        pytest.param("424242424242424a", False, id="str-contains_letter"),
        pytest.param("4242-4242-4242-4242", False, id="str-contains_hyphens"),
        pytest.param("4242 4242 4242 4242", False, id="str-contains_spaces"),
        pytest.param(None, False, id="none"),
        pytest.param(123, False, id="int"),
        pytest.param(b"4242424242424242", False, id="bytes-luhn_fail"),
    ],
)
def test_card_number_isp_acoc(value, expected_valid: bool) -> None:
    """TR-ISP-CARD-NUMBER-ACoC: All feasible blocks/combinations for card_number."""
    _assert_result(card_number(value), expected_valid)


# Table 2: amex, diners, visa -> Length and prefix x Luhn checksum (2 x 2 x 2 = 8 <= 20 -> ACoC)
@pytest.mark.parametrize(
    ("func", "value", "expected_valid"),
    [
        # visa: Luhn x Length (16) x Prefix (^4)
        pytest.param(visa, "4242424242424242", True, id="visa-luhn_pass-len_valid-prefix_valid"),
        pytest.param(visa, "5000000000000009", False, id="visa-luhn_pass-len_valid-prefix_wrong"),
        pytest.param(visa, "400000000000006", False, id="visa-luhn_pass-len_wrong-prefix_valid"),
        pytest.param(visa, "550000000000004", False, id="visa-luhn_pass-len_wrong-prefix_wrong"),
        pytest.param(visa, "4242424242424241", False, id="visa-luhn_fail-len_valid-prefix_valid"),
        pytest.param(visa, "5000000000000008", False, id="visa-luhn_fail-len_valid-prefix_wrong"),
        pytest.param(visa, "400000000000005", False, id="visa-luhn_fail-len_wrong-prefix_valid"),
        pytest.param(visa, "550000000000003", False, id="visa-luhn_fail-len_wrong-prefix_wrong"),
        # amex: Luhn x Length (15) x Prefix (^(34|37))
        pytest.param(amex, "378282246310005", True, id="amex-luhn_pass-len_valid-prefix_valid"),
        pytest.param(amex, "350000000000006", False, id="amex-luhn_pass-len_valid-prefix_wrong"),
        pytest.param(amex, "3400000000000000", False, id="amex-luhn_pass-len_wrong-prefix_valid"),
        pytest.param(amex, "4242424242424242", False, id="amex-luhn_pass-len_wrong-prefix_wrong"),
        pytest.param(amex, "378282246310004", False, id="amex-luhn_fail-len_valid-prefix_valid"),
        pytest.param(amex, "350000000000005", False, id="amex-luhn_fail-len_valid-prefix_wrong"),
        pytest.param(amex, "3400000000000001", False, id="amex-luhn_fail-len_wrong-prefix_valid"),
        pytest.param(amex, "4242424242424241", False, id="amex-luhn_fail-len_wrong-prefix_wrong"),
        # diners: Luhn x Length ({14, 16}) x Prefix (^(30|36|38|39))
        pytest.param(diners, "3056930009020004", True, id="diners-luhn_pass-len_valid-prefix_valid"),
        pytest.param(diners, "3100000000000003", False, id="diners-luhn_pass-len_valid-prefix_wrong"),
        pytest.param(diners, "300000000000007", False, id="diners-luhn_pass-len_wrong-prefix_valid"),
        pytest.param(diners, "378282246310005", False, id="diners-luhn_pass-len_wrong-prefix_wrong"),
        pytest.param(diners, "3056930009020003", False, id="diners-luhn_fail-len_valid-prefix_valid"),
        pytest.param(diners, "3100000000000002", False, id="diners-luhn_fail-len_valid-prefix_wrong"),
        pytest.param(diners, "300000000000006", False, id="diners-luhn_fail-len_wrong-prefix_valid"),
        pytest.param(diners, "378282246310004", False, id="diners-luhn_fail-len_wrong-prefix_wrong"),
    ],
)
def test_table2_issuers_isp_acoc(func, value: str, expected_valid: bool) -> None:
    """TR-ISP-ISSUERS-ACoC: All combinations of Luhn, length, and prefix for amex/diners/visa."""
    _assert_result(func(value), expected_valid)


# ===========================================================================
# 2. Logic Coverage (PC, CC, CACC) - Section 2.4
# ===========================================================================


@pytest.mark.parametrize(
    ("value", "expected_valid"),
    [
        # Predicate 1 (card_number): if not value
        pytest.param("", False, id="empty_true"),
        # Predicate 2 (card_number): ValueError exception vs normal return
        pytest.param("424242424242424a", False, id="value_error_raised_non_digit"),
        # Predicate 3 (card_number): (odd_sum + even_sum) % 10 == 0
        pytest.param("4242424242424242", True, id="luhn_mod10_true"),
        pytest.param("4242424242424241", False, id="luhn_mod10_false"),
    ],
)
def test_card_number_logic_coverage(value: str, expected_valid: bool) -> None:
    """TR-LC-CARD-NUMBER: PC/CC for empty check, ValueError branch, and Luhn predicate."""
    _assert_result(card_number(value), expected_valid)


# Compound Predicate for all 8 card issuers:
#   P = card_number(value) and len_check(value) and pattern.match(value)
#
# Clauses:
#   c1: bool(card_number(value))       [Luhn checksum passes]
#   c2: len(value) == L (or in {14,16}) [Issuer-specific length]
#   c3: bool(pattern.match(value))     [Issuer-specific BIN prefix]
#
# Truth Table (8 rows):
#   Row 1: c1=T, c2=T, c3=T -> P=T
#   Row 2: c1=T, c2=T, c3=F -> P=F
#   Row 3: c1=T, c2=F, c3=T -> P=F  (c3 short-circuited by c2=F)
#   Row 4: c1=T, c2=F, c3=F -> P=F  (c3 short-circuited by c2=F)
#   Row 5: c1=F, c2=T, c3=T -> P=F  (c2, c3 short-circuited by c1=F)
#   Row 6: c1=F, c2=T, c3=F -> P=F  (c2, c3 short-circuited by c1=F)
#   Row 7: c1=F, c2=F, c3=T -> P=F  (c2, c3 short-circuited by c1=F)
#   Row 8: c1=F, c2=F, c3=F -> P=F  (c2, c3 short-circuited by c1=F)
#
# CACC pairs:
#   - Active c1 (c2=T, c3=T): Row 1 vs Row 5
#   - Active c2 (c1=T, c3=T): Row 1 vs Row 3
#   - Active c3 (c1=T, c2=T): Row 1 vs Row 2
@pytest.mark.parametrize(
    ("func", "value", "expected_valid"),
    [
        # visa
        pytest.param(visa, "4242424242424242", True, id="visa-row1-luhn_true-len_true-prefix_true"),
        pytest.param(visa, "5000000000000009", False, id="visa-row2-luhn_true-len_true-prefix_false"),
        pytest.param(visa, "400000000000006", False, id="visa-row3-luhn_true-len_false-prefix_true"),
        pytest.param(visa, "4242424242424241", False, id="visa-row5-luhn_false-len_true-prefix_true"),
        # mastercard
        pytest.param(mastercard, "5555555555554444", True, id="mastercard-row1-luhn_true-len_true-prefix_true"),
        pytest.param(mastercard, "5000000000000009", False, id="mastercard-row2-luhn_true-len_true-prefix_false"),
        pytest.param(mastercard, "550000000000004", False, id="mastercard-row3-luhn_true-len_false-prefix_true"),
        pytest.param(mastercard, "5555555555554443", False, id="mastercard-row5-luhn_false-len_true-prefix_true"),
        # amex
        pytest.param(amex, "378282246310005", True, id="amex-row1-luhn_true-len_true-prefix_true"),
        pytest.param(amex, "350000000000006", False, id="amex-row2-luhn_true-len_true-prefix_false"),
        pytest.param(amex, "3400000000000000", False, id="amex-row3-luhn_true-len_false-prefix_true"),
        pytest.param(amex, "378282246310004", False, id="amex-row5-luhn_false-len_true-prefix_true"),
        # unionpay
        pytest.param(unionpay, "6200000000000005", True, id="unionpay-row1-luhn_true-len_true-prefix_true"),
        pytest.param(unionpay, "6100000000000006", False, id="unionpay-row2-luhn_true-len_true-prefix_false"),
        pytest.param(unionpay, "620000000000000", False, id="unionpay-row3-luhn_true-len_false-prefix_true"),
        pytest.param(unionpay, "6200000000000004", False, id="unionpay-row5-luhn_false-len_true-prefix_true"),
        # diners
        pytest.param(diners, "3056930009020004", True, id="diners-row1-luhn_true-len_true-prefix_true"),
        pytest.param(diners, "3100000000000003", False, id="diners-row2-luhn_true-len_true-prefix_false"),
        pytest.param(diners, "300000000000007", False, id="diners-row3-luhn_true-len_false-prefix_true"),
        pytest.param(diners, "3056930009020003", False, id="diners-row5-luhn_false-len_true-prefix_true"),
        # jcb
        pytest.param(jcb, "3566002020360505", True, id="jcb-row1-luhn_true-len_true-prefix_true"),
        pytest.param(jcb, "3400000000000000", False, id="jcb-row2-luhn_true-len_true-prefix_false"),
        pytest.param(jcb, "350000000000006", False, id="jcb-row3-luhn_true-len_false-prefix_true"),
        pytest.param(jcb, "3566002020360504", False, id="jcb-row5-luhn_false-len_true-prefix_true"),
        # discover
        pytest.param(discover, "6011111111111117", True, id="discover-row1-luhn_true-len_true-prefix_true"),
        pytest.param(discover, "5900000000000000", False, id="discover-row2-luhn_true-len_true-prefix_false"),
        pytest.param(discover, "600000000000004", False, id="discover-row3-luhn_true-len_false-prefix_true"),
        pytest.param(discover, "6011111111111116", False, id="discover-row5-luhn_false-len_true-prefix_true"),
        # mir
        pytest.param(mir, "2200123456789019", True, id="mir-row1-luhn_true-len_true-prefix_true"),
        pytest.param(mir, "2205000000000009", False, id="mir-row2-luhn_true-len_true-prefix_false"),
        pytest.param(mir, "220000000000004", False, id="mir-row3-luhn_true-len_false-prefix_true"),
        pytest.param(mir, "2200123456789018", False, id="mir-row5-luhn_false-len_true-prefix_true"),
    ],
)
def test_all_issuers_compound_predicate_cacc(
    func, value: str, expected_valid: bool
) -> None:
    """TR-LC-ISSUERS: PC, CC, and CACC for `card_number and len_check and pattern.match`."""
    _assert_result(func(value), expected_valid)


@pytest.mark.parametrize(
    ("value", "expected_valid"),
    [
        # Remaining short-circuited rows (Rows 4, 6, 7, 8) for complete 8-row coverage
        pytest.param("550000000000004", False, id="row4-luhn_true-len_false-prefix_false"),
        pytest.param("5000000000000008", False, id="row6-luhn_false-len_true-prefix_false"),
        pytest.param("400000000000005", False, id="row7-luhn_false-len_false-prefix_true"),
        pytest.param("550000000000003", False, id="row8-luhn_false-len_false-prefix_false"),
    ],
)
def test_visa_truth_table_short_circuit_rows(value: str, expected_valid: bool) -> None:
    """TR-LC-VISA-TT: Completes all 8 truth-table combinations including short-circuited rows."""
    _assert_result(visa(value), expected_valid)


# ===========================================================================
# 3. Branch Coverage, Mutation Testing & ValidationError Contract - Sec 2.1/2.2
# ===========================================================================


@pytest.mark.parametrize(
    ("func", "bad_input"),
    [
        pytest.param(card_number, None, id="card_number-none"),
        pytest.param(card_number, 123, id="card_number-int"),
        pytest.param(card_number, 12.34, id="card_number-float"),
        pytest.param(card_number, b"4242424242424242", id="card_number-bytes_luhn_fail"),
        pytest.param(
            card_number,
            b"4242424242424240",
            id="card_number-bytes_ascii_luhn_pass_16digit",
            marks=_BYTES_LUHN_TRUE_XFAIL,
        ),
        pytest.param(
            card_number,
            b"22",
            id="card_number-bytes_ascii_luhn_pass_2digit",
            marks=_BYTES_LUHN_TRUE_XFAIL,
        ),
        pytest.param(card_number, [], id="card_number-empty_list"),
        pytest.param(card_number, {}, id="card_number-empty_dict"),
        pytest.param(visa, None, id="visa-none"),
        pytest.param(visa, 4242424242424242, id="visa-int"),
        pytest.param(visa, b"4242424242424240", id="visa-bytes_luhn_true_regex_type_error"),
        pytest.param(mastercard, b"5555555555554444", id="mastercard-bytes"),
        pytest.param(amex, b"378282246310005", id="amex-bytes"),
        pytest.param(unionpay, b"6200000000000005", id="unionpay-bytes"),
        pytest.param(diners, b"3056930009020004", id="diners-bytes"),
        pytest.param(jcb, b"3566002020360505", id="jcb-bytes"),
        pytest.param(discover, b"6011111111111117", id="discover-bytes"),
        pytest.param(mir, b"2200123456789019", id="mir-bytes"),
    ],
)
def test_invalid_types_return_validation_error(func, bad_input) -> None:
    """Confirm decorator-caught/falsy non-str inputs return falsy ValidationError."""
    result = func(bad_input)
    _assert_result(result, False)
    assert result.func.__name__ == func.__name__


@pytest.mark.parametrize(
    ("value", "expected_valid"),
    [
        # Luhn slice / carry / modulo mutation killers
        pytest.param("0000000000000000", True, id="all_zeros"),
        pytest.param("4000000000000002", True, id="even_len_ends_only"),
        pytest.param("0400000000000006", True, id="even_len_odd_positions_only"),
        pytest.param("400000000000006", True, id="odd_len_15_first_and_last"),
        pytest.param("18", True, id="two_digit_valid_18"),
        pytest.param("81", False, id="two_digit_swapped_81"),
        pytest.param("91", True, id="divmod_carry_valid_91"),
        pytest.param("92", False, id="divmod_carry_invalid_92"),
        pytest.param("+4242424242424242", False, id="leading_plus_sign"),
        pytest.param("-4242424242424242", False, id="leading_minus_sign"),
        pytest.param(" 4242424242424242", False, id="leading_space"),
        pytest.param("4242424242424242 ", False, id="trailing_space"),
        pytest.param("4242424242424242\n", False, id="trailing_newline"),
    ],
)
def test_card_number_luhn_boundaries_and_mutations(
    value: str, expected_valid: bool
) -> None:
    """Kills slice-step, doubling, divmod, modulo, and sign mutants in card_number."""
    _assert_result(card_number(value), expected_valid)


@pytest.mark.parametrize(
    ("func", "value"),
    [
        # visa (prefix ^4, len 16)
        pytest.param(visa, "4000000000000002", id="visa-prefix_4000_min"),
        pytest.param(visa, "4999999999999996", id="visa-prefix_4999_max"),
        # mastercard (51-55, 2221-2720, len 16)
        pytest.param(mastercard, "5100000000000008", id="mastercard-prefix_51_min"),
        pytest.param(mastercard, "5500000000000004", id="mastercard-prefix_55_max"),
        pytest.param(mastercard, "2221000000000009", id="mastercard-prefix_2221_min"),
        pytest.param(mastercard, "2229000000000001", id="mastercard-prefix_2229_max"),
        pytest.param(mastercard, "2230000000000008", id="mastercard-prefix_2230_min"),
        pytest.param(mastercard, "2299000000000006", id="mastercard-prefix_2299_max"),
        pytest.param(mastercard, "2300000000000003", id="mastercard-prefix_2300_min"),
        pytest.param(mastercard, "2699000000000002", id="mastercard-prefix_2699_max"),
        pytest.param(mastercard, "2700000000000009", id="mastercard-prefix_2700_min"),
        pytest.param(mastercard, "2719000000000008", id="mastercard-prefix_2719_max"),
        pytest.param(mastercard, "2720000000000005", id="mastercard-prefix_2720_exact"),
        # amex (34, 37, len 15)
        pytest.param(amex, "340000000000009", id="amex-prefix_34_len_15"),
        pytest.param(amex, "378282246310005", id="amex-prefix_37_len_15"),
        # diners (30, 36, 38, 39 at both len 14 and len 16)
        pytest.param(diners, "30000000000004", id="diners-prefix_30_len_14"),
        pytest.param(diners, "36000000000008", id="diners-prefix_36_len_14"),
        pytest.param(diners, "38000000000006", id="diners-prefix_38_len_14"),
        pytest.param(diners, "39000000000005", id="diners-prefix_39_len_14"),
        pytest.param(diners, "3056930009020004", id="diners-prefix_30_len_16"),
        pytest.param(diners, "3600000000000008", id="diners-prefix_36_len_16"),
        pytest.param(diners, "3800000000000006", id="diners-prefix_38_len_16"),
        pytest.param(diners, "3900000000000005", id="diners-prefix_39_len_16"),
        # discover (60, 64, 65, len 16)
        pytest.param(discover, "6011111111111117", id="discover-prefix_60"),
        pytest.param(discover, "6400000000000003", id="discover-prefix_64"),
        pytest.param(discover, "6500000000000002", id="discover-prefix_65"),
        # mir (2200-2204, len 16)
        pytest.param(mir, "2200123456789019", id="mir-prefix_2200_min"),
        pytest.param(mir, "2201000000000003", id="mir-prefix_2201_mid"),
        pytest.param(mir, "2204000000000000", id="mir-prefix_2204_max"),
    ],
)
def test_issuer_valid_prefix_and_length_boundaries(func, value: str) -> None:
    """Exercise every regex branch and valid length boundary across all issuers."""
    assert func(value) is True


@pytest.mark.parametrize(
    ("func", "value"),
    [
        # visa: adjacent prefixes, off-by-one/13-digit lengths, unanchored '4'
        pytest.param(visa, "3999999999999998", id="visa-prefix_39_below"),
        pytest.param(visa, "5000000000000009", id="visa-prefix_50_above"),
        pytest.param(visa, "4000000000006", id="visa-len_13"),
        pytest.param(visa, "400000000000006", id="visa-len_15"),
        pytest.param(visa, "40000000000000006", id="visa-len_17"),
        pytest.param(visa, "0400000000000006", id="visa-unanchored_4_at_idx_1"),
        # mastercard: adjacent prefixes, off-by-one lengths, unanchored '55'
        pytest.param(mastercard, "5000000000000009", id="mastercard-prefix_50_below"),
        pytest.param(mastercard, "5600000000000003", id="mastercard-prefix_56_above"),
        pytest.param(mastercard, "2220000000000000", id="mastercard-prefix_2220_below"),
        pytest.param(mastercard, "2721000000000004", id="mastercard-prefix_2721_above"),
        pytest.param(mastercard, "550000000000004", id="mastercard-len_15"),
        pytest.param(mastercard, "55000000000000004", id="mastercard-len_17"),
        pytest.param(mastercard, "0550000000000004", id="mastercard-unanchored_55_at_idx_1"),
        # amex: adjacent prefixes, off-by-one lengths, unanchored '34'
        pytest.param(amex, "330000000000001", id="amex-prefix_33"),
        pytest.param(amex, "350000000000006", id="amex-prefix_35"),
        pytest.param(amex, "360000000000004", id="amex-prefix_36"),
        pytest.param(amex, "380000000000000", id="amex-prefix_38"),
        pytest.param(amex, "34000000000000", id="amex-len_14"),
        pytest.param(amex, "3400000000000000", id="amex-len_16"),
        pytest.param(amex, "034000000000000", id="amex-unanchored_34_at_idx_1"),
        # unionpay: adjacent prefixes, off-by-one lengths, unanchored '62'
        pytest.param(unionpay, "6100000000000006", id="unionpay-prefix_61_below"),
        pytest.param(unionpay, "6300000000000004", id="unionpay-prefix_63_above"),
        pytest.param(unionpay, "620000000000000", id="unionpay-len_15"),
        pytest.param(unionpay, "62000000000000000", id="unionpay-len_17"),
        pytest.param(unionpay, "0620000000000000", id="unionpay-unanchored_62_at_idx_1"),
        # diners: adjacent prefixes, lengths 13/15/17, unanchored '30'
        pytest.param(diners, "2900000000000007", id="diners-prefix_29"),
        pytest.param(diners, "3100000000000003", id="diners-prefix_31"),
        pytest.param(diners, "3500000000000009", id="diners-prefix_35"),
        pytest.param(diners, "3700000000000007", id="diners-prefix_37"),
        pytest.param(diners, "4000000000000002", id="diners-prefix_40"),
        pytest.param(diners, "3000000000007", id="diners-len_13"),
        pytest.param(diners, "300000000000007", id="diners-len_15_between_14_and_16"),
        pytest.param(diners, "30000000000000007", id="diners-len_17"),
        pytest.param(diners, "0300000000000007", id="diners-unanchored_30_at_idx_1"),
        # jcb: adjacent prefixes, off-by-one lengths, unanchored '35'
        pytest.param(jcb, "3400000000000000", id="jcb-prefix_34_below"),
        pytest.param(jcb, "3600000000000008", id="jcb-prefix_36_above"),
        pytest.param(jcb, "350000000000006", id="jcb-len_15"),
        pytest.param(jcb, "35000000000000006", id="jcb-len_17"),
        pytest.param(jcb, "0350000000000006", id="jcb-unanchored_35_at_idx_1"),
        # discover: adjacent prefixes, off-by-one lengths, unanchored '60'
        pytest.param(discover, "5900000000000000", id="discover-prefix_59"),
        pytest.param(discover, "6100000000000006", id="discover-prefix_61"),
        pytest.param(discover, "6300000000000004", id="discover-prefix_63"),
        pytest.param(discover, "6600000000000001", id="discover-prefix_66"),
        pytest.param(discover, "600000000000004", id="discover-len_15"),
        pytest.param(discover, "60000000000000004", id="discover-len_17"),
        pytest.param(discover, "0600000000000004", id="discover-unanchored_60_at_idx_1"),
        # mir: adjacent prefixes, off-by-one lengths, unanchored '2200'
        pytest.param(mir, "2199000000000007", id="mir-prefix_2199_below"),
        pytest.param(mir, "2205000000000009", id="mir-prefix_2205_above"),
        pytest.param(mir, "220000000000004", id="mir-len_15"),
        pytest.param(mir, "22000000000000004", id="mir-len_17"),
        pytest.param(mir, "0220000000000004", id="mir-unanchored_2200_at_idx_1"),
    ],
)
def test_issuer_invalid_prefix_length_and_anchor_boundaries(func, value: str) -> None:
    """All inputs pass Luhn checksum so rejection isolates prefix, length, or ^ anchor."""
    _assert_result(func(value), False)
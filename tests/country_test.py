import pytest

from validators.country import _get_code_type, calling_code, country_code, currency
from validators.utils import ValidationError

_BYTES_AUTO_DETECT_XFAIL = pytest.mark.xfail(
    raises=AttributeError,
    strict=True,
    reason=(
        "Defect in validators.country.country_code: bytes of length 2..3 with "
        "iso_format='auto' reaches _get_code_type(value).isdecimal() and raises "
        "AttributeError, which @validator does not catch."
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
        pytest.param(calling_code, "+91", True, id="calling_code-str_valid"),
        pytest.param(calling_code, None, False, id="calling_code-none"),
        pytest.param(calling_code, 123, False, id="calling_code-int"),
        pytest.param(calling_code, b"+91", False, id="calling_code-bytes"),
        pytest.param(country_code, "US", True, id="country_code-str_valid"),
        pytest.param(country_code, None, False, id="country_code-none"),
        pytest.param(country_code, 123, False, id="country_code-int"),
        pytest.param(
            country_code,
            b"US",
            False,
            id="country_code-bytes",
            marks=_BYTES_AUTO_DETECT_XFAIL,
        ),
        pytest.param(currency, "USD", True, id="currency-str_valid"),
        pytest.param(currency, None, False, id="currency-none"),
        pytest.param(currency, 123, False, id="currency-int"),
        pytest.param(currency, b"USD", False, id="currency-bytes"),
    ],
)
def test_all_country_validators_argument_types(func, value, expected_valid: bool) -> None:
    """TR-ISP-TYPE: Verify str, None, int, and bytes across all country validators."""
    _assert_result(func(value), expected_valid)


@pytest.mark.parametrize(
    ("value", "expected_valid"),
    [
        # calling_code -> ACoC (<= 20 tests)
        pytest.param("", False, id="str-empty"),
        pytest.param("+91", True, id="str-valid_simple"),
        pytest.param("+1-264", True, id="str-valid_hyphenated"),
        pytest.param("-31", False, id="str-invalid_minus_prefix"),
        pytest.param("91", False, id="str-invalid_missing_plus"),
        pytest.param("+999", False, id="str-invalid_unknown_code"),
        pytest.param("+abc", False, id="str-invalid_letters"),
        pytest.param(None, False, id="none"),
        pytest.param(91, False, id="int"),
        pytest.param(b"+91", False, id="bytes"),
    ],
)
def test_calling_code_isp_acoc(value, expected_valid: bool) -> None:
    """TR-ISP-CALLING-ACoC: All feasible blocks/combinations for calling_code."""
    _assert_result(calling_code(value), expected_valid)


# country_code -> PWC (4 iso_format x 5 lengths x 4 case options = 80 > 20)
# Characteristics & Blocks (Table 2):
#   - Format option (iso_format): {auto, alpha2, alpha3, numeric}
#   - Value length: {Empty (0), 1, 2, 3, more than 3}
#   - Case option (ignore_case): {True+lower, True+upper, False+lower, False+upper}
# For non-empty lengths {1, 2, 3, >3}, the 4x4 Latin square below covers all
# feasible (iso_format, length), (iso_format, case), and (length, case) pairs.
@pytest.mark.parametrize(
    ("value", "iso_format", "ignore_case", "expected_valid"),
    [
        # iso_format = "auto"
        pytest.param("u", "auto", True, False, id="auto-len_1-ignore_case_on-lowercase"),
        pytest.param("US", "auto", True, True, id="auto-len_2-ignore_case_on-uppercase"),
        pytest.param("usa", "auto", False, False, id="auto-len_3-ignore_case_off-lowercase"),
        pytest.param("USAA", "auto", False, False, id="auto-len_4plus-ignore_case_off-uppercase"),
        pytest.param("", "auto", False, False, id="auto-empty-ignore_case_off"),
        # iso_format = "alpha2"
        pytest.param("U", "alpha2", True, False, id="alpha2-len_1-ignore_case_on-uppercase"),
        pytest.param("us", "alpha2", True, True, id="alpha2-len_2-ignore_case_on-lowercase"),
        pytest.param("USA", "alpha2", False, False, id="alpha2-len_3-ignore_case_off-uppercase"),
        pytest.param("usaa", "alpha2", False, False, id="alpha2-len_4plus-ignore_case_off-lowercase"),
        pytest.param("", "alpha2", True, False, id="alpha2-empty-ignore_case_on"),
        # iso_format = "alpha3"
        pytest.param("u", "alpha3", False, False, id="alpha3-len_1-ignore_case_off-lowercase"),
        pytest.param("GB", "alpha3", False, False, id="alpha3-len_2-ignore_case_off-uppercase"),
        pytest.param("usa", "alpha3", True, True, id="alpha3-len_3-ignore_case_on-lowercase"),
        pytest.param("USAA", "alpha3", True, False, id="alpha3-len_4plus-ignore_case_on-uppercase"),
        pytest.param("", "alpha3", False, False, id="alpha3-empty-ignore_case_off"),
        # iso_format = "numeric"
        pytest.param("U", "numeric", False, False, id="numeric-len_1-ignore_case_off-uppercase"),
        pytest.param("us", "numeric", False, False, id="numeric-len_2-ignore_case_off-lowercase"),
        pytest.param("USA", "numeric", True, False, id="numeric-len_3-ignore_case_on-uppercase"),
        pytest.param("usaa", "numeric", True, False, id="numeric-len_4plus-ignore_case_on-lowercase"),
        pytest.param("", "numeric", True, False, id="numeric-empty-ignore_case_on"),
    ],
)
def test_country_code_isp_pwc_matrix(
    value: str, iso_format: str, ignore_case: bool, expected_valid: bool
) -> None:
    """TR-ISP-COUNTRY-PWC: Pairwise covering array over Table 2 blocks."""
    _assert_result(
        country_code(value, iso_format=iso_format, ignore_case=ignore_case),
        expected_valid,
    )


@pytest.mark.parametrize(
    ("value", "iso_format", "ignore_case", "expected_valid"),
    [
        pytest.param("US", "auto", False, True, id="valid-alpha2-auto"),
        pytest.param("USA", "auto", False, True, id="valid-alpha3-auto"),
        pytest.param("840", "auto", False, True, id="valid-numeric-auto"),
        pytest.param("840", "auto", True, True, id="valid-numeric-auto-ignore_case_on"),
        pytest.param("US", "alpha2", False, True, id="valid-alpha2-explicit"),
        pytest.param("USA", "alpha3", False, True, id="valid-alpha3-explicit"),
        pytest.param("840", "numeric", False, True, id="valid-numeric-explicit"),
        pytest.param("840", "numeric", True, True, id="valid-numeric-explicit-ignore_case_on"),
        pytest.param("ZZ", "auto", False, False, id="invalid-alpha2-unknown"),
        pytest.param("ZZZ", "auto", False, False, id="invalid-alpha3-unknown"),
        pytest.param("999", "auto", False, False, id="invalid-numeric-3digit_unknown"),
        pytest.param("84", "numeric", False, False, id="invalid-numeric-2digit"),
        pytest.param("U1", "auto", False, False, id="invalid-mixed_alphanumeric-auto"),
    ],
)
def test_country_code_isp_code_validity_blocks(
    value: str, iso_format: str, ignore_case: bool, expected_valid: bool
) -> None:
    """TR-ISP-COUNTRY-CONTENT: Valid/invalid code blocks across all iso_format options."""
    _assert_result(
        country_code(value, iso_format=iso_format, ignore_case=ignore_case),
        expected_valid,
    )


# currency -> ACoC (<= 20 tests)
# Covers Table 2 (skip_symbols and value kind) + ignore_case signature flag.
@pytest.mark.parametrize(
    ("value", "skip_symbols", "ignore_case", "expected_valid"),
    [
        # Symbol with skip_symbols=True vs False across ignore_case
        pytest.param("$", True, False, False, id="symbol-skip_symbols_on-ignore_case_off"),
        pytest.param("$", True, True, False, id="symbol-skip_symbols_on-ignore_case_on"),
        pytest.param("$", False, False, True, id="symbol-skip_symbols_off-ignore_case_off"),
        pytest.param("$", False, True, True, id="symbol-skip_symbols_off-ignore_case_on"),
        # Valid 3-letter uppercase code across skip_symbols and ignore_case
        pytest.param("USD", True, False, True, id="valid_upper-skip_symbols_on-ignore_case_off"),
        pytest.param("USD", True, True, True, id="valid_upper-skip_symbols_on-ignore_case_on"),
        pytest.param("USD", False, False, True, id="valid_upper-skip_symbols_off-ignore_case_off"),
        pytest.param("USD", False, True, True, id="valid_upper-skip_symbols_off-ignore_case_on"),
        # Valid 3-letter lowercase code across skip_symbols and ignore_case
        pytest.param("usd", True, False, False, id="valid_lower-skip_symbols_on-ignore_case_off"),
        pytest.param("usd", True, True, True, id="valid_lower-skip_symbols_on-ignore_case_on"),
        pytest.param("usd", False, False, False, id="valid_lower-skip_symbols_off-ignore_case_off"),
        pytest.param("usd", False, True, True, id="valid_lower-skip_symbols_off-ignore_case_on"),
        # Other / invalid values across skip_symbols and ignore_case
        pytest.param("ZWX", True, False, False, id="other_invalid_upper_3char-skip_symbols_on-ignore_case_off"),
        pytest.param("zwx", True, True, False, id="other_invalid_lower_3char-skip_symbols_on-ignore_case_on"),
        pytest.param("@", False, False, False, id="other_non_symbol_char-skip_symbols_off-ignore_case_off"),
        pytest.param("US", False, True, False, id="other_len_2-skip_symbols_off-ignore_case_on"),
        pytest.param("", True, False, False, id="other_empty-skip_symbols_on-ignore_case_off"),
        pytest.param("USDD", False, False, False, id="other_len_4-skip_symbols_off-ignore_case_off"),
    ],
)
def test_currency_isp_acoc(
    value: str, skip_symbols: bool, ignore_case: bool, expected_valid: bool
) -> None:
    """TR-ISP-CURRENCY-ACoC: All combinations of skip_symbols, ignore_case, and value kind."""
    _assert_result(
        currency(value, skip_symbols=skip_symbols, ignore_case=ignore_case),
        expected_valid,
    )


# ===========================================================================
# 2. Logic Coverage (PC, CC, CACC) - Section 2.4
# ===========================================================================


# Compound Predicate P1 (country_code): not (1 < len(value) < 4)
# Clauses: c1 = (1 < len(value)), c2 = (len(value) < 4)
# Truth Table (for non-empty strings):
#   Row 1: c1=T, c2=T -> P1=F   ("US", "USA")  [Feasible]
#   Row 2: c1=T, c2=F -> P1=T   ("USAA")       [Feasible]
#   Row 3: c1=F, c2=T -> P1=T   ("U")          [Feasible; c2 short-circuited]
#   Row 4: c1=F, c2=F -> P1=T   (len<=1 & >=4) [Infeasible]
# CACC pairs: active c1 (Row 1 vs Row 3), active c2 (Row 1 vs Row 2)
@pytest.mark.parametrize(
    ("value", "expected_valid"),
    [
        pytest.param("US", True, id="row1-gt_1_true-lt_4_true-pred_false-len_2"),
        pytest.param("USA", True, id="row1-gt_1_true-lt_4_true-pred_false-len_3"),
        pytest.param("USAA", False, id="row2-gt_1_true-lt_4_false-pred_true-len_4"),
        pytest.param("U", False, id="row3-gt_1_false-lt_4_true-pred_true-len_1"),
    ],
)
def test_country_code_predicate_p1_length_bounds_cacc(
    value: str, expected_valid: bool
) -> None:
    """TR-LC-P1: PC, CC, and CACC for `not (1 < len(value) < 4)`."""
    _assert_result(country_code(value), expected_valid)


# Compound Predicate P2 (country_code):
#   iso_format == "auto" and (iso_format := _get_code_type(value)) == "invalid"
# Clauses: c1 = (iso_format == "auto"), c2 = (_get_code_type(value) == "invalid")
# Truth Table:
#   Row 1: c1=T, c2=T -> P2=T   ("U1", "auto")    [Feasible]
#   Row 2: c1=T, c2=F -> P2=F   ("US", "auto")    [Feasible]
#   Row 3: c1=F, c2=T -> P2=F   ("U1", "alpha2")  [c2 short-circuited]
#   Row 4: c1=F, c2=F -> P2=F   ("US", "alpha2")  [c2 short-circuited]
# CACC pairs: active c1 (Row 1 vs Row 3), active c2 (Row 1 vs Row 2)
@pytest.mark.parametrize(
    ("value", "iso_format", "expected_valid"),
    [
        pytest.param("U1", "auto", False, id="row1-auto_true-invalid_type_true-pred_true"),
        pytest.param("US", "auto", True, id="row2-auto_true-invalid_type_false-pred_false-alpha2"),
        pytest.param("USA", "auto", True, id="row2-auto_true-invalid_type_false-pred_false-alpha3"),
        pytest.param("840", "auto", True, id="row2-auto_true-invalid_type_false-pred_false-numeric"),
        pytest.param("U1", "alpha2", False, id="row3-auto_false-short_circuit_invalid-pred_false"),
        pytest.param("US", "alpha2", True, id="row4-auto_false-short_circuit_valid-pred_false"),
    ],
)
def test_country_code_predicate_p2_auto_detect_cacc(
    value: str, iso_format: str, expected_valid: bool
) -> None:
    """TR-LC-P2: PC, CC, and CACC for `iso_format == 'auto' and ... == 'invalid'`."""
    _assert_result(country_code(value, iso_format=iso_format), expected_valid)


# Compound Predicate P3 (currency - explicitly cited in Section 2.4):
#   not skip_symbols and value in _currency_symbols
# Clauses: c1 = (not skip_symbols), c2 = (value in _currency_symbols)
# Truth Table:
#   Row 1: c1=T (skip=False), c2=T ("$")   -> P3=T  [Feasible]
#   Row 2: c1=T (skip=False), c2=F ("@")   -> P3=F  [Feasible; "USD" falls through]
#   Row 3: c1=F (skip=True),  c2=T ("$")   -> P3=F  [c2 short-circuited]
#   Row 4: c1=F (skip=True),  c2=F ("USD") -> P3=F  [c2 short-circuited]
# CACC pairs: active c1 (Row 1 vs Row 3), active c2 (Row 1 vs Row 2)
@pytest.mark.parametrize(
    ("value", "skip_symbols", "expected_valid"),
    [
        pytest.param("$", False, True, id="row1-allow_symbols_true-in_symbols_true-pred_true"),
        pytest.param("@", False, False, id="row2-allow_symbols_true-in_symbols_false-pred_false-invalid"),
        pytest.param("USD", False, True, id="row2-allow_symbols_true-in_symbols_false-pred_false-valid_code"),
        pytest.param("$", True, False, id="row3-allow_symbols_false-short_circuit_symbol-pred_false"),
        pytest.param("USD", True, True, id="row4-allow_symbols_false-short_circuit_valid_code-pred_false"),
        pytest.param("@", True, False, id="row4-allow_symbols_false-short_circuit_invalid-pred_false"),
    ],
)
def test_currency_predicate_p3_symbol_check_cacc(
    value: str, skip_symbols: bool, expected_valid: bool
) -> None:
    """TR-LC-P3: PC, CC, and CACC for `not skip_symbols and value in _currency_symbols`."""
    _assert_result(currency(value, skip_symbols=skip_symbols), expected_valid)


@pytest.mark.parametrize(
    ("value", "expected_valid"),
    [
        pytest.param("", False, id="empty_true"),
        pytest.param("+91", True, id="empty_false-in_calling_codes_true"),
        pytest.param("-31", False, id="empty_false-in_calling_codes_false"),
    ],
)
def test_calling_code_single_clause_predicates(value: str, expected_valid: bool) -> None:
    """TR-LC-CALLING: PC/CC for `if not value` and membership check."""
    _assert_result(calling_code(value), expected_valid)


@pytest.mark.parametrize(
    ("value", "iso_format", "ignore_case", "expected_valid"),
    [
        pytest.param("", "auto", False, False, id="empty_true"),
        pytest.param("us", "alpha2", True, True, id="alpha2-ignore_case_true-valid"),
        pytest.param("zz", "alpha2", True, False, id="alpha2-ignore_case_true-invalid"),
        pytest.param("US", "alpha2", False, True, id="alpha2-ignore_case_false-valid"),
        pytest.param("us", "alpha2", False, False, id="alpha2-ignore_case_false-invalid"),
        pytest.param("usa", "alpha3", True, True, id="alpha3-ignore_case_true-valid"),
        pytest.param("zzz", "alpha3", True, False, id="alpha3-ignore_case_true-invalid"),
        pytest.param("USA", "alpha3", False, True, id="alpha3-ignore_case_false-valid"),
        pytest.param("usa", "alpha3", False, False, id="alpha3-ignore_case_false-invalid"),
        pytest.param("840", "numeric", False, True, id="numeric-valid"),
        pytest.param("999", "numeric", False, False, id="numeric-invalid"),
        pytest.param("USA", "unsupported", False, False, id="unsupported_format-else_false"),
    ],
)
def test_country_code_single_clause_predicates(
    value: str, iso_format: str, ignore_case: bool, expected_valid: bool
) -> None:
    """TR-LC-COUNTRY-BRANCHES: PC/CC for format branches and ignore_case ternaries."""
    _assert_result(
        country_code(value, iso_format=iso_format, ignore_case=ignore_case),
        expected_valid,
    )


@pytest.mark.parametrize(
    ("value", "ignore_case", "expected_valid"),
    [
        pytest.param("", False, False, id="empty_true"),
        pytest.param("US", False, False, id="len_not_3_true-short"),
        pytest.param("USDD", False, False, id="len_not_3_true-long"),
        pytest.param("usd", True, True, id="ignore_case_true-valid"),
        pytest.param("zwx", True, False, id="ignore_case_true-invalid"),
        pytest.param("USD", False, True, id="ignore_case_false-valid"),
        pytest.param("usd", False, False, id="ignore_case_false-invalid"),
    ],
)
def test_currency_single_clause_predicates(
    value: str, ignore_case: bool, expected_valid: bool
) -> None:
    """TR-LC-CURRENCY-BRANCHES: PC/CC for empty check, length != 3, and ignore_case ternary."""
    _assert_result(currency(value, ignore_case=ignore_case), expected_valid)


@pytest.mark.parametrize(
    ("value", "expected_type"),
    [
        pytest.param("840", "numeric", id="isdecimal_true-numeric"),
        pytest.param("US", "alpha2", id="isalpha_true-len_2-alpha2"),
        pytest.param("USA", "alpha3", id="isalpha_true-len_3-alpha3"),
        pytest.param("A", "invalid", id="isalpha_true-len_1-invalid"),
        pytest.param("ABCD", "invalid", id="isalpha_true-len_4-invalid"),
        pytest.param("U1", "invalid", id="isalpha_false-alphanumeric-invalid"),
    ],
)
def test_get_code_type_predicates(value: str, expected_type: str) -> None:
    """TR-LC-HELPER: PC/CC for every branch in _get_code_type."""
    assert _get_code_type(value) == expected_type


# ===========================================================================
# 3. Branch Coverage, Mutation Testing & ValidationError Contract - Sec 2.1/2.2
# ===========================================================================


@pytest.mark.parametrize(
    ("func", "bad_input"),
    [
        pytest.param(calling_code, None, id="calling_code-none"),
        pytest.param(calling_code, 123, id="calling_code-int"),
        pytest.param(calling_code, 91.5, id="calling_code-float"),
        pytest.param(calling_code, b"+91", id="calling_code-bytes"),
        pytest.param(calling_code, [], id="calling_code-empty_list"),
        pytest.param(calling_code, {}, id="calling_code-empty_dict"),
        pytest.param(country_code, None, id="country_code-none"),
        pytest.param(country_code, 123, id="country_code-int"),
        pytest.param(country_code, 12.3, id="country_code-float"),
        pytest.param(country_code, b"", id="country_code-bytes_empty"),
        pytest.param(country_code, b"U", id="country_code-bytes_len_1"),
        pytest.param(
            country_code,
            b"US",
            id="country_code-bytes_len_2",
            marks=_BYTES_AUTO_DETECT_XFAIL,
        ),
        pytest.param(
            country_code,
            b"840",
            id="country_code-bytes_len_3_numeric",
            marks=_BYTES_AUTO_DETECT_XFAIL,
        ),
        pytest.param(country_code, b"USAA", id="country_code-bytes_len_4"),
        pytest.param(country_code, [], id="country_code-empty_list"),
        pytest.param(currency, None, id="currency-none"),
        pytest.param(currency, 123, id="currency-int"),
        pytest.param(currency, 1.23, id="currency-float"),
        pytest.param(currency, b"USD", id="currency-bytes"),
        pytest.param(currency, [], id="currency-empty_list"),
    ],
)
def test_invalid_types_return_validation_error(func, bad_input) -> None:
    """Confirm decorator-caught/falsy non-str inputs return falsy ValidationError."""
    result = func(bad_input)
    _assert_result(result, False)
    assert result.func.__name__ == func.__name__


@pytest.mark.parametrize(
    ("value", "iso_format", "ignore_case"),
    [
        pytest.param(b"US", "alpha2", False, id="bytes-alpha2-ignore_case_off"),
        pytest.param(b"us", "alpha2", True, id="bytes-alpha2-ignore_case_on"),
        pytest.param(b"USA", "alpha3", False, id="bytes-alpha3"),
        pytest.param(b"840", "numeric", False, id="bytes-numeric"),
    ],
)
def test_country_code_bytes_explicit_format_returns_validation_error(
    value: bytes, iso_format: str, ignore_case: bool
) -> None:
    """When iso_format != 'auto', _get_code_type is bypassed and bytes return ValidationError."""
    _assert_result(
        country_code(value, iso_format=iso_format, ignore_case=ignore_case),
        False,
    )


def test_currency_invalid_type_with_skip_symbols_false() -> None:
    """Ensure int/bytes with skip_symbols=False return ValidationError instead of crashing."""
    _assert_result(currency(123, skip_symbols=False), False)
    _assert_result(currency(b"$", skip_symbols=False), False)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("+297", id="first_entry_abw"),
        pytest.param("+1", id="single_digit_nanp"),
        pytest.param("+1-264", id="hyphenated_aia"),
        pytest.param("+44-1481", id="hyphenated_ggy"),
        pytest.param("+263", id="last_entry_zwe"),
    ],
)
def test_calling_code_valid_boundaries(value: str) -> None:
    assert calling_code(value) is True


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(" +91", id="leading_space"),
        pytest.param("+91 ", id="trailing_space"),
        pytest.param("+0", id="zero"),
        pytest.param("+00", id="double_zero"),
        pytest.param("+1-", id="trailing_hyphen"),
        pytest.param("-1", id="minus_prefix"),
        pytest.param("1-264", id="missing_plus_hyphenated"),
        pytest.param("+1 264", id="space_instead_of_hyphen"),
    ],
)
def test_calling_code_invalid_formatting(value: str) -> None:
    _assert_result(calling_code(value), False)


def test_country_code_defaults_are_auto_and_case_sensitive() -> None:
    """Kills mutants flipping default iso_format='auto' or ignore_case=False."""
    assert country_code("US") is True
    assert country_code("USA") is True
    assert country_code("840") is True
    _assert_result(country_code("us"), False)
    _assert_result(country_code("usa"), False)
    _assert_result(country_code("iN"), False)


@pytest.mark.parametrize(
    ("value", "iso_format", "ignore_case"),
    [
        pytest.param("AW", "alpha2", False, id="alpha2-first_entry_aw"),
        pytest.param("ZW", "alpha2", False, id="alpha2-last_entry_zw"),
        pytest.param("Us", "alpha2", True, id="alpha2-mixed_case"),
        pytest.param("ABW", "alpha3", False, id="alpha3-first_entry_abw"),
        pytest.param("ZWE", "alpha3", False, id="alpha3-last_entry_zwe"),
        pytest.param("uSa", "alpha3", True, id="alpha3-mixed_case"),
        pytest.param("004", "numeric", False, id="numeric-first_entry_004"),
        pytest.param("894", "numeric", False, id="numeric-last_entry_894"),
        pytest.param("us", "auto", True, id="auto-alpha2_lower_ignore_case"),
        pytest.param("usa", "auto", True, id="auto-alpha3_lower_ignore_case"),
    ],
)
def test_country_code_valid_boundaries_and_case(
    value: str, iso_format: str, ignore_case: bool
) -> None:
    assert country_code(value, iso_format=iso_format, ignore_case=ignore_case) is True


@pytest.mark.parametrize(
    ("value", "iso_format", "ignore_case"),
    [
        pytest.param("GB", "alpha3", False, id="alpha2_code_with_alpha3_format"),
        pytest.param("USA", "alpha2", False, id="alpha3_code_with_alpha2_format"),
        pytest.param("840", "alpha2", False, id="numeric_code_with_alpha2_format"),
        pytest.param("840", "alpha3", False, id="numeric_code_with_alpha3_format"),
        pytest.param("US", "numeric", False, id="alpha2_code_with_numeric_format"),
        pytest.param("USA", "numeric", False, id="alpha3_code_with_numeric_format"),
        pytest.param("0840", "numeric", False, id="numeric_4_digits"),
        pytest.param("000", "numeric", False, id="numeric_000_not_in_table"),
        pytest.param("1", "numeric", False, id="numeric_1_digit"),
        pytest.param("USA", "ALPHA3", False, id="uppercase_format_name_ALPHA3"),
        pytest.param("840", "invalid", False, id="unknown_format_invalid"),
        pytest.param("US", "", False, id="empty_format_name"),
        pytest.param("²³", "auto", False, id="superscript_digits"),
        pytest.param("½", "auto", False, id="vulgar_fraction"),
        pytest.param("١٢٣", "auto", False, id="arabic_indic_digits"),
        pytest.param(" US", "auto", False, id="leading_space"),
        pytest.param("US ", "auto", False, id="trailing_space"),
    ],
)
def test_country_code_invalid_cross_format_and_edge_cases(
    value: str, iso_format: str, ignore_case: bool
) -> None:
    _assert_result(
        country_code(value, iso_format=iso_format, ignore_case=ignore_case),
        False,
    )


def test_currency_defaults_skip_symbols_and_case_sensitive() -> None:
    """Kills mutants flipping default skip_symbols=True or ignore_case=False."""
    assert currency("USD") is True
    _assert_result(currency("$"), False)
    _assert_result(currency("usd"), False)
    _assert_result(currency("Usd"), False)


@pytest.mark.parametrize(
    ("value", "skip_symbols", "ignore_case"),
    [
        pytest.param("AED", True, False, id="iso4217-first_entry_aed"),
        pytest.param("ZWL", True, False, id="iso4217-last_entry_zwl"),
        pytest.param("Cad", True, True, id="iso4217-mixed_case"),
        pytest.param("؋", False, False, id="symbol-first_entry_afghani"),
        pytest.param("€", False, False, id="symbol-euro"),
        pytest.param("₹", False, False, id="symbol-rupee"),
        pytest.param("Rs", False, False, id="symbol-two_char_Rs"),
        pytest.param("Rs", False, True, id="symbol-two_char_Rs_ignore_case_on"),
        pytest.param("¤", False, False, id="symbol-last_entry_generic"),
    ],
)
def test_currency_valid_boundaries_and_symbols(
    value: str, skip_symbols: bool, ignore_case: bool
) -> None:
    assert currency(value, skip_symbols=skip_symbols, ignore_case=ignore_case) is True


@pytest.mark.parametrize(
    ("value", "skip_symbols", "ignore_case"),
    [
        pytest.param("Rs", True, False, id="two_char_Rs_with_skip_symbols_on"),
        pytest.param("rs", False, True, id="lowercase_rs_symbol_case_sensitive"),
        pytest.param("RS", False, True, id="uppercase_RS_not_symbol_or_code"),
        pytest.param(" USD", True, False, id="leading_space"),
        pytest.param("USD ", True, False, id="trailing_space"),
        pytest.param("123", False, False, id="three_digits"),
        pytest.param("U$D", False, False, id="embedded_dollar_sign"),
        pytest.param("$$$", False, False, id="repeated_dollar_signs"),
    ],
)
def test_currency_invalid_edge_cases(
    value: str, skip_symbols: bool, ignore_case: bool
) -> None:
    _assert_result(
        currency(value, skip_symbols=skip_symbols, ignore_case=ignore_case),
        False,
    )
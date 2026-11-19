import pytest

from validators.domain import _IanaTLD, domain
from validators.utils import ValidationError


def _assert_invalid(result) -> None:
    """Confirm invalid validations return a falsy ValidationError."""
    assert isinstance(result, ValidationError)
    assert not result


# ---------------------------------------------------------------------------
# 1. ISP: Argument type (Table 2 - All validators)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "is_valid"),
    [
        pytest.param("example.com", True, id="str_valid"),
        pytest.param("", False, id="str_empty"),
        pytest.param(None, False, id="none"),
        pytest.param(0, False, id="int_zero"),
        pytest.param(b"example.com", False, id="bytes_ascii"),
        pytest.param(b"", False, id="bytes_empty"),
    ],
)
def test_domain_argument_types(value, is_valid):
    """Cover non-raising argument types from Table 2 (str, None, int, bytes)."""
    result = domain(value)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


def test_domain_truthy_int_defect():
    """Document Section 2.2 defect: truthy int raises AttributeError instead of ValidationError."""
    with pytest.raises(AttributeError):
        domain(123)


# ---------------------------------------------------------------------------
# 2. ISP: Pairwise Coverage (PWC) & Option Flag Matching (Table 2 - domain)
# ---------------------------------------------------------------------------
# Because ACoC across (Character set [3] x Label length [2] x Total length [2]
# x consider_tld [2] x rfc_1034 [2] x rfc_2782 [2]) yields 96 combinations (> 20),
# these 8 tests form a Pairwise Covering Array covering all 70 parameter pairs:
#
#   ID    | Char set    | Label | Total | consider_tld | rfc_1034 | rfc_2782
#   ------+-------------+-------+-------+--------------+----------+---------
#   pwc1  | mapped IDN  | <=63  | <=253 | False        | False    | False
#   pwc2  | mapped IDN  | >=64  | >=254 | True         | True     | True
#   pwc3  | direct IDN  | <=63  | >=254 | False        | True     | False
#   pwc4  | direct IDN  | >=64  | <=253 | True         | False    | True
#   pwc5  | ASCII       | <=63  | <=253 | True         | False    | True
#   pwc6  | ASCII       | >=64  | >=254 | False        | True     | False
#   pwc7  | ASCII       | <=63  | >=254 | True         | False    | False
#   pwc8  | direct IDN  | >=64  | <=253 | False        | True     | True


@pytest.mark.parametrize(
    ("value", "consider_tld", "rfc_1034", "rfc_2782", "is_valid"),
    [
        pytest.param(
            "\uff45\uff58\uff41\uff4d\uff50\uff4c\uff45.com",
            False,
            False,
            False,
            False,
            id="pwc1_mapped_short",
        ),
        pytest.param(
            "_srv." + ("\uff45" * 64) + "." + ("a" * 62 + ".") * 3 + "com.",
            True,
            True,
            True,
            False,
            id="pwc2_mapped_long_label_and_total",
        ),
        pytest.param(
            "m\u00fcnchen." + ("a" * 62 + ".") * 3 + ("b" * 60 + ".") + "notatld.",
            False,
            True,
            False,
            False,
            id="pwc3_direct_long_total",
        ),
        pytest.param(
            "_srv.\u00fc" + ("a" * 63) + ".de",
            True,
            False,
            True,
            False,
            id="pwc4_direct_long_label",
        ),
        pytest.param(
            "_http._tcp.example.com",
            True,
            False,
            True,
            True,
            id="pwc5_ascii_valid_service",
        ),
        pytest.param(
            ("a" * 64 + ".") + ("b" * 62 + ".") * 3 + "notatld.",
            False,
            True,
            False,
            False,
            id="pwc6_ascii_long_label_and_total",
        ),
        pytest.param(
            ("a" * 62 + ".") * 4 + "com",
            True,
            False,
            False,
            False,
            id="pwc7_ascii_long_total",
        ),
        pytest.param(
            "_srv.\u00fc" + ("a" * 63) + ".notatld.",
            False,
            True,
            True,
            False,
            id="pwc8_direct_long_label_service_dot",
        ),
    ],
)
def test_domain_isp_pairwise(value, consider_tld, rfc_1034, rfc_2782, is_valid):
    """Verify Pairwise Coverage (PWC) across all domain ISP characteristics."""
    result = domain(
        value,
        consider_tld=consider_tld,
        rfc_1034=rfc_1034,
        rfc_2782=rfc_2782,
    )
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


@pytest.mark.parametrize(
    ("value", "consider_tld", "rfc_1034", "rfc_2782", "is_valid"),
    [
        pytest.param("example.com", True, False, False, True, id="consider_tld_on_popular"),
        pytest.param("example.io", True, False, False, True, id="consider_tld_on_iana"),
        pytest.param("example.notatld", True, False, False, False, id="consider_tld_on_unknown"),
        pytest.param("example.notatld", False, False, False, True, id="consider_tld_off_unknown"),
        pytest.param("example.com.", False, True, False, True, id="rfc1034_on_trailing_dot"),
        pytest.param("example.com.", False, False, False, False, id="rfc1034_off_trailing_dot"),
        pytest.param("_http._tcp.example.com", False, False, True, True, id="rfc2782_on_underscore"),
        pytest.param("_http._tcp.example.com", False, False, False, False, id="rfc2782_off_underscore"),
        pytest.param("m\u00fcnchen.de", False, False, False, True, id="direct_idn_valid"),
        pytest.param("_http._tcp.m\u00fcnchen.de.", True, True, True, True, id="all_flags_on_direct_idn"),
    ],
)
def test_domain_isp_option_flags(value, consider_tld, rfc_1034, rfc_2782, is_valid):
    """Ensure each option flag on/off is tested with a matching valid/invalid input."""
    result = domain(
        value,
        consider_tld=consider_tld,
        rfc_1034=rfc_1034,
        rfc_2782=rfc_2782,
    )
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


# ---------------------------------------------------------------------------
# 3. Logic Coverage (PC, CC, CACC) for compound predicates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "is_valid"),
    [
        # Predicate P1 (_relies_on_idna_mapping):
        #   A and (B or any(D or E for char in value))
        #   A: not value.isascii()
        #   B: normalize("NFKC", value) != value
        #   D: in_table_b1(char)
        #   E: char in "\u3002\uff0e\uff61"
        #
        # Note: When A is False (ASCII), B, D, and E are structurally False and
        # short-circuited. Similarly, D and E cannot both be True on the same char.
        pytest.param("example.com", True, id="ascii_short_circuit"),           # A=F -> P1=F
        pytest.param("m\u00fcnchen.de", True, id="direct_non_ascii_valid"),    # A=T, B=F, D=F, E=F -> P1=F
        pytest.param("caf\u00e9.com", True, id="nfc_non_ascii_valid"),         # A=T, B=F, D=F, E=F -> P1=F
        pytest.param("\uff45\uff58\uff41\uff4d\uff50\uff4c\uff45.com", False, id="nfkc_fullwidth_letters"),  # A=T, B=T, D=F, E=F -> P1=T
        pytest.param("cafe\u0301.com", False, id="nfkc_decomposed_accent"),    # A=T, B=T, D=F, E=F -> P1=T
        pytest.param("exa\u00admple.com", False, id="table_b1_soft_hyphen"),   # A=T, B=F, D=T, E=F -> P1=T
        pytest.param("example\u3002com", False, id="special_dot_u3002"),       # A=T, B=F, D=F, E=T -> P1=T
        pytest.param("example\uff0ecom", False, id="special_dot_uff0e"),
        pytest.param("example\uff61com", False, id="special_dot_uff61"),
    ],
)
def test_logic_coverage_idna_mapping_predicate(value, is_valid):
    """CACC/CC/PC for _relies_on_idna_mapping(value)."""
    result = domain(value)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


@pytest.mark.parametrize(
    ("value", "consider_tld", "is_valid"),
    [
        # Predicate P2: F and G
        #   F: consider_tld
        #   G: not _IanaTLD.check(...)
        pytest.param("example.notatld", True, False, id="flag_on_unknown_tld"),   # F=T, G=T -> P2=T
        pytest.param("example.notatld", False, True, id="flag_off_unknown_tld"),  # F=F, G=T -> P2=F
        pytest.param("example.com", True, True, id="flag_on_valid_tld"),          # F=T, G=F -> P2=F
        pytest.param("example.com", False, True, id="flag_off_valid_tld"),        # F=F, G=F -> P2=F
    ],
)
def test_logic_coverage_consider_tld_predicate(value, consider_tld, is_valid):
    """CACC/CC/PC for the consider_tld compound condition."""
    result = domain(value, consider_tld=consider_tld)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


@pytest.mark.parametrize(
    ("value", "rfc_2782", "is_valid"),
    [
        # Predicate P3: H and I
        #   H: not re.search(r"\s|__+", value)
        #   I: bool(re.match(..., encoded, re.IGNORECASE))
        #
        # Note: "example.com\n" matches regex $ before trailing newline (I=T)
        # and "__http._tcp.example.com" with rfc_2782=True matches regex (I=T),
        # so both make H=F while keeping I=T.
        pytest.param("example.com", False, True, id="valid_chars_and_format"),                    # H=T, I=T -> P3=T
        pytest.param("example.com\n", False, False, id="trailing_newline_caught_by_search"),      # H=F, I=T -> P3=F
        pytest.param("__http._tcp.example.com", True, False, id="double_underscore_caught_by_search"),  # H=F, I=T -> P3=F
        pytest.param("-example.com", False, False, id="leading_hyphen_caught_by_regex"),          # H=T, I=F -> P3=F
        pytest.param("exa mple", False, False, id="space_and_missing_tld"),                       # H=F, I=F -> P3=F
    ],
)
def test_logic_coverage_final_return_predicate(value, rfc_2782, is_valid):
    """CACC/CC/PC for the final whitespace/underscore and regex predicate."""
    result = domain(value, rfc_2782=rfc_2782)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


# ---------------------------------------------------------------------------
# 4. Boundary, Branch, and Mutation-Killing Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "rfc_1034", "rfc_2782", "is_valid"),
    [
        # Label length boundaries (1, 2, 63 vs 64, and punycode expansion > 63)
        pytest.param("a.com", False, False, True, id="sub_1_char"),
        pytest.param("ab.com", False, False, True, id="sub_2_chars"),
        pytest.param(("a" * 63) + ".com", False, False, True, id="sub_63_chars"),
        pytest.param(("a" * 64) + ".com", False, False, False, id="sub_64_chars"),
        pytest.param("example.co", False, False, True, id="tld_2_chars"),
        pytest.param("example.a", False, False, False, id="tld_1_char"),
        pytest.param("example." + ("a" * 63), False, False, True, id="tld_63_chars"),
        pytest.param("example." + ("a" * 64), False, False, False, id="tld_64_chars"),
        pytest.param("\u00fc" + ("a" * 56) + ".com", False, False, False, id="encoded_label_over_63"),
        # Total length boundaries (253 vs 254, with/without trailing dot, punycode > 253)
        pytest.param(("a" * 63 + ".") * 3 + ("b" * 57) + ".com", False, False, True, id="total_253_chars"),
        pytest.param(("a" * 63 + ".") * 3 + ("b" * 57) + ".com.", True, False, True, id="total_253_with_trailing_dot"),
        pytest.param(("a" * 63 + ".") * 3 + ("b" * 58) + ".com", False, False, False, id="total_254_chars"),
        pytest.param(("a" * 63 + ".") * 3 + ("b" * 58) + ".com.", True, False, False, id="total_254_with_trailing_dot"),
        pytest.param("m\u00fcnchen." * 17 + "de", False, False, False, id="encoded_total_over_253"),
        # Numeric TLD checks (ASCII and IDN all-decimal TLDs)
        pytest.param("example.123", False, False, False, id="numeric_tld"),
        pytest.param("example.123.", True, False, False, id="numeric_tld_trailing_dot"),
        pytest.param("example.\u0661", False, False, False, id="numeric_idn_tld"),
        pytest.param("example.\u0661.", True, False, False, id="numeric_idn_tld_trailing_dot"),
        pytest.param("123.example.com", False, False, True, id="numeric_subdomain"),
        pytest.param("123", False, False, False, id="numeric_only"),
        # Case, hyphens, digits, structural errors, and UnicodeError paths
        pytest.param("EXAMPLE.COM", False, False, True, id="uppercase_domain"),
        pytest.param("my-host-1.sub-2.example.com", False, False, True, id="hyphen_in_middle"),
        pytest.param("example.x1y", False, False, True, id="digit_in_tld"),
        pytest.param("example.1ab", False, False, True, id="leading_digit_in_tld"),
        pytest.param("example.ab1", False, False, False, id="trailing_digit_in_tld"),
        pytest.param("-example.com", False, False, False, id="leading_hyphen"),
        pytest.param("example-.com", False, False, False, id="trailing_hyphen"),
        pytest.param("example.-com", False, False, False, id="tld_leading_hyphen"),
        pytest.param("example.com-", False, False, False, id="tld_trailing_hyphen"),
        pytest.param("localhost", False, False, False, id="single_label"),
        pytest.param(".", False, False, False, id="only_dot"),
        pytest.param(".example.com", False, False, False, id="leading_dot"),
        pytest.param("example..com", False, False, False, id="double_dot"),
        pytest.param("example.com..", True, False, False, id="double_trailing_dot"),
        pytest.param(" example.com", False, False, False, id="leading_space"),
        pytest.param("example.com ", False, False, False, id="trailing_space"),
        pytest.param("exa mple.com", False, False, False, id="internal_space"),
        pytest.param("example\t.com", False, False, False, id="tab_char"),
        # Service record underscore edge cases (rfc_2782)
        pytest.param("sub_1.example.com", False, True, True, id="srv_middle_underscore"),
        pytest.param("sub_.example.com", False, True, True, id="srv_trailing_underscore"),
        pytest.param("___http.example.com", False, True, False, id="srv_triple_underscore"),
        pytest.param("example.c_m", False, True, False, id="srv_underscore_in_tld"),
        # Non-domain punctuation
        pytest.param("example.com/", False, False, False, id="trailing_slash"),
        pytest.param("user@example.com", False, False, False, id="at_symbol"),
        pytest.param("example!.com", False, False, False, id="exclamation_mark"),
    ],
)
def test_domain_boundaries_and_structure(value, rfc_1034, rfc_2782, is_valid):
    """Test length boundaries, numeric TLDs, IDNA UnicodeErrors, and regex edge cases."""
    result = domain(value, rfc_1034=rfc_1034, rfc_2782=rfc_2782)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


@pytest.mark.parametrize(
    ("value", "rfc_1034", "is_valid"),
    [
        pytest.param("example.onion", False, True, id="tld_popular_onion"),
        pytest.param("example.Io", False, True, id="tld_case_insensitive"),
        pytest.param("example.io.", True, True, id="tld_iana_trailing_dot"),
        pytest.param("\u043f\u0440\u0438\u043c\u0435\u0440.\u0440\u0444", False, True, id="tld_idn_punycode"),
    ],
)
def test_domain_iana_tld_lookup_variants(value, rfc_1034, is_valid):
    """Verify popular cache, mixed-case normalization, trailing dots, and IDN punycode TLDs."""
    result = domain(value, consider_tld=True, rfc_1034=rfc_1034)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


def test_domain_iana_tld_full_cache_enabled(monkeypatch):
    """Cover _IanaTLD._full_cache population and cache-hit branches via PYVLD_CACHE_TLD."""
    monkeypatch.setenv("PYVLD_CACHE_TLD", "True")
    monkeypatch.setattr(_IanaTLD, "_full_cache", None)

    # First non-popular TLD lookup populates _full_cache
    assert domain("example.ca", consider_tld=True) is True
    assert _IanaTLD._full_cache is not None

    # Subsequent lookups hit populated _full_cache directly
    assert domain("example.edu", consider_tld=True) is True
    _assert_invalid(domain("example.notatld", consider_tld=True))
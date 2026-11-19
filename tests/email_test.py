import pytest

from validators.email import email
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
        pytest.param("someone@example.com", True, id="str_valid"),
        pytest.param("", False, id="str_empty"),
        pytest.param(None, False, id="none"),
        pytest.param(0, False, id="int_zero"),
        pytest.param(b"someone@example.com", False, id="bytes_email"),
        pytest.param(b"", False, id="bytes_empty"),
    ],
)
def test_email_argument_types(value, is_valid):
    """Cover non-raising argument types from Table 2 (str, None, int, bytes)."""
    result = email(value)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


def test_email_truthy_int_defect():
    """Document Section 2.2 defect: truthy int raises AttributeError instead of ValidationError."""
    with pytest.raises(AttributeError):
        email(123)


# ---------------------------------------------------------------------------
# 2. ISP: Pairwise Coverage (PWC) & Option Flag Matching (Table 2 - email)
# ---------------------------------------------------------------------------
# Because ACoC across (Number of @ signs [3] x Domain form [3] x Local len [2]
# x Domain len [2] x ipv4 [2] x ipv6 [2] x simple_host [2] x rfc_1034 [2]
# x rfc_2782 [2]) yields 1,152 combinations (> 20), these 10 tests form a
# Pairwise Covering Array covering all pairs across all 9 parameters:
#
#   ID    | @ count | Form | Local | Domain | ipv4 | ipv6 | simple | 1034 | 2782
#   ------+---------+------+-------+--------+------+------+--------+------+------
#   pwc1  | 1       | host | <=64  | <=253  | F    | F    | F      | F    | F
#   pwc2  | 1       | [ip] | <=64  | <=253  | T    | F    | T      | T    | T
#   pwc3  | 1       | ip   | >=65  | >=254  | F    | T    | F      | T    | F
#   pwc4  | 0       | host | <=64  | >=254  | T    | T    | T      | F    | T
#   pwc5  | 0       | [ip] | >=65  | <=253  | F    | F    | F      | T    | F
#   pwc6  | 0       | ip   | <=64  | <=253  | T    | F    | T      | F    | T
#   pwc7  | >1      | host | >=65  | <=253  | F    | T    | T      | T    | F
#   pwc8  | >1      | [ip] | <=64  | >=254  | F    | T    | F      | F    | T
#   pwc9  | >1      | ip   | >=65  | >=254  | T    | T    | F      | F    | F
#   pwc10 | >1      | host | >=65  | >=254  | F    | F    | F      | T    | T


@pytest.mark.parametrize(
    ("value", "ipv4_address", "ipv6_address", "simple_host", "rfc_1034", "rfc_2782", "is_valid"),
    [
        pytest.param(
            "someone@example.com",
            False,
            False,
            False,
            False,
            False,
            True,
            id="pwc1_valid_hostname",
        ),
        pytest.param(
            "someone@[127.0.0.1]",
            True,
            False,
            True,
            True,
            True,
            True,
            id="pwc2_valid_bracketed_ipv4",
        ),
        pytest.param(
            ("a" * 65) + "@127.0.0." + ("1" * 246),
            False,
            True,
            False,
            True,
            False,
            False,
            id="pwc3_long_local_unbracketed_ip_len",
        ),
        pytest.param(
            ("a" * 63 + ".") * 3 + ("b" * 58) + ".com",
            True,
            True,
            True,
            False,
            True,
            False,
            id="pwc4_zero_at_long_hostname",
        ),
        pytest.param(
            ("a" * 65) + "[127.0.0.1]",
            False,
            False,
            False,
            True,
            False,
            False,
            id="pwc5_zero_at_bracketed_ip",
        ),
        pytest.param(
            "127.0.0.1",
            True,
            False,
            True,
            False,
            True,
            False,
            id="pwc6_zero_at_unbracketed_ip",
        ),
        pytest.param(
            "a@" + ("b" * 65) + "@example.com",
            False,
            True,
            True,
            True,
            False,
            False,
            id="pwc7_multi_at_long_local_host",
        ),
        pytest.param(
            "a@b@[::" + ("1" * 251) + "]",
            False,
            True,
            False,
            False,
            True,
            False,
            id="pwc8_multi_at_long_bracketed_ipv6",
        ),
        pytest.param(
            ("a" * 64) + "@b@127.0.0." + ("1" * 246),
            True,
            True,
            False,
            False,
            False,
            False,
            id="pwc9_multi_at_long_unbracketed_ip",
        ),
        pytest.param(
            ("a" * 65) + "@b@" + ("c" * 63 + ".") * 3 + ("d" * 58) + ".com",
            False,
            False,
            False,
            True,
            True,
            False,
            id="pwc10_multi_at_long_local_and_host",
        ),
    ],
)
def test_email_isp_pairwise(
    value,
    ipv4_address,
    ipv6_address,
    simple_host,
    rfc_1034,
    rfc_2782,
    is_valid,
):
    """Verify Pairwise Coverage (PWC) across all email ISP characteristics and option flags."""
    result = email(
        value,
        ipv4_address=ipv4_address,
        ipv6_address=ipv6_address,
        simple_host=simple_host,
        rfc_1034=rfc_1034,
        rfc_2782=rfc_2782,
    )
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


@pytest.mark.parametrize(
    ("value", "kwargs", "is_valid"),
    [
        pytest.param("someone@[127.0.0.1]", {"ipv4_address": True}, True, id="ipv4_on_bracketed"),
        pytest.param("someone@[127.0.0.1]", {"ipv4_address": False}, False, id="ipv4_off_bracketed"),
        pytest.param("someone@127.0.0.1", {"ipv4_address": True}, False, id="ipv4_on_unbracketed"),
        pytest.param("someone@[127.0.0.1]", {"ipv6_address": True}, False, id="ipv4_literal_with_ipv6_flag"),
        pytest.param("someone@example.com", {"ipv4_address": True}, False, id="ipv4_on_plain_hostname"),
        pytest.param("someone@[::1]", {"ipv6_address": True}, True, id="ipv6_on_bracketed"),
        pytest.param("someone@[2001:db8::1]", {"ipv6_address": True}, True, id="ipv6_on_full_bracketed"),
        pytest.param("someone@[::1]", {"ipv6_address": False}, False, id="ipv6_off_bracketed"),
        pytest.param("someone@::1", {"ipv6_address": True}, False, id="ipv6_on_unbracketed"),
        pytest.param("someone@[::1]", {"ipv4_address": True}, False, id="ipv6_literal_with_ipv4_flag"),
        pytest.param("someone@example.com", {"ipv6_address": True}, False, id="ipv6_on_plain_hostname"),
        pytest.param(
            "someone@[127.0.0.1]",
            {"ipv4_address": True, "ipv6_address": True},
            True,
            id="both_ip_flags_on_ipv4",
        ),
        pytest.param(
            "someone@[::1]",
            {"ipv4_address": True, "ipv6_address": True},
            True,
            id="both_ip_flags_on_ipv6",
        ),
        pytest.param("someone@localhost", {"simple_host": True}, True, id="simple_host_on_localhost"),
        pytest.param("someone@my-host-1", {"simple_host": True}, True, id="simple_host_on_hyphenated"),
        pytest.param("someone@localhost", {"simple_host": False}, False, id="simple_host_off_localhost"),
        pytest.param("someone@example.com.", {"rfc_1034": True}, True, id="rfc1034_on_trailing_dot"),
        pytest.param("someone@example.com.", {"rfc_1034": False}, False, id="rfc1034_off_trailing_dot"),
        pytest.param("someone@_http._tcp.example.com", {"rfc_2782": True}, True, id="rfc2782_on_underscore"),
        pytest.param("someone@_http._tcp.example.com", {"rfc_2782": False}, False, id="rfc2782_off_underscore"),
        pytest.param(
            "someone@_http._tcp.example.com.",
            {"simple_host": True, "rfc_1034": True, "rfc_2782": True},
            True,
            id="combined_simple_dot_service",
        ),
    ],
)
def test_email_isp_option_flags(value, kwargs, is_valid):
    """Ensure every option flag toggles matching valid and invalid domain forms."""
    result = email(value, **kwargs)
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
        # Predicate P1: A or B
        #   A: not value
        #   B: value.count("@") != 1
        #
        # Note: (A=T, B=F) is infeasible because an empty string cannot contain "@".
        # A satisfies PC and CC; B satisfies CACC via (A=F, B=T) vs (A=F, B=F).
        pytest.param("", False, id="empty_string"),                   # A=T (short-circuits B) -> P1=T
        pytest.param("someone.example.com", False, id="zero_at_signs"),  # A=F, B=T -> P1=T
        pytest.param("a@b@example.com", False, id="two_at_signs"),    # A=F, B=T -> P1=T
        pytest.param("someone@example.com", True, id="one_at_sign"),  # A=F, B=F -> P1=F
    ],
)
def test_logic_coverage_empty_and_at_count_predicate(value, is_valid):
    """CACC/CC/PC for the emptiness and '@' count input predicate."""
    result = email(value)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


@pytest.mark.parametrize(
    ("value", "is_valid"),
    [
        # Predicate P2: C or D
        #   C: len(username_part) > 64
        #   D: len(domain_part) > 253
        pytest.param(
            ("a" * 64) + "@" + ("b" * 63 + ".") * 3 + ("c" * 57) + ".com",
            True,
            id="both_within_limits",
        ),  # C=F, D=F -> P2=F
        pytest.param(
            ("a" * 65) + "@example.com",
            False,
            id="local_over_64_only",
        ),  # C=T, D=F -> P2=T
        pytest.param(
            "someone@" + ("b" * 63 + ".") * 3 + ("c" * 58) + ".com",
            False,
            id="domain_over_253_only",
        ),  # C=F, D=T -> P2=T
        pytest.param(
            ("a" * 65) + "@" + ("b" * 63 + ".") * 3 + ("c" * 58) + ".com",
            False,
            id="both_over_limits",
        ),  # C=T, D=T -> P2=T
    ],
)
def test_logic_coverage_length_predicate(value, is_valid):
    """CACC/CC/PC for the local-part and domain-part length predicate."""
    result = email(value)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


@pytest.mark.parametrize(
    ("value", "ipv6_address", "ipv4_address", "is_valid"),
    [
        # Predicate P3: E or F
        #   E: ipv6_address
        #   F: ipv4_address
        pytest.param("someone@[127.0.0.1]", False, False, False, id="both_flags_off_ipv4_fails"),  # E=F, F=F -> P3=F
        pytest.param("someone@[127.0.0.1]", False, True, True, id="ipv4_flag_on_valid"),           # E=F, F=T -> P3=T
        pytest.param("someone@[::1]", False, False, False, id="both_flags_off_ipv6_fails"),        # E=F, F=F -> P3=F
        pytest.param("someone@[::1]", True, False, True, id="ipv6_flag_on_valid"),                 # E=T, F=F -> P3=T
        pytest.param("someone@[127.0.0.1]", True, True, True, id="both_flags_on_ipv4_valid"),      # E=T, F=T -> P3=T
        pytest.param("someone@[::1]", True, True, True, id="both_flags_on_ipv6_valid"),            # E=T, F=T -> P3=T
    ],
)
def test_logic_coverage_ip_flag_predicate(value, ipv6_address, ipv4_address, is_valid):
    """CACC/CC/PC for the ipv6_address or ipv4_address predicate."""
    result = email(value, ipv6_address=ipv6_address, ipv4_address=ipv4_address)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


@pytest.mark.parametrize(
    ("value", "is_valid"),
    [
        # Predicate P4: G and H
        #   G: domain_part.startswith("[")
        #   H: domain_part.endswith("]")
        pytest.param("someone@[127.0.0.1]", True, id="both_brackets_present"),      # G=T, H=T -> P4=T
        pytest.param("someone@[127.0.0.1", False, id="missing_closing_bracket"),   # G=T, H=F -> P4=F
        pytest.param("someone@127.0.0.1]", False, id="missing_opening_bracket"),   # G=F, H=T -> P4=F
        pytest.param("someone@127.0.0.1", False, id="both_brackets_missing"),      # G=F, H=F -> P4=F
    ],
)
def test_logic_coverage_bracket_predicate(value, is_valid):
    """CACC/CC/PC for the bracketed IP literal check."""
    result = email(value, ipv4_address=True)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)


# ---------------------------------------------------------------------------
# 4. Boundary, Branch, and Mutation-Killing Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "kwargs", "is_valid"),
    [
        # Length boundaries
        pytest.param("a@example.com", {}, True, id="local_1_char"),
        pytest.param(("a" * 64) + "@example.com", {}, True, id="local_64_chars"),
        pytest.param(("a" * 65) + "@example.com", {}, False, id="local_65_chars"),
        pytest.param(
            "someone@" + ("b" * 63 + ".") * 3 + ("c" * 57) + ".com",
            {},
            True,
            id="domain_253_chars",
        ),
        pytest.param(
            "someone@" + ("b" * 63 + ".") * 3 + ("c" * 56) + ".com.",
            {"rfc_1034": True},
            True,
            id="domain_253_chars_with_dot",
        ),
        pytest.param(
            "someone@" + ("b" * 63 + ".") * 3 + ("c" * 58) + ".com",
            {},
            False,
            id="domain_254_chars",
        ),
        pytest.param(
            "someone@" + ("b" * 63 + ".") * 3 + ("c" * 57) + ".com.",
            {"rfc_1034": True},
            False,
            id="domain_253_plus_dot_over_253",
        ),
        # Split & @-sign structure
        pytest.param("@example.com", {}, False, id="empty_local_part"),
        pytest.param("someone@", {}, False, id="empty_domain_part"),
        pytest.param("@", {}, False, id="only_at_sign"),
        pytest.param('"user@inner"@example.com', {}, False, id="quoted_extra_at_sign"),
        # IP literal & hostname delegation checks (may_have_port=False, cidr=False)
        pytest.param("someone@[]", {"ipv4_address": True}, False, id="empty_brackets"),
        pytest.param("someone@[999.0.0.1]", {"ipv4_address": True}, False, id="invalid_ipv4_literal"),
        pytest.param("someone@[127.0.0.1/24]", {"ipv4_address": True}, False, id="ipv4_cidr_rejected"),
        pytest.param("someone@example.com:8080", {}, False, id="port_on_hostname"),
        pytest.param("someone@[127.0.0.1]:8080", {"ipv4_address": True}, False, id="port_outside_brackets"),
        pytest.param("someone@[127.0.0.1:8080]", {"ipv4_address": True}, False, id="port_inside_brackets"),
        # Local-part branch 1 & 2: Extended Latin and fullmatch vs match killers
        pytest.param("\u00e9@example.com", {}, True, id="ext_latin_single_u00e9"),
        pytest.param("\u0100@example.com", {}, True, id="ext_latin_single_u0100"),
        pytest.param("\u0180@example.com", {}, True, id="ext_latin_single_u0180"),
        pytest.param("jos\u00e9@example.com", {}, True, id="ext_latin_multi_char"),
        pytest.param("\u00e9 space@example.com", {}, False, id="ext_latin_trailing_space_fullmatch"),
        pytest.param("\u00e9\n@example.com", {}, False, id="ext_latin_trailing_newline_fullmatch"),
        pytest.param("\u043f\u0440\u0438\u0432\u0435\u0442@example.com", {}, False, id="cyrillic_local_rejected"),
        pytest.param("someone@m\u00fcnchen.de", {}, True, id="idn_domain_valid"),
        # Local-part branch 2: Dot-atom characters and invalid delimiters
        pytest.param("UPPER.Case_123@example.com", {}, True, id="uppercase_dot_atom"),
        pytest.param("first.middle.last@example.com", {}, True, id="multiple_dots"),
        pytest.param("a!#$%&'*+/=?^_`{|}~-z@example.com", {}, True, id="all_atext_specials"),
        pytest.param(".leadingdot@example.com", {}, False, id="leading_dot"),
        pytest.param("trailingdot.@example.com", {}, False, id="trailing_dot"),
        pytest.param("double..dot@example.com", {}, False, id="consecutive_dots"),
        pytest.param("has space@example.com", {}, False, id="internal_space"),
        pytest.param("someone\n@example.com", {}, False, id="trailing_newline"),
        pytest.param("bad(paren)@example.com", {}, False, id="paren_in_dot_atom"),
        pytest.param("bad,comma@example.com", {}, False, id="comma_in_dot_atom"),
        pytest.param("bad:colon@example.com", {}, False, id="colon_in_dot_atom"),
        pytest.param("bad;semi@example.com", {}, False, id="semicolon_in_dot_atom"),
        pytest.param("bad<angle>@example.com", {}, False, id="angle_brackets_in_dot_atom"),
        pytest.param("bad[bracket]@example.com", {}, False, id="square_brackets_in_dot_atom"),
        pytest.param("bad\\slash@example.com", {}, False, id="backslash_in_dot_atom"),
        # Local-part branch 3: Quoted-string rules
        pytest.param('""@example.com', {}, True, id="quoted_empty"),
        pytest.param('"simple"@example.com', {}, True, id="quoted_simple"),
        pytest.param('"john..doe"@example.com', {}, True, id="quoted_consecutive_dots"),
        pytest.param('"first.last."@example.com', {}, True, id="quoted_trailing_dot"),
        pytest.param('"(parens),:;<>[text]"@example.com', {}, True, id="quoted_special_chars"),
        pytest.param('"caf\u00e9"@example.com', {}, True, id="quoted_ext_latin"),
        pytest.param(r'"escaped\."@example.com', {}, True, id="quoted_escaped_dot"),
        pytest.param('"escaped\\\t"@example.com', {}, True, id="quoted_escaped_tab"),
        pytest.param('"unclosed@example.com', {}, False, id="quoted_unclosed"),
        pytest.param('unopened"@example.com', {}, False, id="quoted_unopened"),
        pytest.param('"outer"extra@example.com', {}, False, id="quoted_trailing_text"),
        pytest.param('extra"inner"@example.com', {}, False, id="quoted_leading_text"),
        pytest.param('"has space"@example.com', {}, False, id="quoted_space_rejected"),
        pytest.param(r'"has\"quote"@example.com', {}, False, id="quoted_escaped_quote_rejected"),
        pytest.param(r'"has\a"@example.com', {}, False, id="quoted_escaped_letter_rejected"),
    ],
)
def test_email_boundaries_and_local_part_regex(value, kwargs, is_valid):
    """Test length boundaries, IP/hostname delegation limits, and all local-part regex branches."""
    result = email(value, **kwargs)
    if is_valid:
        assert result is True
    else:
        _assert_invalid(result)
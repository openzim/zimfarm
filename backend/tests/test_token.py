# ruff: noqa: E501
from contextlib import nullcontext as does_not_raise

import pytest
from _pytest.python_api import RaisesContext
from cryptography.hazmat.primitives.asymmetric import dsa

from zimfarm_backend.exceptions import PublicKeyLoadError
from zimfarm_backend.utils.token import get_public_key_type, load_public_key


@pytest.mark.parametrize(
    "public_key,expected",
    [
        # Valid public rsa key in openSSH format
        pytest.param(
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCviQIFpu2khxOqyhChlIk6J7cr3K6PzJV5qYScZF3SeVYR0gdEM0ySwCCWarHAJ72BpbnMrhKj6/7vl3MjNcIngxsEiyzFda46YqG1svYQoyk0PsTUeNS1TAp3MluRCZ/tXSlaDt0lDG/YCSj7B3qS4w8s7ko73srvJe7Cml2yq7DbcnDODKCF4ovMtTyxLvEv81qN3wnWVzY1Es0NVH6Cq/rFan/2FDRyjDxEybiUS/Rn0MTf2QKNSURlzXdWPn8y9VmYrA/IwjWeMKfedUuTGdXqODwKj6b/MzMzzkCPBwP9YBMiiypucnPIFlZoGTxj1Dye9lGuyaAnWGJ2Q4SeLXB4HA3WcHFyqDJFcCfgljiUOZgnx5bl6IMiGhofVhfmOloWmrDUXygztOjkJ+0Mq1PpFarCIE2LqfYQw4L5sQZ7gzdn7Fyk0zHfKFg3tLaQLDn5J5NFyuQqXp8F1qYw7hY0x1wb7RsVTdhEq5c0iQ7i6IxruxV19D6izyj0JGtUacLYeVpjxPnw+iCqTTPAHjEDx/6D86pyZQ4z/WBPZI+In1JCSiViuIMF8J9y7NaVypB06UWuua2dY6HcSv7khgBOK5S+v6dg0YullBqAsiQ0N4GiiXsfrgnYCeNhs7ztjWPIjPO0TRcWCnzuCO68wu53x3Ioy539PW6ng89q9Q== elf@imladrisj",
            does_not_raise(),
            id="valid-rsa-openssh-key",
        ),
        # Valid public ECDSA  key in openSSH format
        pytest.param(
            "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBL5QqA6K6X3JZyyxlznmfnwHYFzMC4elWdY0zSorkjVAFtqllHv2nLGGSgPIQ8WpsOp0ZLbV2QTggjUfxgX9PfI= elf@imladris",
            does_not_raise(),
            id="valid-ecdsa-openssh_key",
        ),
        # Valid public RSA key in PEM format
        pytest.param(
            """
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAr4kCBabtpIcTqsoQoZSJ
Oie3K9yuj8yVeamEnGRd0nlWEdIHRDNMksAglmqxwCe9gaW5zK4So+v+75dzIzXC
J4MbBIssxXWuOmKhtbL2EKMpND7E1HjUtUwKdzJbkQmf7V0pWg7dJQxv2Ako+wd6
kuMPLO5KO97K7yXuwppdsquw23JwzgygheKLzLU8sS7xL/Najd8J1lc2NRLNDVR+
gqv6xWp/9hQ0cow8RMm4lEv0Z9DE39kCjUlEZc13Vj5/MvVZmKwPyMI1njCn3nVL
kxnV6jg8Co+m/zMzM85AjwcD/WATIosqbnJzyBZWaBk8Y9Q8nvZRrsmgJ1hidkOE
ni1weBwN1nBxcqgyRXAn4JY4lDmYJ8eW5eiDIhoaH1YX5jpaFpqw1F8oM7To5Cft
DKtT6RWqwiBNi6n2EMOC+bEGe4M3Z+xcpNMx3yhYN7S2kCw5+SeTRcrkKl6fBdam
MO4WNMdcG+0bFU3YRKuXNIkO4uiMa7sVdfQ+os8o9CRrVGnC2HlaY8T58Pogqk0z
wB4xA8f+g/OqcmUOM/1gT2SPiJ9SQkolYriDBfCfcuzWlcqQdOlFrrmtnWOh3Er+
5IYATiuUvr+nYNGLpZQagLIkNDeBool7H64J2AnjYbO87Y1jyIzztE0XFgp87gju
vMLud8dyKMud/T1up4PPavUCAwEAAQ==
-----END PUBLIC KEY-----
""",
            does_not_raise(),
            id="valid-rsa-in-pem-format",
        ),
        # Invalid key
        pytest.param(
            "ssh-rsa NOTAREALBASE64 user@example.com",
            pytest.raises(PublicKeyLoadError),
            id="invalid-key",
        ),
        # Valid Ed25519 key
        pytest.param(
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIId3y4Xfr6yNlJpFb1EN4w9tGf38HRJND4qYuou04ubD elf@imladris",
            does_not_raise(),
            id="valid-ed25519",
        ),
    ],
)
def test_load_public_key(public_key: str, expected: RaisesContext[Exception]):
    with expected:
        load_public_key(bytes(public_key, encoding="ascii"))


@pytest.mark.parametrize(
    "public_key,expected",
    [
        pytest.param(
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIId3y4Xfr6yNlJpFb1EN4w9tGf38HRJND4qYuou04ubD elf@imladris",
            "ED25519",
            id="valid-ed25519",
        ),
        pytest.param(
            "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBL5QqA6K6X3JZyyxlznmfnwHYFzMC4elWdY0zSorkjVAFtqllHv2nLGGSgPIQ8WpsOp0ZLbV2QTggjUfxgX9PfI= elf@imladris",
            "ECDSA",
            id="valid-ecdsa-openssh_key",
        ),
        pytest.param(
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCviQIFpu2khxOqyhChlIk6J7cr3K6PzJV5qYScZF3SeVYR0gdEM0ySwCCWarHAJ72BpbnMrhKj6/7vl3MjNcIngxsEiyzFda46YqG1svYQoyk0PsTUeNS1TAp3MluRCZ/tXSlaDt0lDG/YCSj7B3qS4w8s7ko73srvJe7Cml2yq7DbcnDODKCF4ovMtTyxLvEv81qN3wnWVzY1Es0NVH6Cq/rFan/2FDRyjDxEybiUS/Rn0MTf2QKNSURlzXdWPn8y9VmYrA/IwjWeMKfedUuTGdXqODwKj6b/MzMzzkCPBwP9YBMiiypucnPIFlZoGTxj1Dye9lGuyaAnWGJ2Q4SeLXB4HA3WcHFyqDJFcCfgljiUOZgnx5bl6IMiGhofVhfmOloWmrDUXygztOjkJ+0Mq1PpFarCIE2LqfYQw4L5sQZ7gzdn7Fyk0zHfKFg3tLaQLDn5J5NFyuQqXp8F1qYw7hY0x1wb7RsVTdhEq5c0iQ7i6IxruxV19D6izyj0JGtUacLYeVpjxPnw+iCqTTPAHjEDx/6D86pyZQ4z/WBPZI+In1JCSiViuIMF8J9y7NaVypB06UWuua2dY6HcSv7khgBOK5S+v6dg0YullBqAsiQ0N4GiiXsfrgnYCeNhs7ztjWPIjPO0TRcWCnzuCO68wu53x3Ioy539PW6ng89q9Q== elf@imladrisj",
            "RSA",
            id="valid-rsa-openssh-key",
        ),
    ],
)
def test_get_public_key_type(public_key: str, expected: RaisesContext[Exception]):
    key = load_public_key(bytes(public_key, encoding="ascii"))
    assert get_public_key_type(key) == expected


def test_public_key_type_invalid_key():
    with pytest.raises(ValueError):
        get_public_key_type(dsa.generate_private_key(key_size=2048).public_key())

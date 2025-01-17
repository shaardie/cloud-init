"""Integration test for the wireguard module."""
import pytest
from pycloudlib.lxd.instance import LXDInstance

from cloudinit.subp import subp
from tests.integration_tests.instances import IntegrationInstance

ASCII_TEXT = "ASCII text"

USER_DATA = """\
#cloud-config
wireguard:
  interfaces:
    - name: wg0
      config_path: /etc/wireguard/wg0.conf
      content: |
        [Interface]
        Address = 192.168.254.1/32
        ListenPort = 51820
        PrivateKey = iNlmgtGo6yiFhD9TuVnx/qJSp+C5Cwg4wwPmOJwlZXI=

        [Peer]
        PublicKey = 6PewunPjxlUq/0xvbVxklN2p73YIytfjxpoIEohCukY=
        AllowedIPs = 192.168.254.2/32
    - name: wg1
      config_path: /etc/wireguard/wg1.conf
      content: |
        [Interface]
        PrivateKey = GGLU4+5vIcK9lGyfz4AJn9fR5/FN/6sf4Fd5chZ16Vc=
        Address = 192.168.254.2/24

        [Peer]
        PublicKey = 2as8z3EDjSsfFEkvOQGVnJ1Hv+h1jRAh2BKJg+DHvGk=
        Endpoint = 127.0.0.1:51820
        AllowedIPs = 0.0.0.0/0
  readinessprobe:
    - ping -qc 5 192.168.254.1 2>&1 > /dev/null
    - echo $? > /tmp/ping
"""


def load_wireguard_kernel_module_lxd(instance: LXDInstance):
    subp(
        "lxc config set {} linux.kernel_modules wireguard".format(
            instance.name
        ).split()
    )


@pytest.mark.ci
@pytest.mark.user_data(USER_DATA)
@pytest.mark.lxd_vm
@pytest.mark.gce
@pytest.mark.ec2
@pytest.mark.azure
@pytest.mark.openstack
@pytest.mark.oci
@pytest.mark.ubuntu
class TestWireguard:
    @pytest.mark.parametrize(
        "cmd,expected_out",
        (
            # check if wireguard module is loaded
            ("lsmod | grep '^wireguard' | awk '{print $1}'", "wireguard"),
            # test if file was written for wg0
            (
                "stat -c '%N' /etc/wireguard/wg0.conf",
                r"'/etc/wireguard/wg0.conf'",
            ),
            # check permissions for wg0
            ("stat -c '%U %a' /etc/wireguard/wg0.conf", r"root 600"),
            # ASCII check wg1
            ("file /etc/wireguard/wg1.conf", ASCII_TEXT),
            # md5sum check wg1
            (
                "md5sum </etc/wireguard/wg1.conf",
                "cff31c9879da0967313d3f561aed766b",
            ),
            # sha256sum check
            (
                "sha256sum </etc/wireguard/wg1.conf",
                "8443055d1442d051588beb03f7895b58"
                "269196eb9916617969dc5220c1a90d54",
            ),
            # check if systemd started wg0
            ("systemctl is-active wg-quick@wg0", "active"),
            # check if systemd started wg1
            ("systemctl is-active wg-quick@wg1", "active"),
            # check readiness probe (ping wg0)
            ("cat /tmp/ping", "0"),
        ),
    )
    def test_wireguard(
        self, cmd, expected_out, class_client: IntegrationInstance
    ):
        result = class_client.execute(cmd)
        assert result.ok
        assert expected_out in result.stdout

    def test_wireguard_tools_installed(
        self, class_client: IntegrationInstance
    ):
        """Test that 'wg version' succeeds, indicating installation."""
        assert class_client.execute("wg version").ok


@pytest.mark.ci
@pytest.mark.user_data(USER_DATA)
@pytest.mark.lxd_setup.with_args(load_wireguard_kernel_module_lxd)
@pytest.mark.lxd_container
@pytest.mark.ubuntu
class TestWireguardWithoutKmod:
    def test_wireguard_tools_installed(
        self, class_client: IntegrationInstance
    ):
        """Test that 'wg version' succeeds, indicating installation."""
        assert class_client.execute("wg version").ok

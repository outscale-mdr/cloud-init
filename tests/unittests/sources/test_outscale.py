# This file is part of cloud-init. See LICENSE file for license information.

import functools
import os
from unittest import mock

import httpretty

from cloudinit import helpers
from cloudinit.sources import DataSourceOutscale as osc
from tests.unittests import helpers as test_helpers

DEFAULT_METADATA = {
 "ami-id": "ami-504e6b16",
 "ami-launch-index": "0",
 "ami-manifest-path": "(unknown)",
 "block-device-mapping": {
  "ami": "/dev/sda1",
  "ebs1": "/dev/xvdb",
  "root": "/dev/sda1"
 },
 "hostname": "ip.eu-west-2.compute.internal",
 "iam": {},
 "instance-action": "none",
 "instance-id": "i-xxxxxx",
 "instance-type": "tinav4.c8r16p2",
 "kernel-id": "(unknown)",
 "local-hostname": "ip.eu-west-2.compute.internal",
 "local-ipv4": "0.0.0.0",
 "mac": "ff:ff:ff:ff:ff:ff",
 "network": {
  "interfaces": {
   "macs": {
    "ff:ff:ff:ff:ff:ff": {
     "device-number": "0",
     "gateway-ipv4": "0.0.0.0",
     "interface-id": "eni-xxxxxx",
     "ipv4-associations": {
      "0.0.0.0": "0.0.0.0"
     },
     "ipv6s": "",
     "local-hostname": "ip.eu-west-2.compute.internal",
     "local-ipv4s": "0.0.0.0",
     "mac": "ff:ff:ff:ff:ff:ff",
     "owner-id": "XXXXXXXXXXXX",
     "public-hostname": "ows-ip.eu-west-2.compute.outscale.com",
     "public-ipv4s": "0.0.0.0",
     "security-group-ids": "sg-id",
     "security-groups": "security_group",
     "subnet-id": "",
     "subnet-ipv4-cidr-block": "",
     "subnet-ipv6-cidr-blocks": "",
     "vpc-id": "OK",
     "vpc-ipv4-cidr-blocks": "",
     "vpc-ipv6-cidr-blocks": ""
    }
   }
  }
 },
 "placement": {
  "availability-zone": "eu-west-2a",
  "cluster": "56bd90f41a8dd3ccbe83ab8ab4155c45b8e0f67c",
  "server": "f456950a8b125ed6a3bedcec57b46039d4153b1a"
 },
 "public-hostname": "ows-ip.eu-west-2.compute.outscale.com",
 "public-ipv4": "0.0.0.0",
 "public-keys": {
  "dev_debian": "ssh-rsa AAAAB3...NZ test"
 },
 "ramdisk-id": "(unknown)",
 "reservation-id": "r-xxxxxxxx",
 "security-groups": "security_group",
 "services": {},
 "spot": {},
 "tags": {
  "name": "dev-debian"
 }
}

DEFAULT_USERDATA = """\
#cloud-config

hostname: localhost"""


def register_mock_metaserver(base_url, data):
    def register_helper(register, base_url, body):
        if isinstance(body, str):
            register(base_url, body)
        elif isinstance(body, list):
            register(base_url.rstrip("/"), "\n".join(body) + "\n")
        elif isinstance(body, dict):
            if not body:
                register(
                    base_url.rstrip("/") + "/", "not found", status_code=404
                )
            vals = []
            for k, v in body.items():
                if isinstance(v, (str, list)):
                    suffix = k.rstrip("/")
                else:
                    suffix = k.rstrip("/") + "/"
                vals.append(suffix)
                url = base_url.rstrip("/") + "/" + suffix
                register_helper(register, url, v)
            register(base_url, "\n".join(vals) + "\n")

    register = functools.partial(httpretty.register_uri, httpretty.GET)
    register_helper(register, base_url, data)


class TestOutscaleDataSource(test_helpers.HttprettyTestCase):
    def setUp(self):
        super(TestOutscaleDataSource, self).setUp()
        cfg = {"datasource": {"Outscale": {"timeout": "0.1", "max_wait": "1"}}}
        distro = {}
        paths = helpers.Paths({"run_dir": self.tmp_dir()})
        self.ds = osc.DataSourceOutscale(cfg, distro, paths)
        self.metadata_address = self.ds.metadata_urls[0]

    @property
    def default_metadata(self):
        return DEFAULT_METADATA

    @property
    def default_userdata(self):
        return DEFAULT_USERDATA

    @property
    def metadata_url(self):
        return (
            os.path.join(
                self.metadata_address,
                self.ds.extended_metadata_versions[0],
                "meta-data",
            )
            + "/"
        )

    @property
    def min_metadata_url(self):
        return (
            os.path.join(
                self.metadata_address,
                self.ds.min_metadata_version,
                "meta-data",
            )
            + "/"
        )
    @property
    def userdata_url(self):
        return os.path.join(
            self.metadata_address, self.ds.extended_metadata_versions[0], "user-data"
        )

    # EC2 provides an instance-identity document which must return 404 here
    # for this test to pass.
    @property
    def default_identity(self):
        return {}

    @property
    def identity_url(self):
        return os.path.join(
            self.metadata_address,
            self.ds.extended_metadata_versions[0],
            "dynamic",
            "instance-identity",
        )

    def regist_default_server(self):
        register_mock_metaserver(self.metadata_url, self.default_metadata)
        register_mock_metaserver(self.min_metadata_url, self.default_metadata)
        register_mock_metaserver(self.userdata_url, self.default_userdata)
        register_mock_metaserver(self.identity_url, self.default_identity)

    def _test_get_data(self):
        self.assertEqual(self.ds.metadata, self.default_metadata)
        self.assertEqual(
            self.ds.userdata_raw, self.default_userdata.encode("utf8")
        )

    @mock.patch("cloudinit.sources.DataSourceOutscale._is_outscale")
    def test_with_mock_server(self, m_is_outscale):
        m_is_outscale.return_value = True
        self.regist_default_server()
        ret = self.ds.get_data()
        self.assertEqual(True, ret)
        self.assertEqual(1, m_is_outscale.call_count)
        self._test_get_data()
        self.assertEqual("outscale", self.ds.cloud_name)
        self.assertEqual("ec2", self.ds.platform)

    @mock.patch("cloudinit.sources.DataSourceOutscale._is_outscale")
    def test_returns_false_when_not_on_outscale(self, m_is_outscale):
        """If is_outscale returns false, then get_data should return False."""
        m_is_outscale.return_value = False
        self.regist_default_server()
        ret = self.ds.get_data()
        self.assertEqual(1, m_is_outscale.call_count)
        self.assertEqual(False, ret)


class TestIsOutscale(test_helpers.CiTestCase):
    read_dmi_data_expected = [mock.call("system-uuid")]

    @mock.patch("cloudinit.sources.DataSourceOutscale.dmi.read_dmi_data")
    def test_true_on_outscale_product(self, m_read_dmi_data):
        """Should return true if the dmi product data has expected value."""
        m_read_dmi_data.return_value = "oscetlasuite"
        ret = osc._is_outscale()
        self.assertEqual(
            self.read_dmi_data_expected, m_read_dmi_data.call_args_list
        )
        self.assertEqual(True, ret)

    @mock.patch("cloudinit.sources.DataSourceOutscale.dmi.read_dmi_data")
    def test_false_on_empty_string(self, m_read_dmi_data):
        """Should return false on empty value returned."""
        m_read_dmi_data.return_value = ""
        ret = osc._is_outscale()
        self.assertEqual(
            self.read_dmi_data_expected, m_read_dmi_data.call_args_list
        )
        self.assertEqual(False, ret)

    @mock.patch("cloudinit.sources.DataSourceOutscale.dmi.read_dmi_data")
    def test_false_on_unknown_string(self, m_read_dmi_data):
        """Should return false on an unrelated string."""
        m_read_dmi_data.return_value = "pas osc dedans"
        ret = osc._is_outscale()
        self.assertEqual(
            self.read_dmi_data_expected, m_read_dmi_data.call_args_list
        )
        self.assertEqual(False, ret)


# vi: ts=4 expandtab

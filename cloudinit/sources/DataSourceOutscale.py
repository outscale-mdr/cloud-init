# This file is part of cloud-init. See LICENSE file for license information.

from cloudinit import dmi, sources
from cloudinit.sources import DataSourceEc2 as EC2
from cloudinit.sources.helpers import ec2
from cloudinit import util, warnings
from cloudinit import log as logging
from cloudinit import url_helper as uhelp

OUTSCALE_CLOUD_NAME = "outscale"
OUTSCALE_SYSTEM_UUID_PREFIX = "osc"

LOG = logging.getLogger(__name__)


class DataSourceOutscale(EC2.DataSourceEc2):

    dsname = "Outscale"

    extended_metadata_versions = ["2016-09-02"]

    def _get_cloud_name(self):
        if _is_outscale():
            return OUTSCALE_CLOUD_NAME
        else:
            return EC2.CloudNames.NO_EC2_METADATA

    def crawl_metadata(self):
        """Crawl metadata service when available.

        @returns: Dictionary of crawled metadata content containing the keys:
          meta-data, user-data and dynamic.
        """
        def _skip_on_tag_errors(exception):
            if isinstance(exception, uhelp.UrlError) and exception.code == 404:
                if "meta-data/tags/" in exception.url:
                    return True
            return False
        if not self.wait_for_metadata_service():
            return {}
        api_version = self.get_metadata_api_version()
        crawled_metadata = {}
        try:
            crawled_metadata["user-data"] = ec2.get_instance_userdata(
                api_version,
                self.metadata_address,
            )
            crawled_metadata["meta-data"] = ec2.get_instance_metadata(
                api_version,
                self.metadata_address,
                skip_cb=_skip_on_tag_errors
            )
        except Exception:
            util.logexc(
                LOG,
                "Failed reading from metadata address %s",
                self.metadata_address,
            )
            return {}
        crawled_metadata["_metadata_api_version"] = api_version
        return crawled_metadata

def _is_outscale():
    return dmi.read_dmi_data("system-uuid").startswith(OUTSCALE_SYSTEM_UUID_PREFIX)


# Used to match classes to dependencies
datasources = [
    (DataSourceOutscale, (sources.DEP_FILESYSTEM, sources.DEP_NETWORK)),
]


# Return a list of data sources that match this set of dependencies
def get_datasource_list(depends):
    return sources.list_from_depends(depends, datasources)


# vi: ts=4 expandtab

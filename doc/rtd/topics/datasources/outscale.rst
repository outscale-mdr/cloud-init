.. _datasource_outscale:

3DS Outscale (Outscale)
======================
The ``Outscale`` datasource reads data from 3DS Outscale.  Support is
present in cloud-init since 0.7.9.

Metadata Service
----------------
The Outscale metadata service is available at the well known url
``http://169.254.169.254/``. For more information see
3DS Outscale on `metadata
<https://docs.outscale.com/en/userguide/Accessing-the-Metadata-and-User-Data-of-an-Instance.html>`__.

Configuration
-------------
The following configuration can be set for the datasource in system
configuration (in ``/etc/cloud/cloud.cfg`` or ``/etc/cloud/cloud.cfg.d/``).

An example configuration with the default values is provided below:

.. sourcecode:: yaml

  datasource:
    Outscale:
      metadata_urls: ["http://169.254.169.254/"]
      timeout: 50
      max_wait: 120

Versions
^^^^^^^^
Like the EC2 metadata service, 3DS Outscale's metadata service provides
versioned data under specific paths. Multiple EC2 Metadata versions of this data provided
to instances.

To see which versions are supported from your cloud provider use the following
URL:

::

    GET http://169.254.169.254/
    1.0
    2007-01-19
    2007-03-01
    2007-08-29
    2007-10-10
    2007-12-15
    2008-02-01
    2008-09-01
    2009-04-04
    ...
    latest


Cloud-init uses the ``2016-09-02`` version.

Metadata
^^^^^^^^
Instance metadata can be queried at
``http://169.254.169.254/2016-09-02/meta-data``

.. code-block:: shell-session

    $ curl http://169.254.169.254/2016-09-02/meta-data
    ami-id
    ami-launch-index
    ami-manifest-path
    block-device-mapping/
    hostname
    instance-action
    instance-id
    instance-type
    kernel-id
    local-hostname
    local-ipv4
    mac
    network/
    placement/
    public-hostname
    public-ipv4
    public-keys/
    ramdisk-id
    reservation-id
    security-groups
    tags/
    iam/
    services/

Userdata
^^^^^^^^
If provided, user-data will appear at
``http://169.254.169.254/2016-09-02/user-data``.
If no user-data is provided, this will return an empty string.

.. code-block:: shell-session

    $ http://169.254.169.254/2016-09-02/user-data
    #!/bin/sh
    echo "Hello World."

.. vi: textwidth=79

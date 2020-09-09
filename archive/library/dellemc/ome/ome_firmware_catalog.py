#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.0.12
# Copyright (C) 2019 Dell Inc. or its subsidiaries. All Rights Reserved.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ome_firmware_catalog
short_description: Creates a catalog on OpenManage Enterprise.
version_added: "2.9"
description: This module triggers the job to create a catalog on OpenManage Enterprise.
options:
  hostname:
    description: Target IP Address or hostname.
    type: str
    required: true
  username:
    description: Target username.
    type: str
    required: true
  password:
    description: Target user password.
    type: str
    required: true
  port:
    description: Target HTTPS port.
    type: int
    default: 443
  catalog_name:
    type: str
    description:
      - Name of the firmware catalog being created.
  catalog_description:
    type: str
    description:
      - Description of the catalog being created.
  source:
    type: str
    description:
      - The share address of the system where the firmware catalog is stored on the network.
  source_path:
    type: str
    description:
      - Full Path of the catalog file location excluding file name.
  file_name:
    type: str
    description:
      - Catalog file name relative to the I(source_path).
  repository_type:
    type: str
    description:
      - Type of Repository. The type supported are HTTP, NFS, CIFS, HTTPS
    choices: ["HTTP", "NFS", "CIFS", "HTTPS"]
    default: "HTTPS"
  repository_username:
    type: str
    description:
      - User name of the repository where the catalog is stored.
      - This option is mandatory when I(repository_type) is CIFS.
  repository_password:
    type: str
    description:
      - Password to access the repository.
      - This option is mandatory when I(repository_type) is CIFS.
  repository_domain:
    type: str
    description:
      - Domain name of the repository.
  check_certificate:
    type: bool
    description:
      - Specifies if certificate warnings are ignored when I(repository_type) is HTTPS.If C(True) option is set,
            then the certificate warnings are ignored otherwise certificate warnings are not ignored.
    default: False
requirements:
    - "python >= 2.7.5"
author: "Sajna Shetty(@Sajna-Shetty)"
'''

EXAMPLES = r'''
---
- name: create catalog from repository on a HTTPS.
  ome_firmware_catalog:
    hostname: "192.168.0.1"
    username: "username"
    catalog_name: "catalog_name"
    catalog_description: "catalog_description"
    repository_type: "HTTPS"
    source: "downloads.dell.com"
    source_path: "catalog"
    file_name: "catalog.gz"
    check_certificate: True

- name: create catalog from repository on a HTTP.
  ome_firmware_catalog:
    hostname: "192.168.0.1"
    username: "username"
    catalog_name: "catalog_name"
    catalog_description: "catalog_description"
    repository_type: "HTTP"
    source: "downloads.dell.com"
    source_path: "catalog"
    file_name: "catalog.gz"

- name: create catalog from CIFS network share.
  ome_firmware_catalog:
    hostname: "192.168.0.1"
    username: "username"
    catalog_name: "catalog_name"
    catalog_description: "catalog_description"
    repository_type: "CIFS"
    source: "192.167.0.1"
    source_path: "cifs/R940"
    file_name: "catalog.gz"
    repository_username: "repository_username"
    repository_password: "repository_password"
    repository_domain: "repository_domain"

- name: create catalog from NFS network share.
  ome_firmware_catalog:
    hostname: "192.168.0.1"
    username: "username"
    catalog_name: "catalog_name"
    catalog_description: "catalog_description"
    repository_type: "NFS"
    source: "192.166.0.2"
    source_path: "/nfs/R940"
    file_name: "catalog.xml"


'''

RETURN = r'''
---
msg:
  description: Overall status of the firmware catalog creation
  returned: always
  type: str
  sample: "Successfully triggered the job to create a catalog with Task Id : 10094"
catalog_status:
  description: Details of the catalog creation.
  returned: on success
  type: dict
  sample:  {
        "AssociatedBaselines": [],
        "BaseLocation": null,
        "BundlesCount": 0,
        "Filename": "catalog.gz",
        "Id": 0,
        "LastUpdated": null,
        "ManifestIdentifier": null,
        "ManifestVersion": null,
        "NextUpdate": null,
        "PredecessorIdentifier": null,
        "ReleaseDate": null,
        "ReleaseIdentifier": null,
        "Repository": {
            "CheckCertificate": true,
            "Description": "HTTPS Desc",
            "DomainName": null,
            "Id": null,
            "Name": "catalog4",
            "Password": null,
            "RepositoryType": "HTTPS",
            "Source": "company.com",
            "Username": null
        },
        "Schedule": null,
        "SourcePath": "catalog",
        "Status": null,
        "TaskId": 10094
    }
error_info:
  type: dict
  description: Details of http error.
  returned: on http error
  sample:  {
        "error": {
            "@Message.ExtendedInfo": [
                {
                    "Message": "Unable to create or update the catalog because a
                    repository with the same name already exists.",
                    "Resolution": "Enter a different name and retry the operation.",
                    "Severity": "Critical"
                }
            ],
            "code": "Base.1.0.GeneralError",
            "message": "A general error has occurred. See ExtendedInfo for more information."
        }
    }

'''

import json
from ssl import SSLError
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.dellemc.ome import RestOME
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import ConnectionError, SSLValidationError


def _get_catalog_payload(params):
    catalog_mapper = {
        "catalog_name": "Name",
        "catalog_description": "Description",
        "repository_type": "RepositoryType",
        "source": "Source",
        "repository_domain": "DomainName",
        "repository_username": "Username",
        "repository_password": "Password",
        "check_certificate": "CheckCertificate",
        "file_name": "Filename",
        "source_path": "SourcePath",
    }
    catalog_payload = {}
    repository_dict = params.copy()
    file_name = repository_dict.pop("file_name", None)
    source_path = repository_dict.pop("source_path", None)
    if file_name is not None:
        catalog_payload.update({"Filename": file_name})
    if source_path is not None:
        catalog_payload.update({"SourcePath": source_path})
    del repository_dict['hostname']
    del repository_dict['username']
    del repository_dict['password']
    del repository_dict['port']
    repository_payload = {catalog_mapper[k]: v for k, v in repository_dict.items() if v is not None}
    if any(repository_payload):
        catalog_payload.update({"Repository": repository_payload})
    return catalog_payload


def main():
    module = AnsibleModule(
        argument_spec={
            "hostname": {"required": True, "type": 'str'},
            "username": {"required": True, "type": 'str'},
            "password": {"required": True, "type": 'str', "no_log": True},
            "port": {"required": False, "default": 443, "type": 'int'},
            "catalog_name": {"required": True, "type": 'str'},
            "catalog_description": {"required": False, "type": 'str'},
            "source": {"required": False, "type": 'str'},
            "source_path": {"required": False, "type": 'str'},
            "file_name": {"required": False, "type": 'str'},
            "repository_type": {"required": False, "default": 'HTTPS',
                                "choices": ["HTTP", "NFS", "CIFS", "HTTPS"]},
            "repository_username": {"required": False, "type": 'str'},
            "repository_password": {"required": False, "type": 'str', "no_log": True},
            "repository_domain": {"required": False, "type": 'str'},
            "check_certificate": {"required": False, "type": 'bool', "default": False},
        },
        supports_check_mode=False)

    try:
        with RestOME(module.params, req_session=True) as rest_obj:
            payload = _get_catalog_payload(module.params)
            resp = rest_obj.invoke_request("POST", "UpdateService/Catalogs", data=payload)
            if resp.success:
                resp_data = resp.json_data
                job_id = resp_data.get("TaskId")
                module.exit_json(msg="Successfully triggered the job to create a "
                                     "catalog with Task Id : {0}".format(job_id),
                                 catalog_status=resp_data, changed=True)
            else:
                module.fail_json(msg="Failed to trigger the job to create catalog.")
    except HTTPError as err:
        module.fail_json(msg=str(err), error_info=json.load(err))
    except (URLError, SSLValidationError, SSLError, ConnectionError, TypeError, ValueError, KeyError) as err:
        module.fail_json(msg=str(err))


if __name__ == '__main__':
    main()

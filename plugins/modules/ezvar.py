#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Yuki Yamashita <kono@kononet.net>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: easyconf

short_description: easy yaml and json config editor

version_added: "2.11"

description:
    - "This is a module that makes it easy to configure a config file
       with a data structure"

options:
    var:
        description:
            - Set the dictionary.
        required: true
    key:
        description:
            - Set the key you want to edit. The input should be in json format.
        required: true
    value:
        description:
            - Set the value to be assigned to key.
        required: false
    state:
        description:
            - Set the state taht present or absent.
        required: false

author:
    - Yuki Yamashita (@konono)
'''

EXAMPLES = '''
- name: 'Test add pattern 1'
  konono.easyconf.ezvar:
    var: '{{ config }}'
    key: 'person[3]''
    value: { "name": "delta", "gender": "female", "age": 21}
    state: 'present'
  register: res
'''

RETURN = '''
var:
   description: Return modified variable.
   returned: success
   type: raw
   sample: 'var'
'''

import shutil  # noqa: E402
import os  # noqa: E402

from ansible.module_utils.basic import AnsibleModule  # noqa: E402
from ansible.module_utils._text import to_bytes  # noqa: E402
from ansible_collections.konono.easyconf.plugins.module_utils.easyconf import EasyConf  # noqa: E402, E501
from datetime import datetime  # noqa: E402


# The AnsibleModule object
module = None


class AnsibleModuleError(Exception):
    def __init__(self, results):
        self.results = results


def main():

    global module

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            var=dict(type='raw', required=True),
            key=dict(type='str', required=True),
            value=dict(type='raw', required=False),
            state=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )

    result = dict(
        value=False,
        changed=False,
        var=False
    )

    var = module.params['var']
    key = module.params['key']
    value = module.params['value']
    state = module.params['state']

    if not isinstance(var, dict) and not isinstance(var, list):
        module.fail_json(msg="%s is not support" % (type(var)))
    if state not in ['present', 'absent']:
        module.fail_json(msg="%s is not support" % (state))
    if state in ['present', 'absent'] and value is None:
        module.fail_json(
            msg="The value parameter is required."
            )

    easyconf = EasyConf(state=state)
    match = easyconf.match_config(key=key, conf=var)
    if state == 'present':
        if match:
            if value == match:
                module.exit_json(**result)
        else:
            if easyconf.match_config(key) == value:
                module.exit_json(**result)
    elif state == 'absent':
        if match:
            if value != match:
                module.exit_json(**result)
        else:
            module.exit_json(**result)

    conf = easyconf.update_config(key=key, value=value, conf=var)
    result['var'] = conf

    result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()

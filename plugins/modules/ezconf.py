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
    src:
        description:
            - Set the path to the config target.
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
            - Set the state taht present or absent, check.
        required: false
    backup:
        description:
            - Set the true if you need src file backup.
        required: false

author:
    - Yuki Yamashita (@konono)
'''

EXAMPLES = '''
- name: 'Test add pattern 1 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'config.d'
    value: 30
    state: 'present'

- name: 'Test add pattern 2 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'config.a-b'
    value: 'c'
    state: 'present'

- name: 'Test add pattern 3 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'config.e'
    value: [1,2,3,4]
    state: 'present'

- name: 'Test add pattern 4 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'config.f'
    value: [{a: 1, b: 2},{c: 3, d: 4}]
    state: 'present'

- name: 'Test add pattern 5 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'lists[2]'
    value: 100
    state: 'present'

- name: 'Test modify pattern 1 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'config.a'
    value: 100
    state: 'present'

- name: 'Test modify pattern 2 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'lists[0]'
    value: 100
    state: 'present'

- name: 'Test delete pattern 1 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'lists[0]'
    value: 0
    state: 'absent'

- name: 'Test delete pattern 2 yaml'
  konono.easyconf.easyconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'lists[0]'
    value: 100
    state: 'absent'

- name: 'Test check pattern 1 yaml'
  konono.easyconf.ezconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'my'
    state: 'check'
  register: res

'''

RETURN = '''
value:
   description: Return the value of the key that was matched if set check to the state.  # noqa: E501
   returned: success
   type: raw
   sample: 'value'
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
            src=dict(type='str', required=True),
            key=dict(type='str', required=True),
            value=dict(type='raw', required=False),
            state=dict(type='str', required=True),
            backup=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
    )

    result = dict(
        value=False,
        changed=False
    )

    src = module.params['src']
    b_src = to_bytes(src, errors='surrogate_or_strict')
    key = module.params['key']
    value = module.params['value']
    state = module.params['state']
    backup = module.params['backup']

    if not os.path.exists(b_src):
        module.fail_json(msg="Source %s not found" % (src))
    if not os.access(b_src, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (src))
    if not os.path.isfile(src):
        module.fail_json(msg="Source %s is not file" % (src))
    if not os.path.splitext(src)[-1] in ['.yaml', '.yml', 'json']:
        module.fail_json(msg="%s is not support" % (os.path.splitext(src)[-1]))
    if state not in ['present', 'absent', 'check']:
        module.fail_json(msg="%s is not support" % (state))
    if state in ['present', 'absent'] and value is None:
        module.fail_json(
            msg="If state is not check,the value parameter is required."
            )

    easyconf = EasyConf(path=src, state=state)
    if not easyconf._load_config:
        module.fail_json(msg="%s is invalid format" % (src))

    match = easyconf.match_config(key)
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
    elif state == 'check':
        result['value'] = match
        module.exit_json(**result)

    if backup:
        shutil.copy2(src, src + "_{0:%Y%m%d%H%M%S}".format(datetime.now()))

    conf = easyconf.update_config(key, value)
    res = easyconf.dump_config(conf)

    if not res:
        module.fail_json(msg="%s is not support" % (easyconf.path.suffix))

    result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()

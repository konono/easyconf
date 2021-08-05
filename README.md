easyconf
=========

### easyconf

このcustom pluginはansible上でyaml、jsonファイルの編集を簡単に行えるものです。

Requirements
------------

python version 3

ansible>=2.9,<2.10

flake8

anyconfig

jmespath

Arguments
--------------

```
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
        required: true
    state:
        description:
            - Set the state taht present or absent, check.
        required: false
    backup:
        description:
            - Set the true if you need src file backup.
        required: false
```

How to use
------------

以下のyamlファイルのpersonに新たに追加したい場合は以下のように表現できます。

example.yml
```
config:
  person:
    - name: alpha
      gender: male
      age: 21
```

```
- name: 'Add pattern 1'
  konono.easyconf.ezconf:
    src: '{{ playbook_dir }}/example.yml'
    key: 'config.person[1]'
    value: {"name": "bravo", "gender": "male", "age": 21}
    state: 'present'
```

result.yml
```
config:
  person:
    - name: alpha
      gender: male
      age: 21
    - name: bravo
      gender: male
      age: 21
```

追加したbravoをcharlieに変更したい場合は以下のように表現できます。

```
- name: 'Mod pattern 1'
  konono.easyconf.ezconf:
    src: '{{ playbook_dir }}/example.yml'
    key: 'config.person[1]'
    value: {"name": "charlie", "gender": "female", "age": 23}
    state: 'present'
```

```
config:
  person:
    - name: alpha
      gender: male
      age: 21
    - name: charlie
      gender: female
      age: 23
```

またlistの一番後ろの要素なので```config.person[-1]```と表現することも可能です。

既存のデータ構造を無視して上書きも可能です。

```
- name: 'Mod pattern 2'
  konono.easyconf.ezconf:
    src: '{{ playbook_dir }}/example.yml'
    key: 'config.person[1]'
    value: ME
    state: 'present'
```

example.yml
```
config:
  person: ME
```

ネストされた要素を追加することも簡単にできます。

```
- name: 'Add pattern 2'
  konono.easyconf.ezconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'my.favorite.whisky.is'
    value: 'Yoichi'
    state: 'present'
```

result.yml
```
my:
  favorite:
    whisky:
      is: Yoichi
```

要素をdeleteしたい場合はどこのネストまで削除するかをkey、何を消すかをvalueで指定して、stateをabsentにしてください。以下の場合だとYoichiが消えます。

```
- name: 'Del pattern 1'
  konono.easyconf.ezconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'my.favorite.whisky.is'
    value: 'Yoichi'
    state: 'absent'
```

result.yml
```
my:
  favorite:
    whisky: {}
```

今回追加した要素をすべて消したい場合はkeyはmyから指定します。valueにはkey以降のデータ構造を入力します。(冪等性担保のため、keyとvalueが一致していない場合は削除されずにOKが帰ってくる仕様です)

しかし、valueにデータ構造を入力するのはとても面倒なので、以下のような書き方をおすすめしています。

state=checkを使うことでkeyの中に入ってるvalueを取り出すことが出来ます。

そこで取り出した値をregisterし、absentのtaskのvalueに与えることで簡単に記述できます。

```
- name: 'Chk pattern 1'
  konono.easyconf.ezconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'my'
    state: 'check'
  register: res

- name: 'show register'
  debug:
    msg: '{{ res.value }}'

- name: 'Del pattern 2'
  konono.easyconf.ezconf:
    src: '{{ playbook_dir }}/tests/test.yml'
    key: 'my'
    value: '{{ res.value }}'
    state: 'absent'
```

実行結果
```
PLAY [localhost] ****************************************

TASK [Chk pattern 1] ************************************
ok: [localhost]

TASK [show register] ************************************
ok: [localhost] => {
    "msg": {
        "favorite": {
            "whisky": {}
        }
    }
}

TASK [Del pattern 2] ************************************
changed: [localhost]

PLAY RECAP *********************************************************************************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Author Information
------------------

Yuki Yamashita(@konono)

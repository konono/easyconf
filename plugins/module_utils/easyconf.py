#!/usr/bin/python
# -*- coding: utf-8 -*-

import anyconfig
import copy
import jmespath
import json
import pathlib
import re
import sys
import yaml


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(Dumper, self).increase_indent(flow, False)


def represent_str(dumper, instance):
    if "\n" in instance:
        instance = re.sub(" +\n| +$", "\n", instance)
        return dumper.represent_scalar(
            "tag:yaml.org,2002:str", instance, style="|"
            )
    else:
        return dumper.represent_scalar(
            "tag:yaml.org,2002:str", instance
            )


class EasyConf:
    def __init__(self, path=None, state="present", dest=None):
        if path:
            self.path = pathlib.Path(path)
        else:
            self.path = path
        if dest:
            self.dest = pathlib.Path(dest)
        else:
            self.dest = dest
        self.state = state

    def match_config(self, key, conf=None):
        conf = conf or self._load_config()
        if isinstance(conf, dict):
            key = re.sub(r"[^a-zA-Z0-9_\-.\[\]]", "", key)
            escaped_query = self._escape_query(key)
            if escaped_query != key:
                match = jmespath.search(escaped_query, conf)
            else:
                match = jmespath.search(key, conf)
            return match
        elif isinstance(conf, list):
            key = re.sub(r"[^0-9\-]", "", str(key))
            try:
                match = conf[int(key)]
            except IndexError:
                match = None
            return match

    def update_config(self, key, value, conf=None, state=None):
        conf = conf or self._load_config()
        state = state or self.state
        if isinstance(conf, list):
            key = re.sub(r"[^0-9\-]", "", str(key))
            if state == 'present':
                if '-' in str(key):
                    if str(key) == '-1':
                        conf.append(value)
                    else:
                        conf.insert(int(key) + 1, value)
                else:
                    conf.insert(int(key), value)
                return conf
            elif state == 'absent':
                conf.pop(int(key))
                return conf
        elif isinstance(conf, dict):
            key = re.sub(r"[^a-zA-Z0-9_\-.\[\]]", "", key)
            e_keys = self._expand_list(key)
            self._modify_nested_dict(key, e_keys, value, conf, state)
        return conf

    def dump_config(self, conf):
        if self.path.suffix in [".yaml", ".yml"]:
            yaml.add_representer(str, represent_str)
            if self.dest:
                return self.dest.write_text(
                    yaml.dump(
                        conf, Dumper=Dumper,
                        default_flow_style=False, sort_keys=False
                    )
                )
            else:
                self.path = self.path.expanduser()
                return self.path.write_text(
                    yaml.dump(
                        conf, Dumper=Dumper,
                        default_flow_style=False, sort_keys=False
                    )
                )
        elif self.path.suffix == ".json":
            if self.dest:
                return self.dest.write_text(anyconfig.dumps(self.path))
            else:
                return self.path.write_text(anyconfig.dumps(self.path))
        else:
            return None

    def dumps_config(self, conf):
        if self.path.suffix in [".yaml", ".yml"]:
            yaml.add_representer(str, represent_str)
            return anyconfig.dumps(
                conf,
                "yaml",
                Dumper=Dumper,
                default_flow_style=False,
                sort_keys=False,
                sequence=4,
                offset=2,
            )
        elif self.path.suffix == ".json":
            return anyconfig.dumps(conf, "json", indent=2)
        else:
            return None

    def _expand_list(self, key):
        i = 0
        splited_keys = key.split(".")
        list = copy.deepcopy(splited_keys)
        for k in splited_keys:
            if re.search(r"[a-zA-Z_\-]+\[-?\d+\]", k):
                del list[i]
                match = re.search(r"-?\d+", k)
                list.insert(i, int(k[match.start(): match.end()]))
                match = re.search(r"\[-?\d+\]", k)
                list.insert(i, k[0: match.start()])
                i += 1
            i += 1
        return list

    def _escape_query(self, key):
        splited_keys = key.split(".")
        for i, k in enumerate(splited_keys):
            if "-" in k:
                del splited_keys[i]
                match = re.search(r"[a-zA-Z_\-]+", k)
                k = '"' + k[match.start(): match.end()] +\
                    '"' + k[match.end(): len(k)]
                splited_keys.insert(i, k)
        return ".".join(splited_keys)

    def _load_config(self):
        if self.path:
            try:
                conf = anyconfig.load(self.path)
            except (yaml.YAMLError, json.decoder.JSONDecodeError,
                    yaml.parser.ParserError) as e:
                sys.stderr.write(e)
                return False
            return conf
        return False

    def _modify_nested_dict(self, key, keys, value, d, state, n=0):
        if n < len(keys) - 1:
            try:
                # 次のnestに入っているvalueがlistであった場合はそのまま再帰で呼び出し
                if isinstance(d[keys[n]][keys[n + 1]],
                              list):
                    self._modify_nested_dict(key, keys, value,
                                             d[keys[n]], state, n+1)
                # 次のnestに入っているvalueがdictionary以外かつ、stateがpresentであった場合は次のnestのvalueを初期化
                elif (
                    not isinstance(d[keys[n]][keys[n + 1]], (dict))
                    and state == "present"
                ):
                    d[keys[n]][keys[n + 1]] = {}
                    self._modify_nested_dict(key, keys, value,
                                             d[keys[n]], state, n+1)
                else:
                    self._modify_nested_dict(key, keys, value,
                                             d[keys[n]], state, n+1)
            except (KeyError, IndexError):
                try:
                    self._modify_nested_dict(key, keys, value,
                                             d[keys[n]], state, n+1)
                except KeyError:
                    # nestされるkeyがもしもなかった場合は新たに作成
                    d[keys[n]] = {}
                    self._modify_nested_dict(key, keys, value,
                                             d[keys[n]], state, n+1)
        else:
            # keyにvalueを入れようとした場合にkeyにlistより長い値が来ていた場合はappend
            if state == "present":
                try:
                    d[keys[n]] = value
                except IndexError:
                    match = self.match_config(key)
                    if not match:
                        # listより大きいindexを渡された場合はlistの最後にあるvalueと引数のvalueを比較して同一でないなら追加する
                        if (
                            self.match_config(re.sub(r"\[-?\d+\]", "[-1]", key))  # noqa: E501
                            != value
                        ):
                            d.append(value)
                    else:
                        if match == value:
                            pass
            elif state == "absent":
                match = self.match_config(key)
                if match:
                    if match == value:
                        try:
                            del d[keys[n]]
                        except KeyError:
                            pass

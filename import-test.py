import os
import sys
import logging
import json
from pyzabbix import ZabbixAPI, ZabbixAPIException
from collections import defaultdict, Counter

#actions_file='/etc/ansible/roles/python/gen-files/reg_actions-test.json'
actions_file='/etc/ansible/roles/python/gen-files/reg_actions.json'
actions_orig='/etc/ansible/roles/python/gen-files/actions_data_orig.json'
actions_dest='/etc/ansible/roles/python/gen-files/actions_data_dest.json'

def get_all(myjson, key):
    loop = ""
    if type(myjson) == str:
        #print("type = str")
        myjson = json.loads(myjson)
    if type(myjson) is dict:
        #print("type = dict")
        for jsonkey in myjson.copy():
            if type(myjson[jsonkey]) in (list, dict):
                get_all(myjson[jsonkey], key)
            elif jsonkey == key:
                print('jsonkey==key', key, myjson[jsonkey])
                if key == 'templateid':
                    for tmplorig in orig["templates"]:
                        if tmplorig['templateid'] == myjson[jsonkey]:
                            hostorig = tmplorig['host']
                            print('host-orig:', hostorig)
                            for tmpldest in dest["templates"]:
                                if hostorig == tmpldest['host']:
                                    print('host-dest:', tmpldest['host'])
                                    print('template-dest', tmpldest['templateid'])
                                    myjson[jsonkey] = tmpldest['templateid']
                elif key == 'groupid':
                    for grporig in orig["hostgroups"]:
                        #print(grporig)
                        #print("for grporig in orig-hostgroups")
                        if grporig['groupid'] == myjson[jsonkey]:
                            hostorig = grporig['name']
                            print('name-orig:', hostorig)
                            for grpdest in dest["hostgroups"]:
                                #print(grpdest)
                                if hostorig == grpdest['name']:
                                    print('name-dest:', grpdest['name'])
                                    print('group-dest:', grpdest['groupid'])
                                    print('cannoli')
                                    myjson[jsonkey] = grpdest['groupid']
                            break
                print('key->value', key, myjson[jsonkey])
                print('-------------------')
            elif jsonkey != key:
                if jsonkey in ('actionid', 'maintenance_mode', 'eval_formula', 'operationid'):
                    del myjson[jsonkey]
    elif type(myjson) is list:
        #print("type = list")
        for item in myjson:
            if type(item) in (list, dict):
                get_all(item, key)


json_data=open(actions_file)
data_orig=open(actions_orig)
data_dest=open(actions_dest)
data = json.load(json_data)
orig = json.load(data_orig)
dest = json.load(data_dest)
counter=0
for line in data:
    counter = counter + 1
    print('counter: ', counter)

    import pprint
    print('printing line: --------------------------------------------------------------------------------------------')
    pprint.pprint(line)
    get_all(line, 'groupid')
    get_all(line, 'templateid')
    print('printing data: --------------------------------------------------------------------------------------------')
    pprint.pprint(data)

#target_path = '{}/reg_actions_import.json'.format(export_dir)
target_path = '/etc/ansible/roles/python/gen-files/reg_actions_import.json'
with open(target_path, "w") as export_file:
     export_file.write(json.dumps(data))

json_data.close()

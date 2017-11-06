import os
import sys
import logging
import json
from pyzabbix import ZabbixAPI, ZabbixAPIException
from collections import defaultdict


#__ZBX_API_DEV = 'zabbix-web.inst.gaz.gb-home.cns.gorillass.co.uk'
__ZBX_API_DEV = 'zbxweb.svc.eb49da3d-7240-6e94-8e93-b65f3954c652.us-east-1.triton.zone'

__ENV_ZABBIX_API_HOST = 'ZBX_API_HOST'
__ENV_USERNAME = 'ZBX_USER'
__ENV_PASSWORD = 'ZBX_PASS'
__ENV_ZBX_CONFIG_DIR = 'ZBX_CONFIG_DIR'

__rules = {
        'applications': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'discoveryRules': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'graphs': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'groups': {
            'createMissing': 'true'
        },
        'hosts': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'images': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'items': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'maps': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'screens': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'templateLinkage': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'templates': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'templateScreens': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'triggers': {
            'createMissing': 'true',
            'updateExisting': 'true'
        },
        'valueMaps': {
            'createMissing': 'true',
            'updateExisting': 'true'
        }
    }


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    stream = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s [%(threadName)s] '
                            '[%(name)s] %(levelname)s: %(message)s')
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    return logger


__LOG = get_logger(__name__)


def __info(message, *args):
    __LOG.log(logging.INFO, message.format(*args))


def __log_error_and_fail(message, *args):
    __LOG.log(logging.ERROR, message.format(*args))
    sys.exit(-1)


__zbx_api = None


def initiate_zabbix_api(zbx_host, zbx_user, zbx_password):
    global __zbx_api
    zbx_url = 'http://{}'.format(zbx_host)
    __info('Logging in using url={} ...', zbx_url)
    __zbx_api = ZabbixAPI(zbx_url)
    __zbx_api.login(user=zbx_user, password=zbx_password)
    __info('Connected to Zabbix API Version {} as {}', __zbx_api.api_version(), zbx_user)


def __import_objects(component, import_dir):
    file = '{}/{}.json'.format(import_dir, component)
    with open(file, 'r') as f:
         component_data = f.read()
         __info('Importing {}...', component)
         try:
             __zbx_api.confimport('json', component_data, __rules)
         except ZabbixAPIException as err:
             print(err)

def __import_actions(component, import_dir):
    file = '{}/{}.json'.format(import_dir, component)
    with open(file, 'r') as f:
         component_data = f.read()
         __info('Importing {}...', component)
         actions = json.loads(component_data)
         for action in actions:
             __zbx_api.action.create(action)
         #try:
         #   __zbx_api.action.create(actions)
         #except ZabbixAPIException as err:
         #   print(err)


def import_hostgroups(import_dir):
    __import_objects('hostgroups', import_dir)


def import_templates(import_dir):
    __import_objects('templates', import_dir)


def import_hosts(import_dir):
    __import_objects('hosts', import_dir)


def import_actions(import_dir):
    __import_actions('reg_actions_import', import_dir)


def import_app(import_dir, components):
    if not os.path.isdir(import_dir):
        os.makedirs(import_dir)

    for import_fn in components:
        import_fn(import_dir)


def exp_act_data_dest(export_dir):

    data = defaultdict(list)

    for template in __zbx_api.template.get(output="extend"):
        templates = {"templateid": template['templateid'], "host": template['host']}
        data['templates'].append(templates)

    for hostgroup in __zbx_api.hostgroup.get(output="extend"):
        hostgroups = {"groupid": hostgroup['groupid'], "name": hostgroup['name']}
        data['hostgroups'].append(hostgroups)

    target_path = '{}/actions_data_dest.json'.format(export_dir)
    with open(target_path, "w") as export_file:
         export_file.write(json.dumps(data))


def get_all(act_line, key, orig, dest):
    if type(act_line) == str:
        act_line = json.loads(act_line)
    if type(act_line) is dict:
        for actjsonkey in act_line.copy():
            if type(act_line[actjsonkey]) in (list, dict):
                get_all(act_line[actjsonkey], key, orig, dest)
            elif actjsonkey == key:
                if key == 'templateid':
                    for tmplorig in orig["templates"]:
                        if tmplorig['templateid'] == act_line[actjsonkey]:
                            hostorig = tmplorig['host']
                            for tmpldest in dest["templates"]:
                                if hostorig == tmpldest['host']:
                                    act_line[actjsonkey] = tmpldest['templateid']
                elif key == 'groupid':
                    for grporig in orig["hostgroups"]:
                        if grporig['groupid'] == act_line[actjsonkey]:
                            hostorig = grporig['name']
                            for grpdest in dest["hostgroups"]:
                                if hostorig == grpdest['name']:
                                    act_line[actjsonkey] = grpdest['groupid']
                            break
            elif actjsonkey != key:
                if actjsonkey in ('actionid', 'maintenance_mode', 'eval_formula', 'operationid'):
                    del act_line[actjsonkey]
    elif type(act_line) is list:
        for item in act_line:
            if type(item) in (list, dict):
                get_all(item, key, orig, dest)
                
                
def gen_imp_act_file(files_dir):
    actions_file = '{}/reg_actions.json'.format(files_dir)
    actions_orig = '{}/actions_data_orig.json'.format(files_dir)
    actions_dest = '{}/actions_data_dest.json'.format(files_dir)

    actions_data = open(actions_file)
    data_orig = open(actions_orig)
    data_dest = open(actions_dest)
    data = json.load(actions_data)
    orig = json.load(data_orig)
    dest = json.load(data_dest)
    for act_line in data:
        get_all(act_line, 'groupid', orig, dest)
        get_all(act_line, 'templateid', orig, dest)
        
    target_path = '{}/reg_actions_import.json'.format(files_dir)
    with open(target_path, "w") as export_file:
        export_file.write(json.dumps(data))

    actions_data.close()


if __name__ == '__main__':
    host = os.getenv(__ENV_ZABBIX_API_HOST) or __ZBX_API_DEV
    user = os.environ[__ENV_USERNAME]
    password = os.environ[__ENV_PASSWORD]
    config_dir = os.getenv(__ENV_ZBX_CONFIG_DIR) or \
                        os.path.abspath(__file__)

    initiate_zabbix_api(host, user, password)
    to_import = [import_hostgroups, import_templates, import_hosts]
    import_app(config_dir, to_import)
    exp_act_data_dest(config_dir)
    gen_imp_act_file(config_dir)
    to_import = [import_actions]
    import_app(config_dir, to_import)

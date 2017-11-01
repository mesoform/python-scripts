import os
import sys
import logging
import json
from pyzabbix import ZabbixAPI, ZabbixAPIException
from collections import defaultdict

__ZBX_API_DEV = 'zabbix-web.inst.gaz.gb-home.cns.gorillass.co.uk'

__ENV_ZABBIX_API_HOST = 'ZBX_API_HOST'
__ENV_USERNAME = 'ZBX_USER'
__ENV_PASSWORD = 'ZBX_PASS'
__ENV_ZBX_CONFIG_DIR = 'ZBX_CONFIG_DIR'


# TODO move this somewhere to reuse
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

def __export_json_to_file(result, export_dir, export_filename):
    target_absolute_path = '{}/{}.json'.format(export_dir, export_filename)
    with open(target_absolute_path, "w") as export_file:
        export_file.write(result)


# __get_data('template', label_for_logging='templates', output='a', other_thing='b')

# getattr(__zbx_api, 'template').get(output='a', other_thing='b')
# __zbx_api.template.get(output='a', other_thing='b')

def __get_data(component, label_for_logging=None, **kwargs):
    if not label_for_logging:
        label_for_logging = '{}s'.format(component)
    __info('Exporting {}...', label_for_logging)
    # getattr is like concatenating component onto the object. In this case ZabbixAPI.template
    results = getattr(__zbx_api, component).get(**kwargs)
    if not results:
        __info('No {} found', label_for_logging)
        return
    print(results)
    return results


def __get_selected_data_and_export(component, get_event_source,
                                   export_dir, export_filename,
                                   label_for_logging=None):
    results = __get_data(component, label_for_logging,
                         output='extend',
                         selectOperations='extend',
                         selectRecoveryOperations='extend',
                         selectFilter='extend',
                         filter={'eventsource': get_event_source})

    __export_json_to_file(json.dumps(results), export_dir, export_filename)


def __get_data_and_export(component, get_output,
                          export_dir, export_filename, label_for_logging=None):
    results = __get_data(component, label_for_logging,
                         output=get_output)

    __export_json_to_file(json.dumps(results), export_dir, export_filename)


def __get_data_and_export_config(component, get_id_prop_name,
                                 export_option_name,
                                 export_dir, export_filename,
                                 label_for_logging=None):
    results = __get_data(component, label_for_logging,
                         output=get_id_prop_name)
    print(results)
    component_ids = [component[get_id_prop_name] for component in results]

    export_options = {export_option_name: component_ids}
    print(export_options)
    result = __zbx_api.configuration.export(options=export_options,
                                            format='json')

    __export_json_to_file(result, export_dir, export_filename)


def export_templates(export_dir):
    __get_data_and_export_config(
        'template', 'templateid', 'templates', export_dir, 'templates')


def export_host_groups(export_dir):
    __get_data_and_export_config(
        'hostgroup', 'groupid', 'groups', export_dir, 'hostgroups')


def export_hosts(export_dir):
    __get_data_and_export_config('host', 'hostid', 'hosts', export_dir, 'hosts')


def export_media_types(export_dir):
    __get_data_and_export('mediatype', 'extend', export_dir, 'mediatypes')


def export_auto_registration_actions(export_dir):
    __get_selected_data_and_export(
        'action', 2, export_dir, 'reg_actions', 'auto-registration actions')


def export_trigger_actions(export_dir):
    __get_selected_data_and_export(
        'action', 0, export_dir, 'trigger_actions', 'trigger actions')


def export_actions_data(export_dir):

    data = defaultdict(list)

    for template in __zbx_api.template.get(output="extend"):
        templates = {"templateid": template['templateid'], "host": template['host']}
        data['templates'].append(templates)

    for hostgroup in __zbx_api.hostgroup.get(output="extend"):
        hostgroups = {"groupid": hostgroup['groupid'], "name": hostgroup['name']}
        data['hostgroups'].append(hostgroups)

    target_path = '{}/actions_data_orig.json'.format(export_dir)
    with open(target_path, "w") as export_file:
         export_file.write(json.dumps(data))


def backup_app(zbx_user, zbx_password, zbx_host, export_dir):
    if not os.path.isdir(export_dir):
        os.makedirs(export_dir)

    initiate_zabbix_api(zbx_host, zbx_user, zbx_password)
    for export_fn in [
                      export_templates,
                      export_host_groups,
                      export_hosts,
                      export_media_types,
                      export_auto_registration_actions,
                      export_trigger_actions,
                      export_actions_data
                     ]:
        export_fn(export_dir)

# be importable
if __name__ == '__main__':
    host = os.getenv(__ENV_ZABBIX_API_HOST) or __ZBX_API_DEV
    user = os.environ[__ENV_USERNAME]
    password = os.environ[__ENV_PASSWORD]
    config_export_dir = os.getenv(__ENV_ZBX_CONFIG_DIR) or \
                        os.path.abspath(__file__)

    backup_app(user, password, host, config_export_dir)

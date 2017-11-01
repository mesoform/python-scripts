import json
from zabbix.api import ZabbixAPI

from collections import defaultdict

# Create ZabbixAPI class instance
__zbx_api = ZabbixAPI("http://secondary.gorillass.co.uk:10052")
__zbx_api.login("dan", "zabbix")
print("Connected to Zabbix API Version %s" % __zbx_api.api_version())

case_file = defaultdict(list)

for template in zapi.template.get(output="extend"):
    result={"templateid": template['templateid'], "host": template['host']}
    case_file['templates'].append(result)

for hostgroup in zapi.hostgroup.get(output="extend"):
    result={"groupid": hostgroup['groupid'], "name": hostgroup['name']}
    case_file['hostgroups'].append(result)

with open("/etc/ansible/roles/python/gen-files/exports.json", "w") as export_file:
    export_file.write(json.dumps(case_file))

#!/usr/bin/env python

from paramiko import SSHClient, MissingHostKeyPolicy
from clusto.scripthelpers import init_script
from diggext.drivers import PenguinServer
import clusto

from optparse import OptionParser
from traceback import format_exc
import sys
import re

ifpattern = re.compile('^(?P<type>[a-z]+)(?P<num>[0-9]+)$')

class SilentPolicy(MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key): pass

def discover_hardware(ip):
    client = SSHClient()

    client.load_system_host_keys()
    client.set_missing_host_key_policy(SilentPolicy())
    client.connect(ip, username='root', timeout=2.0)
    stdout = client.exec_command('cat /proc/partitions')[1].read()

    disks = []
    for line in stdout.split('\n'):
        if not line: continue
        line = [x for x in line.split(' ') if x]
        if not line[0].isdigit(): continue
        if not re.match('^[hs]d[a-z]$', line[3]): continue
        name = line[3]
        blocks = int(line[2])
        blocks *= 1024

        hdinfo = {
            'osname': name,
            'size': str(blocks),
        }

        # Query info from hdparm (IDE and SATA)
        stdout = client.exec_command('hdparm -I /dev/%s' % name)[1].read()
        useful = ('model', 'serial', 'firmware')
        for field in stdout.split('\n'):
            field = field.strip(' \t')
            for u in useful:
                if field.lower().startswith(u):
                    value = field.split(':', 1)[1]
                    hdinfo[u] = value.strip(' \t')

        # Attempt a SCSI query
        if not [x for x in useful if x in hdinfo]:
            stdout = client.exec_command('/usr/bin/sg_inq /dev/%s' % name)[1].read()
            scsi_useful = {
                'Product identification': 'model',
                'Product revision level': 'firmware',
                'Unit serial number': 'serial',
            }
            for field in [x.strip(' \t') for x in stdout.split('\n')]:
                for u in scsi_useful:
                    if field.startswith(u):
                        key = scsi_useful[u]
                        value = field.split(':', 1)[1]
                        hdinfo[key] = value.strip(' \t')
            if [x for x in useful if not x in hdinfo]:
                sys.stdout.write('%s:missing ' % name)

        disks.append(hdinfo)

    xen = False
    stdout = client.exec_command('uname -r')[1].read()
    if stdout.lower().find('-xen-') != -1:
        xen = True

    stdout = client.exec_command('dmidecode -t memory')[1].read()
    memory = []
    mem = {}
    for line in stdout.split('\n'):
        if not line and mem:
            memory.append(mem)
            mem = {}
            continue
        if not line.startswith('\t'): continue

        key, value = line.lstrip('\t').split(': ', 1)
        if key in ('Locator', 'Type', 'Speed', 'Size'):
            mem[key.lower()] = value

    processors = []
    cpu = {}

    if xen:
        sys.stdout.write('xen ')
        sys.stdout.flush()
        stdout = client.exec_command('/usr/sbin/xm info')[1].read()
        for line in stdout.split('\n'):
            line = line.split(':', 1)
            if len(line) != 2:
                continue
            key, value = line
            key = key.strip(' \t')
            value = value.strip(' \t')
            if key == 'nr_cpus':
                cpucount = int(value)
            if key == 'total_memory':
                kmem = int(value)
    else:
        stdout = client.exec_command('/usr/bin/free -m')[1].read()
        stdout = [x for x in stdout.split('\n')[1].split(' ') if x]
        kmem = int(stdout[1])

        stdout = client.exec_command('cat /proc/cpuinfo')[1].read()
        for line in stdout.split('\n'):
            if not line and cpu:
                processors.append(cpu)
                cpu = {}
                continue
            if not line: continue

            key, value = line.split(':', 1)
            key = key.strip(' \t')
            if key in ('model name', 'cpu MHz', 'cache size', 'vendor_id'):
                key = key.lower().replace(' ', '-').replace('_', '-')
                cpu[key] = value.strip(' ')
        cpucount = len(processors)

    serial = client.exec_command('/usr/sbin/dmidecode --string=system-serial-number')[1].read().rstrip('\r\n')
    hostname = client.exec_command('/bin/hostname -s')[1].read().rstrip('\r\n')

    stdout = client.exec_command('/sbin/ifconfig -a')[1].read()
    iface = {}
    for line in stdout.split('\n'):
        line = line.rstrip('\r\n')
        if not line: continue
        line = line.split('  ')
        if line[0]:
            name = line[0]
            iface[name] = []
            del line[0]
        line = [x for x in line if x]
        iface[name] += line

    for name in iface:
        attribs = {}
        value = None
        for attr in iface[name]:
            value = None
            if attr.startswith('Link encap') or \
                attr.startswith('inet addr') or \
                attr.startswith('Bcast') or \
                attr.startswith('Mask') or \
                attr.startswith('MTU') or \
                attr.startswith('Metric'):
                key, value = attr.split(':', 1)
            if attr.startswith('HWaddr'):
                key, value = attr.split(' ', 1)
            if attr.startswith('inet6 addr'):
                key, value = attr.split(': ', 1)
            if not value: continue
            attribs[key.lower()] = value
        iface[name] = attribs

    client.close()

    return {
        'disk': disks,
        'memory': memory,
        'processor': processors,
        'network': iface,
        'system': [{
            'serial': serial,
            'cpucount': cpucount,
            'hostname': hostname,
            'memory': kmem,
            'disk': sum([int(x['size'][:-9]) for x in disks])
        }],
    }

def update_server(server, info):
    server.del_attrs(key='memory')
    server.del_attrs(key='disk')
    server.del_attrs(key='processor')
    server.del_attrs(key='system')

    for itemtype in info:
        if itemtype == 'network': continue
        for i, item in enumerate(info[itemtype]):
            for subkey, value in item.items():
                server.set_attr(key=itemtype, subkey=subkey, value=value, number=i)

    for ifnum in range(0, 2):
        ifname = 'eth%i' % ifnum
        if not ifname in info['network']:
            continue

        #if server.attrs(subkey='mac', value=info['network'].get(ifname, {}).get('hwaddr', '')):
        #    continue
        #server.del_port_attr('nic-eth', ifnum + 1, 'mac')
        server.set_port_attr('nic-eth', ifnum + 1, 'mac', info['network'][ifname]['hwaddr'])

        if 'inet addr' in info['network'][ifname]:
            server.bind_ip_to_osport(info['network'][ifname]['inet addr'], ifname)

def main():
    parser = OptionParser(usage='usage: %prog [options] <object>')
    options, args = parser.parse_args()

    if not args:
        parser.print_help()
        return -1

    try:
        obj = clusto.get_by_name(args[0])
    except LookupError:
        sys.stderr.write('Object does not exist: %s\n' % args[0])
        return -1

    if obj.type != 'server':
        obj = obj.contents()
    else:
        obj = [obj]

    for server in obj:
        if server.type != 'server':
            sys.stdout.write('Not a server\n')
            continue

        #if server.attr_values(key='disk', subkey='serial'):
        #    continue

        sys.stdout.write(server.name + ' ')
        sys.stdout.flush()

        ip = server.get_ips()
        if not ip:
            sys.stdout.write('No IP assigned\n')
            continue
        ip = ip[0]

        try:
            sys.stdout.write('discover_hardware ')
            sys.stdout.flush()
            info = discover_hardware(ip)
        except:
            sys.stdout.write('Unable to discover. %s\n' % sys.exc_info()[1])
            continue

        try:
            sys.stdout.write('update_server ')
            clusto.begin_transaction()
            update_server(server, info)
            clusto.commit()
            sys.stdout.write('.\n')
        except:
            sys.stdout.write('Error updating clusto:\n%s\n' % format_exc())
            clusto.rollback_transaction()
        sys.stdout.flush()

if __name__ == '__main__':
    init_script()

    sys.exit(main())

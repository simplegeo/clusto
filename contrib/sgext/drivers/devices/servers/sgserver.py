from clusto.drivers.devices.servers.basicserver import BasicServer
from IPy import IP
import boto.ec2
import paramiko
import urllib2
import socket
import sys

class IgnoreMissingHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return

class SGException(Exception):
    pass

class SGServer(BasicServer):
    _driver_name = 'sgserver'
    _portmeta = {
        'nic-eth': {'numports': 1},
    }

    def get_boto_connection(self):
        region = self.attr_value(key='ec2', subkey='region', merge_container_values=True)
        return boto.ec2.connect_to_region(region)

    def get_best_ip(self):
        for dnsname in self.attr_values(key='ec2', subkey='public-dns'):
            try:
                ip = socket.gethostbyname(dnsname)
                return ip
            except Exception, e:
                pass
        ips = self.attr_values(key='ip', subkey='ipstring')
        for ip in ips:
            if IP(ip).iptype() != 'PRIVATE':
                return ip
        if not ips:
            raise SGException('Unable to determine IP for %s' % self.name)

    def ssh_command(self, command, timeout=0.0):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(IgnoreMissingHostKeyPolicy)
        client.connect(self.get_best_ip())
        transport = client.get_transport()
        session = transport.open_session()
        session.settimeout(timeout)
        returncode = session.recv_exit_status()
        return returncode

    def reboot(self):
        conn = self.get_boto_connection()
        conn.reboot_instances([self.attr_value(key='ec2', subkey='instance-id')])

    def opsd_request(self, method, endpoint, data={}):
        url = 'http://%s:9666/%s' % (self.get_best_ip(), endpoint)
        if data:
            req = urllib2.Request(url, data=data)
        else:
            req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        return json.loads(resp.read())

    def start_service(self, name, provider='monit'):
        result = self.opsd_request('POST', '/v0/service/%s/%s.json' % (provider, name), {'action': 'start'})
        if result['status'] != 'ok':
            raise SGException('Error starting service: %s' % result)

    def stop_service(self, name, provider='monit'):
        result = self.opsd_request('POST', '/v0/service/%s/%s.json' % (provider, name), {'action': 'stop'})
        if result['status'] != 'ok':
            raise SGException('Error starting service: %s' % result)

    def get_service_status(self, name, provider='monit'):
        return self.opsd_request('GET', '/v0/service/%s/%s.json' % (provider, name))

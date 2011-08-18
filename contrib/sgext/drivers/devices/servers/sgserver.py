from clusto.drivers.devices.servers.basicserver import BasicServer
from IPy import IP
import boto.ec2
import urllib2
import socket
import json
import sys

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

    def reboot(self):
        conn = self.get_boto_connection()
        conn.reboot_instances([self.attr_value(key='ec2', subkey='instance-id')])

    def opsd_request(self, method, endpoint, data={}):
        url = 'http://%s:9666%s' % (self.get_best_ip(), endpoint)
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
            raise SGException('Error stopping service: %s' % result)

    def restart_service(self, name, provider='monit'):
        result = self.opsd_request('POST', '/v0/service/%s/%s.json' % (provider, name), {'action': 'restart'})
        if result['status'] != 'ok':
            raise SGException('Error restarting service: %s' % result)

    def get_service_status(self, name=None, provider='monit'):
        if name is None:
            return self.opsd_request('GET', '/v0/service/%s/' % provider)
        else:
            return self.opsd_request('GET', '/v0/service/%s/%s.json' % (provider, name))

    def install_package(self, name, provider='apt'):
        result = self.opsd_request('POST', '/v0/package/%s/%s.json' % (provider, name), {'action': 'install'})
        if result['status'] != 'ok':
            raise SGException('Error installing package: %s' % result)

    def remove_package(self, name, provider='apt'):
        result = self.opsd_request('POST', '/v0/package/%s/%s.json' % (provider, name), {'action': 'remove'})
        if result['status'] != 'ok':
            raise SGException('Error removing package: %s' % result)

    def apt_update(self):
        return self.opsd_request('POST', '/v0/package/apt/update.json')

    def get_package_status(self, name=None, provider='apt'):
        if name is None:
            return self.opsd_request('GET', '/v0/package/%s/' % provider)
        else:
            return self.opsd_request('GET', '/v0/package/%s/%s.json' % (provider, name))

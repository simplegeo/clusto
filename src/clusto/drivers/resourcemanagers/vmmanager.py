"""
The VMManager is a special case of resource manager.

It overrides many of the standard ResourceManager functions but still makes
use of the ResourceManager plumbing where appropriate.

"""

import clusto
from clusto.drivers.devices.servers import BasicServer, BasicVirtualServer
from clusto.drivers.base import ResourceManager
from clusto.exceptions import ResourceException

import random

class VMManager(ResourceManager):
    """Manage resources for Virtual Machines.

    The resource being managed are the host machines.  A VM gets assigned to a
    host machine.  The VMManager keeps track of how much cpu/ram/disk is
    available on each host and allocates them accordingly.
    """
    
    _driver_name = "vmmanager"

    _attr_name = "vmmanager"

    def ensure_type(self, resource, number=True, thing=None):

        if isinstance(resource, basestring):
            resource = clusto.get_by_name(resource)

        if resource not in self:
            raise ResourceException("%s is not managed by this VM manager"
                                    % resource.name)

        return (resource, number)
    
        
    def insert(self, thing, memory=None, disk=None, cpucount=None):
        # insert into self and also add attributes that will help with  allocation
        if thing.type != BasicServer._clusto_type:
            raise ResourceException("Only servers can be inserted into "
                                    "this manager but %s is of type %s."
                                    % (thing.name, thing.type))

        
        memory = memory or thing.attr_value('system', subkey='memory')
        disk = disk or thing.attr_value('system', subkey='disk')
        cpucount = cpucount or thing.attr_value('system', subkey='cpucount')

        if not memory and not disk and not cpucount:
            raise ResourceException("Server must have attributes for "
                                    "key='system' and subkey='disk',"
                                    "'memory', and 'cpucount' set to be "
                                    "inserted into this manager.")

        attr = super(VMManager, self).insert(thing)
        
        return attr
    
    def remove(self, thing):
        # check if thing is in use by a VM
        # error if yes
        # remove if no and clear attributes related to helping allocation

        vms = self.owners(thing)
        if vms:
            raise ResourceException("%s is still allocated to VMs: %s"
                                    % (thing.name, str(vms)))

        super(VMManager, self).remove(thing)
        
        
    def additional_attrs(self, thing, resource, number):

        resource, number = self.ensure_type(resource, number)

        thing.set_attr(self._attr_name, number=number,
                       subkey='allocated_memory',
                       value=thing.attr_value('system', subkey='memory'))

    def available(self, resource, number=True, thing=None):
        resource, number = self.ensure_type(resource, number)

        return self._has_capacity(resource, thing)

        
    def _has_capacity(self, host, vm):

        ## this is a very slow way to do this
        
        mem = host.attr_value('system', subkey='memory')
        disk = host.attr_value('system', subkey='disk')
        cpu = host.attr_value('system', subkey='cpucount')
        vms = host.referencers(clusto_types=[BasicVirtualServer])

        for v in vms:
            mem -= v.attr_value('system', subkey='memory')
            disk -= v.attr_value('system', subkey='disk')
            cpu -= v.attr_value('system', subkey='cpucount')

        vmmem = vm.attr_value('system', subkey='memory')
        vmdisk = vm.attr_value('system', subkey='disk')
        vmcpu = vm.attr_value('system', subkey='cpucount')
        
        return (vmcpu <= cpu) & (vmmem <= mem) & (vmdisk <= disk)
        
    
    def allocator(self, thing):
        """Allocate a host server for a given virtual server. """

        for res in self.resources(thing):
            raise ResourceException("%s is already assigned to %s"
                                    % (thing.name, res.value))

        hosts = self.contents(clusto_types=[BasicServer])

        hosts = sorted(hosts,
                       key=lambda x: x.attr_value('system', subkey='disk'))
        hosts = sorted(hosts,
                       key=lambda x: x.attr_value('system', subkey='cpucount'))
        hosts = sorted(hosts,
                       key=lambda x: x.attr_value('system', subkey='memory'))
                       
        
        for i in hosts:
            if self._has_capacity(i, thing):
                return (i, True)

                
        raise ResourceException("No hosts available.")

    def allocate(self, thing, resource=(), number=True, **kwargs):
        """Allocate resources for VMs

        pass off normal allocation to the parent but also keep track of
        available host-resources
        """
        
        for res in self.resources(thing):
            raise ResourceException("%s is already assigned to %s"
                                    % (thing.name, res.value))

        attr = super(VMManager, self).allocate(thing, resource, number)

        return attr
    

class EC2VMManager(VMManager):

    _driver_name = "ec2vmmanager"

    _properties = {'budget':None,
                   'current_cost':None,
                   'accountstuff':None} # i'd have to lookup again what ec2 actually needs

    def allocator(self):
        """allocate VMs on ec2 while keeping track of current costs and staying within the budget"""
        pass

class XenVMManager(VMManager):
    """Manage Xen Instances


    insert() servers that can act as hypervisors into this VM manager
    """
    
    _driver_name = "xenvmmanager"

    #_properties = { # som configuration properties that help control how many VMs per CPU or something like that}
    
    def allocator(self):
        """allocate VMs """
        pass
        # get list of potential servers: self.contents(clusto_type=[BasicServer])

        # find server with available resources

        # maybe do some bookeeping

        
        
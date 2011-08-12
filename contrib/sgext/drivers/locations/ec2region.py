from clusto.drivers import Driver

class EC2Region(Driver):
    _driver_name = 'ec2region'

    def __init__(self, name_driver_entity, **kwargs):
        Driver.__init__(self, name_driver_entity, **kwargs)
        self.set_attr(key='ec2', subkey='region', value=self.name)

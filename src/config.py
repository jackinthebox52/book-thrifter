import os
import yaml

class Config:
    def __init__(self, email, password, price_threshold, notification_rate, notification_methods, notification_email, notification_phone):
        self.email = email
        self.password = password
        self.price_threshold = price_threshold
        self.notification_rate = notification_rate
        self.notification_methods = notification_methods
        self.notification_email = notification_email
        self.notification_phone = notification_phone

    @classmethod
    def read_file(cls, filename):
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def write_file(self, filename):
        with open(filename, 'w') as f:
            yaml.safe_dump(self.__dict__, f)
            


def load_configs() -> list[Config]:
    '''Locates all configuration files in the user's home directory. If the directory does not exist, it is created, and None is returned. Returns data as Config objects.'''
    if 'HOME' not in os.environ:
        raise ValueError("HOME environment variable not found")
    configs = []
    config_dir = os.path.join(os.environ['HOME'], '.bookthrifter', 'config')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        return None
    for path in os.listdir(config_dir):
        if path.endswith('.conf'):
            print(f'Found configuration file: {path}')
            data = Config.read_file(f'{config_dir}/{path}')
            configs.append(data)
    return configs

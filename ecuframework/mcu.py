import threading
import logging
import queue

from ecuframework.util import looped


class Receiver:
    """

    """
    def __init__(self, mcu_instance, on_receiver):
        self.mcu_instance = mcu_instance
        self.on_receiver = on_receiver

    def get(self, job):
        self.on_receiver(self.mcu_instance, job)


class McuController:
    _pattern = {}
    _mcu_instance = None
    _receiver = None
    _modules = []

    def __init__(self):
        self.shared_queue = queue.PriorityQueue()

    def get_modules(self):
        return self._modules

    def get_receiver(self):
        return self._receiver

    def get_module_target(self, target_type):
        filtered = list(filter(lambda module: module.module_type == target_type, self._modules))
        return filtered[0] if len(filtered) > 0 else None

    def init(self, mcu_instance, mcu_pattern):
        self._mcu_instance = mcu_instance
        on_receiver = mcu_pattern.__dict__['_handler_functions'].pop('on_receiver')
        self._receiver = Receiver(self._mcu_instance, on_receiver)
        self._pattern = mcu_pattern.__dict__['_handler_functions']

    def _processor(self):
        job = self.shared_queue.get()
        if self._pattern['assigning_job']:
            self._pattern['assigning_job'](self._mcu_instance, job)
        self.shared_queue.task_done()

    def add_module(self, module):
        self._modules.append(module)

    def run(self):
        if self._mcu_instance is None:
            raise AssertionError('The Mcu instance is None')

        looped(self._processor, daemon=False)


class McuPattern:

    def __init__(self):
        self._handler_functions = {
            'on_receiver': None,
            'assigning_job': None,
            'processor': None,
        }

    def on_receiver(self):
        def decorator(f):
            self._handler_functions['on_receiver'] = f
        return decorator

    def assigning_job(self):
        def decorator(f):
            self._handler_functions['assigning_job'] = f
        return decorator

    def processor(self):
        def decorator(f):
            self._handler_functions['processor'] = f
        return decorator


class Mcu(threading.Thread):

    def __init__(self, name):
        super().__init__(name=name, daemon=False)
        self.logger = logging.getLogger(name)
        self.controller = McuController()

    def register_modules(self, modules):
        candidate_modules = list(dict.fromkeys(modules))

        if all(module in self.controller.get_modules() for module in candidate_modules):
            raise AssertionError('The modules have already been registered')

        for module in candidate_modules:
            module.register_receiver(self.controller.get_receiver())
            self.controller.add_module(module)

    def _start_modules(self):
        if len(self.controller.get_modules()) == 0:
            self.logger.warning('No module to start')
        [module.start() for module in self.controller.get_modules()]

    def run(self):
        self.logger.info(f'Modules starting')
        self.controller.run()
        self._start_modules()
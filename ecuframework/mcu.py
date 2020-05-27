import threading
import logging
import queue

from ecuframework.util import looped


class Receiver:
    """
    Allows communication between modules and MCU.
    This class is stored in the modules when they are registered in the MCU
    """
    def __init__(self, mcu_instance, on_receiver):
        """
        :param mcu_instance: it is the instance of the MCU to which the Jobs must be sent
        :param on_receiver: it is the function that deals with Job
        """
        self.mcu_instance = mcu_instance
        self.on_receiver = on_receiver

    def get(self, job):
        """
        It obtains the sender's job passed to it as input and sends it to the recipient receiver
        :param job: assigned by the sender
        :return: None
        """
        self.on_receiver(self.mcu_instance, job)


class McuController:

    """
    It is the class that manages all MCU entirely
    """

    # Stores the MCU pattern. Through this access is made to methods decorated with the support of McuPattern objects
    _pattern = {}

    # Instance of the MCU
    _mcu_instance = None

    # It is the receiver object that will be used to receive jobs from the modules
    _receiver = None

    # Is the list of modules currently registered on the MCU
    _modules = []

    def __init__(self):
        # It is the queue where the jobs produced by the modules will be paid.
        # Thanks to it, MCU can adequately distribute the jobs to the right recipients
        self.shared_queue = queue.PriorityQueue()

    def get_modules(self):
        return self._modules

    def get_receiver(self):
        return self._receiver

    def get_module_target(self, type_target):
        """
        It is the method that obtains the recipient of a particular module based on the basic rule,
        that is, the search based on the type of module
        :param type_target: is the type of the recipient module associated with a particular job
        :return: recipient form if it exists, otherwise it returns None
        """
        filtered = list(filter(lambda module: module.module_type == type_target, self._modules))
        return filtered[0] if len(filtered) > 0 else None

    def init(self, mcu_instance, mcu_pattern):
        """
        This method is very important and only needs to be called once in the class constructor
        :param mcu_instance: it is the instance of the MCU
        :param mcu_pattern: it is the mcu pattern that contains the method scheme
        :return: None
        """
        self._mcu_instance = mcu_instance
        on_receiver = mcu_pattern.__dict__['_handler_functions'].pop('on_receiver')
        self._receiver = Receiver(self._mcu_instance, on_receiver)
        self._pattern = mcu_pattern.__dict__['_handler_functions']

    def _processor(self):
        """
        It is the process that obtains jobs from the MCU queue and
        calls the method decorated with @assigning_job to assign jobs to the modules
        :return: None
        """
        job = self.shared_queue.get()
        if self._pattern['assigning_job']:
            self._pattern['assigning_job'](self._mcu_instance, job)
        self.shared_queue.task_done()

    def add_module(self, module):
        self._modules.append(module)

    def run(self):
        """
        It is the method that starts the whole mcu.
        Here the various processes necessary for correct operation are started
        :return: None
        """
        if self._mcu_instance is None:
            raise AssertionError('The Mcu instance is None')

        looped(self._processor, daemon=False)


class McuPattern:

    """
    The McuPattern object is used to store the decorated methods in the MCU.
    If we want to use this scheme we need to initialize it as a class attribute in the inherited MCU
    """

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

    """
    MCU (Modules Central Unit)
    It is the main object that manages the communication between the modules.
    It is very important because it gives a common base to all processes
    by offering the shared queue administered by the McuController
    """

    def __init__(self, name):
        # Call to the constructor of the Thread class.
        # By default the Mcu process is not a thread daemon
        super().__init__(name=name, daemon=False)
        self.logger = logging.getLogger(name)
        self.controller = McuController()

    def register_modules(self, modules):
        candidate_modules = list(dict.fromkeys(modules))

        if all(module in self.controller.get_modules() for module in candidate_modules):
            raise AssertionError('The modules have already been registered')

        for module in candidate_modules:
            # Here the MCU receiver is saved on the new modules to be registered
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
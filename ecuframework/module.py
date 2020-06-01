import threading
import logging
import queue

from ecuframework.util import looped


class Module(threading.Thread):

    """
    It is the object that allows you to manage multiple threads that perform certain actions.
    It can be grouped into multiple types and is used to manage a section of the entire project.
    There can be many modules in a project that communicate to solve or execute certain problems
    """

    class Pattern:

        """
        The ModulePattern object is used to store the decorated methods in the Module.
        If we want to use this scheme, we have to initialize it as a class attribute in the inherited Module
        """

        def __init__(self):
            self._handler_functions = {
                'goal_solvers': {},
                'timers': {},
                'main_loop': None,
                'setup': None,
                'on_incoming_data': None
            }

        def solve(self, job_goal):
            def decorator(f):
                self._handler_functions['goal_solvers'][job_goal.name.lower()] = f

            return decorator

        def timer(self, name, interval):
            def decorator(f):
                self._handler_functions['timers'][name] = {'interval': interval, 'function': f}
                return f

            return decorator

        def main_loop(self, interval=None):
            def decorator(f):
                self._handler_functions['main_loop'] = {'interval': interval, 'function': f}
                return f

            return decorator

        def setup(self):
            def decorator(f):
                self._handler_functions['setup'] = f
                return f

            return decorator

        def on_incoming_data(self):
            def decorator(f):
                self._handler_functions['on_incoming_data'] = f
                return f

            return decorator

    class _Controller:

        """
        It is the class that manages all Module entirely
        """

        # Stores the Module pattern.
        # Through this access is made to methods decorated with the support of ModulePattern objects
        _pattern = {}

        # It is the receiver object of MCU that will be used to send jobs
        _receiver_mcu = None

        # Instance of the Module
        _module_instance = None

        def __init__(self, module_instance):
            self._module_instance = module_instance

        def get_pattern(self):
            return self._pattern

        def get_module_instance(self):
            return self._module_instance

        def register_receiver(self, receiver_mcu):
            self._receiver_mcu = receiver_mcu

        def register_pattern(self, module_pattern):
            self._pattern = module_pattern.__dict__['_handler_functions']

        def send_job(self, job):
            """
            Calling this method sends a job passed in input to the registered receiver
            :param job: job to be sent
            :return: None
            """
            if self._receiver_mcu is None:
                return
            self._receiver_mcu.get(job)

        def run_job(self, job):
            """
            Executes the job by calling the method decorated with @solve().
            It basically serves to define a method for solving a specific goal job
            :param job: job to be executed
            :return: None
            """
            if job is None:
                return
            try:
                self._pattern['goal_solvers'][job.goal.name.lower()](self._module_instance, job)
            except AttributeError as e:
                print(e)

    def __init__(self, instance, tag):
        # Call to the constructor of the Thread class.
        # By default the Mcu process is not a thread daemon
        super().__init__(name=f'Module[{tag}]', daemon=False)
        self.tag = tag
        self.logger = logging.getLogger(tag)
        self.controller = self._Controller(module_instance=instance)
        self.queue = queue.PriorityQueue()

    def _inner_on_incoming_data(self):
        job = self.queue.get()
        if job is not None:
            self.controller.get_pattern()['on_incoming_data'](self.controller.get_module_instance(), job)
        self.queue.task_done()

    def run(self):
        module_instance = self.controller.get_module_instance()
        pattern = self.controller.get_pattern()

        if module_instance is None:
            raise AssertionError('The module instance is None')

        if not pattern:
            raise AssertionError('The pattern of module is empty')

        if pattern['setup']:
            pattern['setup'](module_instance)
        if pattern['on_incoming_data']:
            looped(self._inner_on_incoming_data)
        if pattern['timers']:
            for timer_name in pattern['timers']:
                function = pattern['timers'][timer_name]['function']
                interval = pattern['timers'][timer_name]['interval']
                looped(function, interval, self=module_instance)
        if pattern['main_loop']:
            looped(pattern['main_loop']['function'], seconds=pattern['main_loop']['interval'],
                   self=module_instance)

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

        def main_loop(self):
            def decorator(f):
                self._handler_functions['main_loop'] = f
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

        def __init__(self):
            # It is the queue that contains all the jobs sent by other modules through MCU
            self.queue = queue.PriorityQueue()

        def register_receiver(self, receiver_mcu):
            self._receiver_mcu = receiver_mcu

        def register_pattern(self, module_pattern):
            self._pattern = module_pattern.__dict__['_handler_functions']

        def bind(self, module_instance):
            self._module_instance = module_instance

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

        def _inner_on_incoming_data(self):
            """
            Prepare returns the next job from the queue to the method decorated with @on_incoming_data()
            :return: None
            """
            job = self.queue.get()
            if job is not None:
                self._pattern['on_incoming_data'](self._module_instance, job)
            self.queue.task_done()

        def run(self):
            """
            It is the method that starts the whole Module.
            Here the various processes necessary for correct operation are started.
            The first to be performed is the setup method.
            Then the on_incoming_data and timers threads are started. Finally the main_loop thread is created
            :return: None
            """
            if self._module_instance is None:
                raise AssertionError('The module instance is None')

            if self._pattern['setup']:
                self._pattern['setup'](self._module_instance)
            if self._pattern['on_incoming_data']:
                looped(self._inner_on_incoming_data)
            if self._pattern['timers']:
                for timer_name in self._pattern['timers']:
                    function = self._pattern['timers'][timer_name]['function']
                    interval = self._pattern['timers'][timer_name]['interval']
                    looped(function, interval, self=self._module_instance)
            if self._pattern['main_loop']:
                looped(self._pattern['main_loop'], seconds=1, self=self._module_instance)

    def __init__(self, instance, tag):
        # Call to the constructor of the Thread class.
        # By default the Mcu process is not a thread daemon
        super().__init__(name=f'Module[{tag}]', daemon=False)
        self.tag = tag
        self.logger = logging.getLogger(tag)
        self.controller = self._Controller()
        self.controller.bind(instance)

    def run(self):
        self.controller.run()

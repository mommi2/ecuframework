import threading
import logging
import queue

from ecuframework.util import looped


class ModuleController:
    _pattern = {}
    _receiver_mcu = None

    _module_instance = None

    def __init__(self):
        self._queue = queue.PriorityQueue()

    def put_job(self, job):
        self._queue.put(job)

    def register_receiver(self, receiver_mcu):
        self._receiver_mcu = receiver_mcu

    def init(self, module_instance, module_pattern):
        self._module_instance = module_instance
        self._pattern = module_pattern.__dict__['_handler_functions']

    def send_new_job(self, job):
        if self._receiver_mcu is None:
            return
        self._receiver_mcu.get(job)

    def run_job(self, job):
        if job is None:
            return
        try:
            self._pattern['goal_solvers'][job.goal.name.lower()](self._module_instance, job)
        except AttributeError as e:
            print(e)

    def _inner_on_incoming_data(self):
        job = self._queue.get()
        if job is not None:
            self._pattern['on_incoming_data'](self._module_instance, job)
        self._queue.task_done()

    def run(self):
        if self._module_instance is None:
            raise AssertionError('The module instance is none')

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


class ModulePattern:

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


class Module(threading.Thread):

    def __init__(self, name, module_type):
        super().__init__(name=name, daemon=False)
        self.module_type = module_type
        self.logger = logging.getLogger(name)
        self.controller = ModuleController()

    def register_receiver(self, receiver_mcu):
        self.controller.register_receiver(receiver_mcu)

    def run(self):
        self.controller.run()

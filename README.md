# ECUframework

**ECUframework** (*Electronic Central Unit*) was born with the intent to simplify and speed up the process of writing code of IoT applications, making the developer avoid tedious and repetitive operations. It offer a solid and consolidated structure that lays the foundation for your application.
The goal of the framework is to introduce as many people as possible to the world of IoT making the writing of an application accessible, legible, and fun.

For further information about ECUframework read the wiki

## Documentation
https://github.com/tommasoviciani/ecuframework/wiki

## Installation
PyPI: https://pypi.org/project/ecuframework/
    
    pip install ecuframework


## Example
```python
from enum import Enum

from ecuframework.job import Job
from ecuframework.mcu import Mcu
from ecuframework.module import Module


class JobGoal(Enum):
    GOAL1 = 1
    GOAL2 = 2


class Module1(Module):

    # The pattern object must always be present in our modules because it stores our decorated methods
    mp = Module.Pattern()

    # The tag is a string that identifies a specific module for distributing jobs
    tag = 'm1'

    def __init__(self):
        # Call the constructor of the Module class. As arguments, it accepts the tag of the module that we are going
        # to initialize, and the instance of module needed to reach the jobs of the other modules.
        # Always put on top of the code
        super().__init__(instance=self, tag=self.tag)

        # Always make sure to call this method after each call to the Module class constructor.
        # Record the module pattern
        self.controller.register_pattern(self.mp)

        # Some variables of example
        self.count = 2
        self.recevied_count = 0

    @mp.setup()
    def setup(self):
        """
        The method decorated with @setup() will be executed only once when starting our module. It is used to configure our
        variables
        """
        print(f'{self.tag}: setup')

    @mp.on_incoming_data()
    def on_incoming_data(self, job):
        """
        The method decorated with @on_incoming_data() will be called when a new job is available in the queue. When
        we use this decorator, there must be an input job which is precisely the one obtained from the queue
        """
        print(f'{self.tag}: received a new job')

        # Call this method to execute the job just obtained from the queue
        self.controller.run_job(job)

    @mp.timer(name='timer', interval=5)
    def timer(self):
        """
        The method decorated with @timer() is a subprocess which will be executed cyclically. There can be multiple timers in
        a module and each of them needs a name to distinguish one from the other and a time interval expressed in seconds
        """
        print(f'{self.tag}[timer]: send job')
        self.controller.send_job(
            Job(data={'x': 'module1'}, goal=JobGoal.GOAL1, producer=self.tag, recipient='m2'))

    @mp.main_loop(interval=1)
    def main_loop(self):
        """
        The method decorated with @main_loop() is the subprocess that continues to run indefinitely until the module process
        is killed. It is performed cyclically and is the last decorated method that is called
        """
        print(f'{self.tag}: count = {self.count + self.recevied_count}')
        self.count += self.recevied_count

    @mp.solve(JobGoal.GOAL2)
    def solve_goal1(self, job):
        """
        The method decorated with @solve() defines how the module should behave when a given job with the usual JobGoal passed
        as input to the decorator is executed by the run_job() method of the controller.
        The decorated method should, therefore, accept this job as an argument
        """
        print(f'{self.tag}: Received {job.data} from {job.producer}')
        self.recevied_count = job.data['x']


class Module2(Module):

    # The pattern object must always be present in our modules because it stores our decorated methods
    mp = Module.Pattern()

    # The tag is a string that identifies a specific module for distributing jobs
    tag = 'm2'

    def __init__(self):
        # Call the constructor of the Module class. As arguments, it accepts the tag of the module that we are going
        # to initialize, and the instance of module needed to reach the jobs of the other modules.
        # Always put on top of the code
        super().__init__(instance=self, tag=self.tag)

        # Always make sure to call this method after each call to the Module class constructor.
        # Record the module pattern
        self.controller.register_pattern(self.mp)

        # Some variables of example
        self.count = 0

    @mp.setup()
    def setup(self):
        """
        The method decorated with @setup() will be executed only once when starting our module. It is used to configure our
        variables
        """
        print(f'{self.tag}: setup')

    @mp.on_incoming_data()
    def on_incoming_data(self, job):
        """
        The method decorated with @on_incoming_data() will be called when a new job is available in the queue. When
        we use this decorator, there must be an input job which is precisely the one obtained from the queue
        """

        # Call this method to execute the job just obtained from the queue
        self.controller.run_job(job)

    @mp.timer(name='timer', interval=8)
    def timer(self):
        """
        The method decorated with @timer() is a subprocess which will be executed cyclically. There can be multiple timers in
        a module and each of them needs a name to distinguish one from the other and a time interval expressed in seconds
        """
        print(f'{self.tag}[timer]: send job')
        self.controller.send_job(
            Job(data={'x': 2}, goal=JobGoal.GOAL2, producer=self.tag, recipient='m1'))

    @mp.solve(JobGoal.GOAL1)
    def solve_goal2(self, job):
        """
        The method decorated with @solve() defines how the module should behave when a given job with the usual JobGoal passed
        as input to the decorator is executed by the run_job() method of the controller.
        The decorated method should, therefore, accept this job as an argument
        """
        print(f'{self.tag}: Received {job.data} from {job.producer}')


class MyMcu(Mcu):

    # The pattern object must always be present in our MCU because it stores our decorated methods
    mp = Mcu.Pattern()

    tag = 'mcu'

    def __init__(self):
        # Call to the constructor of the MCU class. As arguments, it accepts the name of the MCU that we are going
        # to initialize. Always put on top of the code
        super().__init__(instance=self, tag=self.tag)

        # Always make sure to call this method after each call to the MCU class constructor.
        # Record the MCU pattern
        self.controller.register_pattern(self.mp)

    @mp.on_receiver()
    def on_receiver(self, job):
        """
        The method decorated with @on_receiver() as a receiver has as input the job sent by the sending module
        """
        if job is None:
            return
        self.shared_queue.put(job)

    @mp.assigning_job()
    def assigning_job(self, job):
        """
        The method decorated with @assinging_job() is called when a job shows up in the queue. In a nutshell, this decorated
        method is used to distribute shared queue jobs to modules
        """

        # Here the recipient module is obtained to which the job in question must be assigned
        module_recipient_result = self.controller.get_recipient_module(lambda module_recipient: module_recipient.tag == job.recipient)

        module_recipient_result.queue.put(job) if module_recipient_result else print(
            f'{self.tag}: the {job.target} destination of the job {job.goal} is unreachable')


if __name__ == '__main__':
    print('Start')
    mcu = MyMcu()
    mcu.register_modules([Module1(), Module2()])
    mcu.start()
```

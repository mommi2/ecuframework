# ECUframework

**ECUframework** (*Electronic Central Unit*) was born with the intent to simplify and speed up the writing of the code of IoT applications, making the developer avoid tedious and repetitive operations. It offers a solid and consolidated structure that lays the foundation for your application.
The goal of the framework is to bring as many people as possible to the world of IoT making the writing of an application accessible, legible, and fun.

For the specific functioning of the ECUframework consult the wiki

## Installation
PyPI: https://pypi.org/project/ecuframework/
    
    pip install ecuframework


## Example
```python
from enum import Enum

from ecuframework.job import Job
from ecuframework.mcu import Mcu, McuPattern
from ecuframework.module import Module, ModulePattern


class JobGoal(Enum):
    GOAL1 = 1
    GOAL2 = 2
    

class ModuleType(Enum):
    MODULE1 = 1,
    MODULE2 = 2


class Module1(Module):
    # The pattern object must always be present in our modules because it stores our decorated methods
    mp = ModulePattern()
    
    # Simply the name of the module
    name = 'm1'
    
    count = 2
    recevied_count = 0

    def __init__(self):
        # Call to the constructor of the Module class. As arguments, it accepts the name of the module that we are going 
        # to initialize and the type of module needed to reach the jobs of the other modules.
        # Always put on top of the code
        super().__init__(name=self.name, module_type=ModuleType.MODULE1)
        
        # Always make sure to call this method after each call to the Module class constructor.
        # Record the instance of our module and the pattern
        self.controller.init(self, self.mp)

    """
    The method decorated with @setup() will be executed only once when starting our module. It is used to configure our 
    variables
    """
    @mp.setup()
    def setup(self):
        print(f'{self.name}: setup')
    
    """
    The method decorated with @on_incoming_data() will be called when a new job is available in the queue. When 
    we use this decorator, there must be an input job which is precisely the one obtained from the queue
    """
    @mp.on_incoming_data()
    def on_incoming_data(self, job):
        print(f'{self.name}: received a new job')
        # Call this method to execute the job just obtained from the queue
        self.controller.run_job(job)
    
    """
    The method decorated with @timer() is a subprocess which will be executed cyclically. There can be multiple timers in 
    a module and each of them needs a name to distinguish one from the other and a time interval expressed in seconds
    """
    @mp.timer(name='timer1', interval=5)
    def timer1(self):
        print(f'{self.name}: send job from timer1')
        self.controller.send_new_job(
            Job(data={'x': 'module1'}, goal=JobGoal.GOAL1, producer=self.name, target=ModuleType.MODULE2)
    
    """
    The method decorated with @main_loop() is the subprocess that continues to run indefinitely until the module process 
    is killed. It is performed cyclically and is the last decorated method that is called
    """
    @mp.main_loop()
    def main_loop(self):
        print(f'{self.name}: count = {self.count + self.recevied_count}')
        self.count += self.recevied_count
    
    """
    The method decorated with @solve() defines how the module should behave when a given job with the usual JobGoal passed 
    as input to the decorator is executed by the run_job() method of the controller. 
    The decorated method should, therefore, accept this job as an argument
    """
    @mp.solve(JobGoal.GOAL2)
    def goal2(self, job):
        print(f'{self.name}: Received {job.data} from {job.producer}')
        self.recevied_count = job.data['x']


class Module2(Module):
    # The pattern object must always be present in our modules because it stores our decorated methods
    mp = ModulePattern()
    
    # Simply the name of the module
    name = 'm2'

    count = 0

    def __init__(self):
        # Call to the constructor of the Module class. As arguments, it accepts the name of the module that we are going 
        # to initialize and the type of module needed to reach the jobs of the other modules.
        # Always put on top of the code
        super().__init__(name=self.name, module_type=ModuleType.MODULE2)

        # Always make sure to call this method after each call to the Module class constructor.
        # Record the instance of our module and the pattern
        self.controller.init(self, self.mp)
    
    """
    The method decorated with @setup() will be executed only once when starting our module. It is used to configure our 
    variables
    """
    @mp.setup()
    def setup(self):
        print(f'{self.name}: setup')
    
    """
    The method decorated with @on_incoming_data() will be called when a new job is available in the queue. When 
    we use this decorator, there must be an input job which is precisely the one obtained from the queue
    """
    @mp.on_incoming_data()
    def on_incoming_data(self, job):
        # Call this method to execute the job just obtained from the queue
        self.controller.run_job(job)
    
    """
    The method decorated with @timer() is a subprocess which will be executed cyclically. There can be multiple timers in 
    a module and each of them needs a name to distinguish one from the other and a time interval expressed in seconds
    """
    @mp.timer(name='timer2', interval=8)
    def timer1(self):
        print(f'{self.name}: send job from timer2')
        self.controller.send_new_job(
            Job(data={'x': 2}, goal=JobGoal.GOAL2, producer=self.name, target=ModuleType.MODULE1))
    
    """
    The method decorated with @solve() defines how the module should behave when a given job with the usual JobGoal passed 
    as input to the decorator is executed by the run_job() method of the controller. 
    The decorated method should, therefore, accept this job as an argument
    """
    @mp.solve(JobGoal.GOAL1)
    def goal2(self, job):
        print(f'{self.name}: Received {job.data} from {job.producer}')


class MyMcu(Mcu):
    # The pattern object must always be present in our MCU because it stores our decorated methods
    mp = McuPattern()

    name = 'mcu'

    def __init__(self):
        # Call to the constructor of the MCU class. As arguments, it accepts the name of the MCU that we are going 
        # to initialize. Always put on top of the code
        super().__init__(name=self.name)

        # Always make sure to call this method after each call to the MCU class constructor.
        # Record the instance of our MCU and the pattern
        self.controller.init(self, self.mp)
    
    """
    The method decorated with @on_receiver() as a receiver has as input the job sent by the sending module
    """
    @mp.on_receiver()
    def on_receiver(self, job):
        if job is None:
            return
        self.controller.shared_queue.put(job)
    
    """
    The method decorated with @assinging_job() is called when a job shows up in the queue. In a nutshell, this decorated 
    method is used to distribute shared queue jobs to modules
    """
    @mp.assigning_job()
    def assigning_job(self, job):
        # Here the recipient module is obtained to which the job in question must be assigned
        module_target = self.controller.get_module_target(job.target)

        module_target.controller.put_job(job) if module_target else print(
            f'The {job.target} destination of the job {job.goal} is unreachable')


if __name__ == '__main__':
    print('Start')
    mcu = MyMcu()
    mcu.register_modules([Module1(), Module2()])
    mcu.start()
```

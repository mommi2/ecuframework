# ECUframework

Documentation: work in progress...

Example:
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
    mp = ModulePattern()

    name = 'm1'
    count = 2
    recevied_count = 0

    def __init__(self):
        super().__init__(name=self.name, module_type=ModuleType.MODULE1)
        self.controller.init(self, self.mp)

    @mp.setup()
    def setup(self):
        print(f'{self.name}: setup')

    @mp.on_incoming_data()
    def on_incoming_data(self, job):
        print(f'{self.name}: received a new job')
        self.controller.run_job(job)

    @mp.timer(name='timer1', interval=5)
    def timer1(self):
        print(f'{self.name}: send job from timer1')
        self.controller.send_new_job(
            Job(data={'x': 'module1'}, goal=JobGoal.GOAL1, producer=self.name, target=ModuleType.MODULE2))

    @mp.solve(JobGoal.GOAL2)
    def goal2(self, job):
        print(f'{self.name}: Received {job.data} from {job.producer}')
        self.recevied_count = job.data['x']

    @mp.main_loop()
    def main_loop(self):
        print(f'{self.name}: count = {self.count + self.recevied_count}')
        self.count += self.recevied_count


class Module2(Module):
    mp = ModulePattern()

    name = 'm2'
    count = 0

    def __init__(self):
        super().__init__(name=self.name, module_type=ModuleType.MODULE2)
        self.controller.init(self, self.mp)

    @mp.setup()
    def setup(self):
        print(f'{self.name}: setup')

    @mp.on_incoming_data()
    def on_incoming_data(self, job):
        self.controller.run_job(job)

    @mp.timer(name='timer2', interval=8)
    def timer1(self):
        print(f'{self.name}: send job from timer2')
        self.controller.send_new_job(
            Job(data={'x': 2}, goal=JobGoal.GOAL2, producer=self.name, target=ModuleType.MODULE1))

    @mp.solve(JobGoal.GOAL1)
    def goal2(self, job):
        print(f'{self.name}: Received {job.data} from {job.producer}')


class MyMcu(Mcu):
    mp = McuPattern()

    name = 'mcu'

    def __init__(self):
        super().__init__(name=self.name)
        self.controller.init(self, self.mp)

    @mp.on_receiver()
    def on_receiver(self, job):
        if job is None:
            return
        self.controller.shared_queue.put(job)

    @mp.assigning_job()
    def assigning_job(self, job):
        module_target = self.controller.get_module_target(job.target)
        module_target.controller.put_job(job) if module_target else print(
            f'The {job.target} destination of the job {job.goal} is unreachable')


if __name__ == '__main__':
    print('Start')
    mcu = MyMcu()
    mcu.register_modules([Module1(), Module2()])
    mcu.start()
```

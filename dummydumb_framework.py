"""a fictitious ML framework for demonstration purposes.

replace references to dummydumb_framework with libraries of your choice
you can also extend dummydumb_framework and use it as a shim


Copyright 2023 Jean-Baptiste Escudié


This program is Free Software. You can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

"""

class DummyDumbBase:
    def __init__(self, *args, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)


class Dataset(DummyDumbBase): pass
class Dataloader(DummyDumbBase):
    def __iter__(self): yield (None, None)
    def __getitem__(self, item): pass

class Model(DummyDumbBase):
    def __call__(self, inputs): pass
    def load_checkpoint(self, buffer): self.state = buffer.read()
    def save_checkpoint(self, buffer): buffer.write(self.state)

class Loss(DummyDumbBase):
    def __call__(self, target, output):
        """`magically` decreasing dummy dumb loss"""
        last_loss = getattr(self, "last_loss", 10.777)
        loss = last_loss * (1 - .007)
        self.last_loss = loss
        return self
    def item(self): return getattr(self, "last_loss", 10.777)
    def backward(self): pass

class Optimizer(DummyDumbBase):
    def init(self): self.model.state = b"dummy dumb dumb"
    def step(self): self.model.state = self.model.state[1:] + self.model.state[:1]
    

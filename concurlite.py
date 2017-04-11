#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'eph'
__all__ = ['Thread', 'spawn', 'join']

import sys
from time import sleep
from heapq import heappop, heappush

try:
    from time import perf_counter
except ImportError:
    if sys.platform == 'win32':
        from time import clock as perf_counter
    else:
        from time import perf_counter


_push, _pop, _head = (lambda h: (lambda t: heappush(h, t),
                                 lambda: heappop(h),
                                 lambda: h[0]))([])


class Event(object):

    def is_set(self):
        return self.__set

    def __init__(self):
        self.__set = False
        self.__threads = []

    def set(self):
        if not self.__set:
            self.__set = True
            for thread in self.__threads:
                _push(thread)


class Thread(object):

    def is_alive(self):
        return self.__alive

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        if group is not None: raise ValueError('group should be None')
        self.name = name
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__time = perf_counter()
        self.__start = False
        self.__alive = True
        self.__iter = None

    def __lt__(self, other):
        return self.__time < other.__time

    def start(self):
        if self.__start:
            raise RuntimeError('threads can only be started once')
        self.__start = True
        _push(self)

    def run(self):
        if self.__target:
            return self.__target(*self.__args, **self.__kwargs)

    def join(self, timeout=None):
        if not self.__start:
            raise RuntimeError('cannot join thread before it is started')

        if timeout is not None:
            timeout += perf_counter()

        while self.__alive:

            # pop head thread
            try:
                thread = _pop()
            except IndexError:
                raise RuntimeError('event loop is stopped')

            # test if join() run out of time
            if timeout is not None and thread.__time > timeout:
                _push(thread)
                dt = timeout - perf_counter()
                if dt > 0: sleep(dt)
                break

            # wait until trigger time
            dt = thread.__time - perf_counter()
            if dt > 0: sleep(dt)

            # run thread.run() or convert to an iterator of steps
            if thread.__iter is None:
                it = thread.run()
                try:
                    it = iter(it)
                except:
                    thread.__alive = False
                    continue
                else:
                    thread.__iter = it
            else:
                it = thread.__iter

            # run this step
            try:
                res = next(it)
            except StopIteration:
                thread.__alive = False
                continue

            # store thread in event and wait for event.set()
            if isinstance(res, Event):
                if res.is_set():
                    res = None
                else:
                    res._Event__threads.append(thread)
                    continue

            # store thread in main list for next step
            t = perf_counter()
            thread.__time = t if res is None else t + res
            _push(thread)


def spawn(target, *args, **kwargs):
    thread = Thread(target=target, args=args, kwargs=kwargs)
    thread.start()
    return thread


def join(timeout=None):

    if timeout is not None:
        timeout += perf_counter()

    while True:

        # get head thread
        try:
            thread = _head()
        except IndexError:
            break

        # test if join() run out of time
        if timeout is not None:
            dt = timeout - perf_counter()
            if dt <= 0: break
        else:
            dt = None

        # join head thread
        thread.join(dt)

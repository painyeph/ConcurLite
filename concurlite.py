#!/usr/bin/env python
# -*- coding: utf-8 -*-

"A Pure Python concurrency library"

__author__ = 'eph'
__license__ = 'WTFPL v2'

__all__ = ['Event', 'Thread', 'Timer', 'CyclicThread',
           'spawn', 'delay', 'every', 'join', 'clear']

import sys
from time import sleep
from heapq import heappop, heappush
from numbers import Real

try:
    from time import perf_counter
except ImportError:
    if sys.platform == 'win32':
        from time import clock as perf_counter
    else:
        from time import time as perf_counter


_push, _pop, _head = (lambda h: (lambda t: heappush(h, t),
                                 lambda: heappop(h),
                                 lambda: h[0]))([])


class Event(object):

    def is_set(self):
        return self.__set

    def __init__(self):
        self.__set = False
        self.__handlers = []

    def set(self):
        if not self.__set:
            self.__set = True
            for func, args, kwargs in self.__handlers:
                func(*args, **kwargs)

    def _apply(self, func, *args, **kwargs):
        if self.__set:
            func(*args, **kwargs)
        else:
            self.__handlers.append((func, args, kwargs))


class Thread(object):

    @property
    def started(self):
        return self.__start

    def is_alive(self):
        return self.__alive

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        if group is not None: raise ValueError('group should be None')
        self.name = name
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__start = False
        self.__time = 0
        self.__alive = True
        self.__iter = None

    def __lt__(self, other):
        return self.__time < other.__time

    def start(self):
        if self.__start:
            raise RuntimeError('threads can only be started once')
        self.__start = True
        self.__time = perf_counter()
        if isinstance(self, Timer): self.__time += self.interval
        _push(self)

    def run(self):
        if self.__target:
            return self.__target(*self.__args, **self.__kwargs)

    def join(self, timeout=None):
        if not self.__start:
            raise RuntimeError('cannot join thread before it is started')

        if timeout is not None:
            timeout += perf_counter()

        while self.is_alive():

            # pop head thread
            try:
                thread = _pop()
            except IndexError:
                raise RuntimeError('event loop is stopped')

            # remove stopped cyclic thread
            if isinstance(thread, CyclicThread) and not thread.is_alive():
                continue

            # test if join() run out of time
            if timeout is not None and thread.__time > timeout:
                _push(thread)
                dt = timeout - perf_counter()
                if dt > 0: sleep(dt)
                break

            # wait until trigger time
            dt = thread.__time - perf_counter()
            if dt > 0: sleep(dt)

            # for cyclic thread
            if isinstance(thread, CyclicThread):
                thread.__time += thread.interval
                _push(thread)
                it = thread.run()
                try:
                    it = iter(it)
                except:
                    continue
                else:
                    thread = Thread()
                    thread.__start = True
                    thread.__iter = it

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

            # convert iterable to None/Number/Event
            if not (res is None or isinstance(res, (Real, Event))):
                try:
                    it = iter(res)
                except:
                    raise RuntimeError('invalid object yield from thread')

                timeout = None
                events = []
                for item in it:
                    if item is None: continue
                    elif isinstance(item, Event): events.append(item)
                    elif not isinstance(item, Real):
                        raise RuntimeError('invalid object yield from thread')
                    elif timeout is None or timeout > item: timeout = item

                if events:
                    res = Event()
                    for event in events: event._apply(res.set)
                    if timeout is not None: delay(timeout, res.set)
                elif timeout is None:
                    res = None
                else:
                    res = timeout

            # store thread in event and wait for event.set()
            if isinstance(res, Event):
                res._apply(_push, thread)
                continue

            # store thread in main list for next step
            t = perf_counter()
            thread.__time = t if res is None else t + res
            _push(thread)


class Timer(Thread):

    @property
    def interval(self):
        return self.__interval

    def __init__(self, interval, function, args=[], kwargs={}):
        self.__interval = interval
        Thread.__init__(self, None, function, None, args, kwargs)


class CyclicThread(Thread):

    @property
    def interval(self):
        return self.__interval

    def is_alive(self):
        return self.__alive

    def __init__(self, interval, group=None, target=None, name=None,
                       args=(), kwargs={}):
        self.__interval = interval
        self.__alive = True
        super(CyclicThread, self).__init__(group, target, name, args, kwargs)

    def stop(self):
        if not self.started:
            raise RuntimeError('cannot stop thread before it is started')
        self.__alive = False


def spawn(target, *args, **kwargs):
    thread = Thread(target=target, args=args, kwargs=kwargs)
    thread.start()
    return thread


def delay(interval, target=None, *args, **kwargs):
    if target is None:

        def _delay(target, *args, **kwargs):
            thread = Timer(interval, function=target, args=args, kwargs=kwargs)
            thread.start()
            return thread
        return _delay

    thread = Timer(interval, function=target, args=args, kwargs=kwargs)
    thread.start()
    return thread


def every(interval, target=None, *args, **kwargs):
    if target is None:

        def _every(target, *args, **kwargs):
            thread = CyclicThread(interval, target=target,
                                  args=args, kwargs=kwargs)
            thread.start()
            return thread
        return _every

    thread = CyclicThread(interval, target=target, args=args, kwargs=kwargs)
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

        # remove stopped cyclic thread
        if isinstance(thread, CyclicThread) and not thread.is_alive():
            _pop()
            continue

        # test if join() run out of time
        if timeout is not None:
            dt = timeout - perf_counter()
            if dt <= 0: break
        else:
            dt = None

        # join head thread
        thread.join(dt)


def clear():
    try:
        while True: _pop()
    except IndexError:
        pass

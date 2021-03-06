#!/usr/bin/env python
# -*- coding: utf-8 -*-

"A pure Python concurrency library"

__author__ = 'eph'
__license__ = 'WTFPL v2'

__all__ = ['Event', 'Thread', 'Timer', 'Cyclic',
           'spawn', 'delay', 'every', 'joinall', 'join', 'clear']

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

    def is_alive(self):
        return not self.__stop.is_set()

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        if group is not None: raise ValueError('group should be None')
        self.name = name
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__start = Event()
        self.__stop = Event()
        self.__time = 0
        self.__iter = None

    def __lt__(self, other):
        return self.__time < other.__time

    def start(self):
        if self.__start.is_set():
            raise RuntimeError('threads can only be started once')
        self.__start.set()
        self.__time = perf_counter()
        if isinstance(self, Timer): self.__time += self.interval
        _push(self)

    def stop(self):
        if not self.__start.is_set():
            raise RuntimeError('cannot stop thread before it is started')
        self.__stop.set()

    def run(self):
        if self.__target:
            return self.__target(*self.__args, **self.__kwargs)

    def join(self, timeout=None):
        '''Wait until the thread terminates. This function should only
        be used outside of threads. In threads, use `yield thread`
        instead.
        '''
        if timeout is not None: timeout += perf_counter()

        while not self.__stop.is_set():

            # pop head thread
            try:
                thread = _pop()
            except IndexError:
                break

            # remove stopped thread
            if thread.__stop.is_set(): continue

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
            if isinstance(thread, Cyclic):
                thread.__time += thread.interval
                _push(thread)
                it = thread.run()
                try:
                    it = iter(it)
                except:
                    continue
                else:
                    thread = Thread()
                    thread.__start.set()
                    thread.__iter = it

            # run thread.run() or convert to an iterator of steps
            if thread.__iter is None:
                it = thread.run()
                try:
                    it = iter(it)
                except:
                    thread.__stop.set()
                    continue
                else:
                    thread.__iter = it
            else:
                it = thread.__iter

            # run this step
            try:
                res = next(it)
            except StopIteration:
                thread.__stop.set()

            if thread.__stop.is_set():
                it.close()
                continue

            # convert yielded object to None / Number / Event
            if isinstance(res, Thread): res = res.__stop
            if not (res is None or isinstance(res, (Real, Event))):
                try:
                    it = iter(res)
                except:
                    raise RuntimeError('invalid object yield from thread')

                t_wait = None
                events = []
                for item in it:
                    if item is None: continue
                    elif isinstance(item, Event): events.append(item)
                    elif isinstance(item, Thread): events.append(item.__stop)
                    elif not isinstance(item, Real):
                        raise RuntimeError('invalid object yield from thread')
                    elif t_wait is None or t_wait > item: t_wait = item

                if len(events) == 1 and t_wait is None:
                    res = events[0]
                elif events:
                    res = Event()
                    for event in events: event._apply(res.set)
                    if t_wait is not None: delay(t_wait, res.set)
                elif t_wait is None:
                    res = None
                else:
                    res = t_wait

            # store thread in event and wait for event.set()
            if isinstance(res, Event):
                def callback(thread):
                    thread.__time = perf_counter()
                    _push(thread)
                res._apply(callback, thread)
                continue

            # store thread in main list for next step
            t_now = perf_counter()
            thread.__time = t_now if res is None else t_now + res
            _push(thread)


class Timer(Thread):

    @property
    def interval(self):
        return self.__interval

    def __init__(self, interval, function=None, args=[], kwargs={}):
        self.__interval = interval
        Thread.__init__(self, None, function, None, args, kwargs)


class Cyclic(Thread):

    @property
    def interval(self):
        return self.__interval

    def __init__(self, interval, function=None, args=[], kwargs={}):
        self.__interval = interval
        Thread.__init__(self, None, function, None, args, kwargs)


def spawn(target, *args, **kwargs):
    thread = Thread(target=target, args=args, kwargs=kwargs)
    thread.start()
    return thread


def delay(interval, target=None, *args, **kwargs):

    if target is None:  # as a decorator
        def _delay(target, *args, **kwargs):
            thread = Timer(interval, target, args, kwargs)
            thread.start()
            return thread
        return _delay

    thread = Timer(interval, target, args, kwargs)
    thread.start()
    return thread


def every(interval, target=None, *args, **kwargs):

    if target is None:  # as a decorator
        def _every(target, *args, **kwargs):
            thread = Cyclic(interval, target, args, kwargs)
            thread.start()
            return thread
        return _every

    thread = Cyclic(interval, target, args, kwargs)
    thread.start()
    return thread


def joinall(threads, timeout=None):

    if timeout is not None:
        timeout += perf_counter()

    for thread in threads:

        # test if join() run out of time
        if timeout is not None:
            dt = timeout - perf_counter()
            if dt <= 0: break
        else:
            dt = None

        # join head thread
        thread.join(dt)


def join(timeout=None):

    def iter_threads():
        while True:

            # get head thread
            try:
                thread = _head()
            except IndexError:
                return

            # remove stopped cyclic thread
            if not thread.is_alive():
                _pop()
                continue

            yield thread

    joinall(iter_threads(), timeout)


def clear():
    try:
        while True: _pop()
    except IndexError:
        pass

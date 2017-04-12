#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'eph'
__license__ = 'WTFPL v2'

import unittest

import concurlite


class TestConcurLite(unittest.TestCase):

    def test_spawn(self):
        l = []

        @concurlite.spawn
        def thread1():
            l.append(1)
            yield
            l.append(3)
            yield
            l.append(5)
            yield
            l.append(7)

        @concurlite.spawn
        def thread2():
            l.append(2)
            yield
            l.append(4)
            yield
            l.append(6)
            yield
            l.append(8)

        concurlite.join()
        self.assertEqual(l, [1, 2, 3, 4, 5, 6, 7, 8])

    def test_delay(self):
        l = []
        event = concurlite.Event()

        @concurlite.spawn
        def thread1():
            while not event.is_set():
                l.append(1)
                yield 0.2

        @concurlite.delay(0.5)
        def thread2():
            event.set()

        concurlite.join()
        self.assertEqual(l, [1, 1, 1])

    def test_every(self):
        l = []

        @concurlite.every(0.5)
        def thread1():
            l.append(1)
            yield 0.2
            l.append(3)

        @concurlite.every(0.5)
        def thread2():
            yield 0.1
            l.append(2)
            yield 0.2
            l.append(4)

        concurlite.join(0.9)
        self.assertEqual(l, [1, 2, 3, 4, 1, 2, 3, 4])
        concurlite.clear()

    def test_every_stop(self):
        l = []

        @concurlite.every(0.1)
        def thread1():
            l.append(1)
            if len(l) >= 6:
                thread1.stop()

        concurlite.join()
        self.assertEqual(l, [1, 1, 1, 1, 1, 1])

    def test_sleep(self):
        l = []

        def _thread(i):
            yield i * 0.1
            l.append(i)

        threads = [ concurlite.Thread(target=_thread, args=(i,))
                    for i in (3, 8, 1, 5, 6, 4, 7, 2) ]
        for thread in threads: thread.start()
        concurlite.join()
        self.assertEqual(l, [1, 2, 3, 4, 5, 6, 7, 8])

    def test_event(self):
        l = []

        event1 = concurlite.Event()
        event2 = concurlite.Event()

        @concurlite.spawn
        def thread1():
            l.append(1)
            yield event1
            l.append(4)
            yield
            l.append(6)
            yield event1
            l.append(7)
            yield event2.set()
            l.append(9)

        @concurlite.spawn
        def thread2():
            l.append(2)
            yield
            l.append(3)
            yield event1.set()
            l.append(5)
            yield event2
            l.append(8)

        concurlite.join()
        self.assertEqual(l, [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_call(self):
        l = []

        event1 = concurlite.Event()
        event2 = concurlite.Event()

        def subroutine():
            l.append(3)
            yield 0.3, event1
            l.append(5)
            yield event1, event2
            l.append(7)

        @concurlite.spawn
        def thread1():
            l.append(1)
            yield concurlite.spawn(subroutine)
            l.append(9)

        @concurlite.spawn
        def thread2():
            l.append(2)
            yield 0.2
            l.append(4)
            yield 0.2
            l.append(6)
            yield event2.set()
            l.append(8)

        concurlite.join()
        self.assertEqual(l, [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_thread_join(self):
        l = []

        @concurlite.spawn
        def thread1():
            yield 0.4

        @concurlite.spawn
        def thread2():
            yield 0.8

        @concurlite.spawn
        def thread3():
            l.append(1)
            yield thread1
            l.append(3)
            yield thread2
            l.append(5)

        @concurlite.spawn
        def thread4():
            l.append(2)
            yield thread1
            l.append(4)
            yield thread2
            l.append(6)

        concurlite.join()
        self.assertEqual(l, [1, 2, 3, 4, 5, 6])

    def test_join_timeout(self):
        l = []

        @concurlite.spawn
        def thread1():
            l.append(1)
            yield 0.2
            l.append(2)
            yield 0.2
            l.append(3)
            yield 0.2
            l.append(4)

        concurlite.join(0.5)
        self.assertEqual(l, [1, 2, 3])
        concurlite.clear()


if __name__ == '__main__':
    unittest.main()

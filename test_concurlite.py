#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: eph

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


if __name__ == '__main__':
    unittest.main()

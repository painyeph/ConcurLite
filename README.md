## Basic concurrency

```python
import concurlite

@concurlite.spawn
def foo():         #  <--------------------+
    print(1)       #                       |
    yield          #  >--+                 |
    print(3)       #     |  <--+           |
                   #     |     |           |
@concurlite.spawn  #     |  >- | ----+     |
def bar():         #  <--+     |     |     |
    print(2)       #           |     |     |
    yield          #  >--------+     |     |
    print(4)       #  <--------------+     |
                   #                       |
concurlite.join()  # ----------------------+
```

## Switch with event

```python
import concurlite

event1 = concurlite.Event()
event2 = concurlite.Event()

@concurlite.spawn
def thread1():          #  <--------------------------------+
    print(1)            #                                   |
    yield event1        #  >--+                             |
    print(4)            #     |  <--+                       |
    yield               #     |  >- | ----+                 |
    print(6)            #     |     |     |  <--+           |
    yield event1        #     |     |     |     |           |
    print(7)            #     |     |     |     |           |
    yield event2.set()  #     |     |     |  >- | ----+     |
                        #     |     |     |     |     |     |
@concurlite.spawn       #     |     |     |     |     |     |
def thread2():          #  <--+     |     |     |     |     |
    print(2)            #           |     |     |     |     |
    yield 1             # sleep 1s  |     |     |     |     |
    print(3)            #           |     |     |     |     |
    yield event1.set()  #  >--------+     |     |     |     |
    print(5)            #  <--------------+     |     |     |
    yield event2        #  >--------------------+     |     |
    print(8)            #  <--------------------------+     |
                        #                                   |
concurlite.join()       # ----------------------------------+
```

## Comparison with multithreading

| ConcurLite                              | Multithreading                         |
|-----------------------------------------|----------------------------------------|
| thread = concurlite.Thread(target=func) | thread = threading.Thread(target=func) |
| thread.start()                          | thread.start()                         |
| thread.join(timeout)                    | thread.join(timeout)                   |
| yield                                   | time.sleep(0)                          |
| yield secs                              | time.sleep(secs)                       |
| event = concurlite.Event()              | event = threading.Event()              |
| event.set()                             | event.set()                            |
| yield event                             | event.wait()                           |
| yield event, timeout                    | event.wait(timeout)                    |
| yield event1, event2, timeout           |                                        |

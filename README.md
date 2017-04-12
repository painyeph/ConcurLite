## Basic concurrency

```python
import concurlite

@concurlite.spawn
def foo():         #  <--------------------+
    print(1)       #                       |
    yield          #  >--+                 |
    print(3)       #     |  <--+           |
                   #     |  >- | ----+     |
@concurlite.spawn  #     |     |     |     |
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

|                      | ConcurLite                                | Multithreading                         |
|----------------------|-------------------------------------------|----------------------------------------|
| Create a thread      | thread = concurlite.Thread(target=func)   | thread = threading.Thread(target=func) |
| Start a thread       | thread.start()                            | thread.start()                         |
| Join a thread        | yield thread                              | thread.join()                          |
| Join with timeout    | yield thread, timeout                     | thread.join(timeout)                   |
| Call a subroutine    | yield concurlite.spawn(subroutine, *args) | subroutine(*args)                      |
| Switch among threads | yield                                     | time.sleep(0)                          |
| Wait for a time      | yield secs                                | time.sleep(secs)                       |
| Create an event      | event = concurlite.Event()                | event = threading.Event()              |
| Trigger an event     | event.set()                               | event.set()                            |
| Wait for an evnet    | yield event                               | event.wait()                           |
| Wait with timeout    | yield event, timeout                      | event.wait(timeout)                    |
| Wait for any object  | yield thread, event, timeout              |                                        |

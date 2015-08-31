# ThreadPoolExecutor based on python3 ThreadPoolExecutor

import atexit
import logging
import threading
import traceback
import weakref
from Queue import Queue

_threads_queues = weakref.WeakKeyDictionary()
_shutdown = False

def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t,q in items:
        q.put(None)
    for t,q in items:
        t.join()

atexit.register(_python_exit)

class _Job(object):
    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fn(*self.args, **self.kwargs)


def _worker(executor_reference, job_queue):
    try:
        while True:
            job = job_queue.get(block=True)
            if job != None:
                job.run()
                del job
                continue
            executor = executor_reference()
            if _shutdown or executor is None or executor._shutdown:
                job_queue.put(None)
                return
            del executor
    except BaseException, e:
        logging.error('Exception in worker: '+traceback.format_exc())


class ThreadPoolExecutor(object):
    def __init__(self, max_workers, thread_name=None):
        self._max_workers = max_workers
        self._job_queue = Queue()
        self._threads = set()
        self._thread_name = thread_name
        self._shutdown = False
        self._shutdown_lock = threading.Lock()

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock: 
            if self._shutdown:
                raise RuntimeError('cannot schedule new job after shutdown')
            job = _Job(fn, args, kwargs)
            self._job_queue.put(job)
            self._adjust_thread_count()

    def _adjust_thread_count(self):
        def weakref_cb(_, q=self._job_queue):
            q.put(None)
        if len(self._threads) < self._max_workers:
            t = threading.Thread(target=_worker, 
                                 args=(weakref.ref(self, weakref_cb),
                                       self._job_queue),
                                 name=self._thread_name)
            t.daemon = True
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self._job_queue

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self._job_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()


i = 0
lock = threading.Lock()

if __name__ == '__main__':
    import time

    # Playground
    executor = ThreadPoolExecutor(max_workers=4)
    
    def fn():
        global i
        global lock
        with lock:
            print 'Hello '+str(i)
            i += 1
        time.sleep(5)

    executor.submit(fn)
    executor.submit(fn)
    executor.submit(fn)
    executor.submit(fn)
    executor.submit(fn)
    executor.submit(fn)
    
    executor.shutdown()

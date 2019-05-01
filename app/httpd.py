import argparse
import logging
import os.path

from threading import Thread
from queue import Queue
from socket import AF_INET, SOCK_STREAM, socket
from const import *
from response import Response, CacheContent
from request import Request


class Worker(Thread):
    def __init__(self, queue, dir, cache=None):
        super().__init__()
        self.queue = queue
        self.dir = dir
        self.cache = cache

    def run(self):
        while True:
            try:
                args, kwargs = self.queue.get()
                if len(args) == 1 and isinstance(args[0], type(STOP_TASK)) and args[0] == STOP_TASK:
                    self.queue.task_done()
                    break
                kwargs["dir"] = self.dir
                kwargs["cache"] = self.cache
                process_connection(*args, **kwargs)
                self.queue.task_done()
            except Exception:
                logging.exception("Processing error:")
                pass


class ThreadPool():
    def __init__(self, n, dir, cache=None):
        self.queue = Queue(n * 2)
        for _ in range(n):
            Worker(self.queue, dir, cache).start()

    def add_task(self, *args, **kwargs):
        self.queue.put((args, kwargs))

    def stop(self):
        for _ in range(self.queue.maxsize):
            self.add_task(STOP_TASK)
        self.queue.join()


def process_connection(c, a, dir, cache=None):
    data = read_http_data(c)
    request = Request(data)
    response = Response.get_response(request, dir, cache)
    response_text = response.to_binary()
    c.sendall(response_text)
    c.close()


def read_http_data(c):
    data = ""
    while True:
        r = c.recv(SOCKET_PART_SIZE)
        data += r.decode("utf8")
        if len(r) < 1:
            break
        if r.endswith(HTTP_END):
            break
        if len(data) > MAX_REQUEST_SIZE:
            break
    return data


class Server:
    def __init__(self, n_worker, d_root, port):
        self.n_worker = n_worker
        self.d_root = d_root
        self.port = port
        self.tp = None
        self.socket = None
        self.cache = CacheContent()

    def run(self):
        dir = os.path.dirname((os.path.abspath(os.path.curdir)))
        dir = os.path.join(dir, self.d_root)
        if not os.path.exists(dir):
            raise FileExistsError(f"Path {dir} not found")

        self.tp = ThreadPool(self.n_worker, dir, self.cache)
        s = socket(AF_INET, SOCK_STREAM)

        self.socket = s
        s.bind(("", self.port))
        s.listen(self.n_worker * 2)
        logging.info("Server started")
        while True:
            c, a = s.accept()
            self.tp.add_task(c, a)

    def stop(self):
        if self.tp:
            self.tp.stop()
        if self.socket:
            self.socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--worker", action="store", type=int, default=20)
    parser.add_argument("-r", "--root", action="store", type=str, default="documents")
    parser.add_argument("-l", "--log", action="store", type=str, default=None)
    parser.add_argument("-p", "--port", action="store", type=int, default=8081)
    args = parser.parse_args()

    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')

    server = Server(args.worker, args.root, args.port)

    try:
        server.run()
    except KeyboardInterrupt:
        server.stop()
        logging.exception("Work interrupted:")
    except Exception as e:
        logging.exception("An error occurred:")

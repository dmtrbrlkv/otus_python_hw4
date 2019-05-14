import argparse
import logging
import os.path

from queue import Queue
from socket import AF_INET, SOCK_STREAM, socket
from const import *
from response import Response, CacheContent
from request import Request
from multiprocessing.dummy import Pool as TreadPool


class Worker:
    def __call__(self, socket, dir, cache=None,):
        try:
            self.process_connection(socket, dir, cache)
        except Exception:
            logging.exception("Processing error:")
            pass

    @classmethod
    def process_connection(cls, socket, dir, cache=None):
        data = cls.read_http_data(socket)
        request = Request(data)
        response = Response.get_response(request, dir, cache)
        response_text = response.to_binary()
        socket.sendall(response_text)
        socket.close()

    @classmethod
    def read_http_data(cls, socket):
        data = ""
        while True:
            r = socket.recv(SOCKET_PART_SIZE)
            data += r.decode("utf8")
            if len(r) < 1:
                break
            if HTTP_END in r:
                break
            if len(data) > MAX_REQUEST_SIZE:
                break
        return data


class ThreadPool2():
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


class Server:
    def __init__(self, workers_count, root_directory, port):
        self.workers_count = workers_count
        self.root_directory = root_directory
        self.port = port
        self.tread_pool = None
        self.socket = None
        self.cache = CacheContent()

    def run(self):
        dir = os.path.dirname((os.path.abspath(os.path.curdir)))
        dir = os.path.join(dir, self.root_directory)
        if not os.path.exists(dir):
            raise FileExistsError(f"Path {dir} not found")

        self.tread_pool = TreadPool(self.workers_count)

        s = socket(AF_INET, SOCK_STREAM)

        self.socket = s
        s.bind(("", self.port))
        s.listen(self.workers_count * 2)
        logging.info("Server started")
        while True:
            c, a = s.accept()
            self.tread_pool.starmap_async(Worker(), [(c, dir, self.cache)])

    def stop(self):
        if self.tread_pool:
            self.tread_pool.terminate()
        if self.socket:
            self.socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--worker", action="store", type=int, default=20)
    parser.add_argument("-r", "--root", action="store", type=str, default="documents")
    parser.add_argument("-l", "--log", action="store", type=str, default=None)
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
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

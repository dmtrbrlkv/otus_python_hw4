import argparse
import logging
import os.path

from time import sleep
from socket import AF_INET, SOCK_STREAM, socket
from const import *
from response import Response, CacheContent
from request import Request
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count


class Worker:
    def __call__(self, socket, dir, cache=None,):
        try:
            self.process_connection(socket, dir, cache)
        except Exception:
            logging.exception("Processing error:")
            pass

    def process_connection(self, socket, dir, cache=None):
        data = self.read_http_data(socket)
        if not data:
            socket.close()
            return
        request = Request(data)
        response = Response.get_response(request, dir, cache)
        response_text = response.to_binary()
        socket.sendall(response_text)
        socket.close()

    def read_http_data(self, socket):
        data = b""
        while True:
            r = socket.recv(SOCKET_PART_SIZE)
            data += r
            if len(r) < 1:
                data = None
                break
            if HTTP_END in r:
                break
            if len(data) > MAX_REQUEST_SIZE:
                break

        if data:
            return data.decode("utf8")
        return None


def clear_cache(cache, run_each_minutes=1):
    while True:
        cache.clear()
        sleep(run_each_minutes * 60)


class Server:
    def __init__(self, workers_count, root_directory, port):
        self.workers_count = workers_count
        self.root_directory = root_directory
        self.port = port
        self.thread_pool = None
        self.socket = None
        self.cache = CacheContent()

    def run(self):
        dir = (os.path.abspath(os.path.curdir))
        dir = os.path.join(dir, self.root_directory)
        if not os.path.exists(dir):
            raise FileExistsError(f"Path {dir} not found")

        self.thread_pool = ThreadPool(self.workers_count + 1)
        self.thread_pool.map_async(clear_cache, [self.cache])

        s = socket(AF_INET, SOCK_STREAM)

        self.socket = s
        s.bind(("", self.port))
        s.listen(self.workers_count * 2)
        logging.info("Server started")
        while True:
            c, a = s.accept()
            self.thread_pool.starmap_async(Worker(), [(c, dir, self.cache)])

    def stop(self):
        if self.thread_pool:
            self.thread_pool.terminate()
        if self.socket:
            self.socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--worker", action="store", type=int, default=cpu_count())
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
        logging.info("Work interrupted")
    except Exception as e:
        logging.exception("An error occurred:")

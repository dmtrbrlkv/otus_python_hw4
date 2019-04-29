import argparse
import logging
import os.path
import datetime
from urllib.parse import unquote

from threading import Thread
from queue import Queue

from socket import AF_INET, SOCK_STREAM, socket


from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime


SOCKET_PART_SIZE = 1000
HTTP_END = b"\r\n\r\n"
UNKNOWN = "UNKNOWN"
STOP_TASK = "STOP_TASK"

OK = 200
FORBIDDEN = 403
NOT_FOUND = 404
NOT_ALLOWED = 405
INDEX_PATH = "index.html"
MAX_REQUEST_SIZE = 2000
SERVER_NAME = "SERVER 3000 XXL TURBO"


class Worker(Thread):
    def __init__(self, queue, cache=None):
        super().__init__()
        self.queue = queue
        self.cache = cache

    def run(self):
        while True:
            try:
                args, kwargs = self.queue.get()
                if len(args) == 1 and isinstance(args[0], type(STOP_TASK)) and args[0] == STOP_TASK:
                    self.queue.task_done()
                    print("stop")
                    break
                kwargs["cache"] = self.cache
                process_connection(*args, **kwargs)
            except Exception as e:
                print(e)
            self.queue.task_done()


class ThreadPool():
    def __init__(self, n, cache=None):
        self.queue = Queue(n)
        for _ in range(n):
            Worker(self.queue, cache).start()

    def add_task(self, *args, **kwargs):
        self.queue.put((args, kwargs))
        pass

    def stop(self):
        for _ in range(self.queue.maxsize):
            self.add_task(STOP_TASK)
        self.queue.join()



def process_connection(c, a, dir, cache=None):
    data = read_http_data(c)
    request = HTTPRequest(data)
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


class Content:
    def __init__(self):
        self.content = None
        self.content_ext = None
        self.content_len = None
        self.content_status = None
        self.content_info = None

    def set_content(self, content, ext, len, status, info):
        self.content = content
        self.content_ext = ext
        self.content_len = len
        self.content_status = status
        self.content_info = info


class Response:
    content_types = {
        "jpg":  "image/jpeg",
        "jpeg": "image/jpeg",
        "png":  "image/png",
        "gif":  "image/gif",

        "css":  "text/css",
        "html": "text/html",

        "js":   "application/javascript",
        "swf":  "application/x-shockwave-flash",
    }

    UNKNOWN_CONTENT = "unknown"

    methods = ("GET", "HEAD")



    @classmethod
    def get_response(cls, request, dir, cache):
        response = cls(request.url, request.method, dir, cache)
        response.load_content()
        return response

    def __init__(self, url, method, dir, cache=None):
        url = unquote(url)
        url = url.split("?")[0]
        self.url = url
        self.method = method
        self.dir = dir
        self.content = None
        self.code = 0
        self.cache = cache

    @property
    def headers(self):

        now = datetime.now()
        stamp = mktime(now.timetuple())

        headers = {
            "Date": format_date_time(stamp),
            "Server": SERVER_NAME,
            "Connection": "close"
        }

        content_length = self.get_content_length()
        if content_length:
            headers["Content-Length"] = content_length

        content_type = self.get_content_type()
        if content_type:
            headers["Content-Type"] = content_type

        return headers

    def get_content_path(self):
        if len(self.url) > 0:
            path = os.path.join(self.dir, self.url[1:])
        else:
            path = self.dir
        if os.path.isdir(path):
            path = os.path.join(path, INDEX_PATH)
        if os.path.exists(path):
            return path
        else:
            return None

    def load_content(self):
        if self.method not in self.methods:
            self.content = Content()
            self.content.set_content(None,  None, None, NOT_ALLOWED, f"Method {self.method} not allowed")
            return

        path = self.get_content_path()
        if path:
            if self.cache:
                content = self.cache.get(path)
                if content:
                    self.content = content
                    return
            try:
                with open(path, mode="rb") as f:
                    if self.method == "GET":
                        content = f.read()
                        self.content = Content()
                        self.content.set_content(content, path.split(".")[-1], os.path.getsize(path), OK, "OK")
                        if self.cache:
                            self.cache.add(path, self.content)
                    else:
                        self.content = Content()
                        self.content.set_content(None, path.split(".")[-1], os.path.getsize(path), OK, "OK")

            except Exception as e:
                self.content = Content()
                self.content.set_content(None, None, None, FORBIDDEN,
                                         f"Forbidden – you don’t have permission to access {self.url}")
        else:
            self.content = Content()
            self.content.set_content(None, None, None, NOT_FOUND,
                                     f"{self.url} not found")

    def get_content_length(self):
        if self.content.content_len is None:
            return 0
        else:
            return self.content.content_len

    def get_content_type(self):
        if self.content.content_ext and self.content.content_ext in self.content_types:
            return self.content_types[self.content.content_ext]
        return self.UNKNOWN_CONTENT

    def get_code(self):
        return self.content.content_status, self.content.content_info

    def to_binary(self):
        code, info = self.get_code()

        text = []
        text.append(f"HTTP/1.1 {str(code)} {info}")
        for k, v in self.headers.items():
            text.append((k + ": " + str(v)))
        if self.content.content:
            text.append(b"\n" + self.content.content)

        text = [t.encode("utf-8") if isinstance(t, str) else t for t in text]

        return b"\n".join(text)

class HTTPRequest():
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.parsed = False
        self._url = ""
        self._method = ""


    def parse_data(self):
        splited_data = self.raw_data.split()
        if len(splited_data) < 2:
            method = UNKNOWN
            url = UNKNOWN
        else:
            method = splited_data[0]
            url = splited_data[1]

        self.method = method
        self.url = url

        self.parsed = True

    @property
    def url(self):
        if not self.parsed:
            self.parse_data()
            
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def method(self):
        if not self.parsed:
            self.parse_data()

        return self._method

    @method.setter
    def method(self, value):
        self._method = value



class Server:
    def __init__(self, n_worker, d_root, port=80):
        self.n_worker = n_worker
        self.d_root = d_root
        self.port = port
        self.tp = None
        self.socket = None
        self.cache = CacheContent()

    def run(self):
        # for i in range(self.n_worker):
        #     self.worker_pool.append(self.create_worker())
        #
        # for worker in self.worker_pool:
        #     worker.start()

        dir = os.path.dirname((os.path.abspath(os.path.curdir)))
        dir = os.path.join(dir, self.d_root)
        if not os.path.exists(dir):
            raise FileExistsError(f"Path {dir} not found")

        self.tp = ThreadPool(self.n_worker, self.cache)
        s = socket(AF_INET, SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except:
            pass
        self.socket = s
        s.bind(("", self.port))
        s.listen(self.n_worker)
        while True:
            c, a = s.accept()
            print("Received connection from", a)
            self.tp.add_task(c, a, dir)

    def close(self):
        if self.tp:
            self.tp.stop()
        if self.socket:
            self.socket.close()


class CacheContent:
    def __init__(self):
        self.cache = {}

    def add(self, key, content):
        self.cache[key] = content

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        return None





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--worker", action="store", type=int, default=10)
    parser.add_argument("-r", "--root", action="store", type=str, default="documents")
    parser.add_argument("-l", "--log", action="store", type=str, default=None)
    args = parser.parse_args()

    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')

    server = Server(args.worker, args.root)

    try:
        server.run()
    except KeyboardInterrupt:
        server.close()




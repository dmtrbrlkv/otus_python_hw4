from urllib.parse import unquote
import datetime
import os
from time import mktime
from wsgiref.handlers import format_date_time
from const import *


class CacheContent:
    def __init__(self):
        self.cache = {}

    def add(self, key, content):
        self.cache[key] = content

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        return None


class Content:
    def __init__(self, content, ext, len, status, info):
        self.content = content
        self.content_ext = ext
        self.content_len = len
        self.content_status = status
        self.content_info = info

    def set_content(self, content, ext, len, status, info):
        self.content = content
        self.content_ext = ext
        self.content_len = len
        self.content_status = status
        self.content_info = info

    @classmethod
    def not_allowed(cls, method):
        obj = cls(None, None, None, NOT_ALLOWED, f"Method {method} not allowed")
        return obj

    @classmethod
    def forbidden(cls, url):
        obj = cls(None, None, None, FORBIDDEN, f"Forbidden – you don’t have permission to access {url}")
        return obj

    @classmethod
    def not_found(cls, url):
        obj = cls(None, None, None, NOT_FOUND, f"{url} not found")
        return obj

    @classmethod
    def ok(cls, content, path):
        obj = cls(content, path.split(".")[-1], os.path.getsize(path), OK, "OK")
        return obj


class Response:
    content_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",

        "css": "text/css",
        "html": "text/html",

        "js": "application/javascript",
        "swf": "application/x-shockwave-flash",
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

        now = datetime.datetime.now()
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
        path = os.path.normpath(path)
        if self.dir not in path:
            return None
        if os.path.isdir(path):
            path = os.path.join(path, INDEX_PATH)
        if not os.path.exists(path):
            return None
        return path

    def load_content(self):
        path = self.get_content_path()
        if path:
            self.content = self.get_content_by_path(path)
        else:
            self.content = self.not_found_processor()

    def get_processor(self, path):
        if self.cache:
            content = self.cache.get(path)
            if content:
                return content

        with open(path, mode="rb") as f:
            content = Content.ok(f.read(), path)
            if self.cache:
                self.cache.add(path, content)
            return content

    def head_processor(self, path):
        content = Content.ok(None, path)
        return content

    def not_allowed_processor(self):
        return Content.not_allowed(self.method)

    def not_found_processor(self):
        return Content.not_found(self.url)

    def get_content_by_path(self, path):
        try:
            if self.method == "GET":
                return self.get_processor(path)
            if self.method == "HEAD":
                return self.head_processor(path)
            return self.not_allowed_processor()

        except Exception:
            return Content.forbidden(self.url)

    def get_content_length(self):
        return self.content.content_len or 0

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
            text.append(HTTP_STR_END + self.content.content)

        text = [t.encode("utf-8") if isinstance(t, str) else t for t in text]

        return HTTP_STR_END.join(text) + HTTP_END

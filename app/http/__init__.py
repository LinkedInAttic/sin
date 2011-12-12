import os

from django.template import Context, loader
from django.http import HttpResponse

class HttpResponsePostRedirect(HttpResponse):
    def __init__(self, redirect_to, paras=None, mimetype=None, charset=None):
        context = Context({
            'redirect_to': redirect_to,
        })
        extra_context = {
            'paras': paras,
        }
        context.update(extra_context)
        t = loader.get_template('http/post_redirect.html')
        HttpResponse.__init__(self, t.render(context), mimetype, charset)

class HttpResponseFile(HttpResponse):
    def __init__(self, path, mimetype, offset=0, length=-1):
        HttpResponse.__init__(self, '', mimetype)
        try:
            file_size = os.path.getsize(path)
            if offset < 0 or offset >= file_size:
                self.status_code = 416
            if length < 0 or file_size-offset < length:
                length = file_size - offset
        finally:
            if self.status_code != 416 and length > 0:
                self['Content-Length'] = str(length)
                if length < file_size:
                    self['Content-Range'] = 'bytes %d-%d/%d' % (offset, offset + length - 1, file_size)
                    self.status_code = 206

        self.path = path
        self.offset = offset
        self.length = length
        if self.length >= 0:
            self.end = self.offset + self.length
        else:
            self.end = -1
        self.filelike = None
        self.blksize = 65536

    def __iter__(self):
        return self

    def next(self):
        if not self.filelike:
            self.filelike = file(self.path)
            self.filelike.seek(self.offset)

        size = self.end - self.filelike.tell()
        if size > self.blksize:
            size = self.blksize
        data = None
        if size > 0:
            data = self.filelike.read(size)
        if data:
            return data

        raise StopIteration

    def close(self):
        if self.filelike:
            self.filelike.close()


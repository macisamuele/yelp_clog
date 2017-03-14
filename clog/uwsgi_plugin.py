import uwsgi
import uwsgidecorators
import logging
import clog
import clog.global_state
import clog.handlers
import six.moves.cPickle as pickle


def _mule_msg(*args, **kwargs):
    mule = kwargs.pop('mule', 1)
    data = pickle.dumps({
        'service': 'uwsgi_mulefunc',
        'func': 'log_line',
        'args': args,
        'kwargs': kwargs,
    })
    uwsgi.mule_msg(data, mule)


class UwsgiHandler(logging.Handler):

    def __init__(self, stream, mule=1):
        logging.Handler.__init__(self)
        self.stream = stream
        self.mule = mule

    def emit(self, record):
        try:
            msg = self.format(record)
            _mule_msg(self.stream, msg, mule=self.mule)
        except Exception:
            raise
        except:
            self.handleError(record)


# TODO: Patch upstream uwsgi to return success on the pipe write so
# we can optionally default to sync log_line
def uwsgi_log_line(stream, line, mule=1):
    _mule_msg(stream, line, mule=mule)


def uwsgi_patch_global_state():
    map(
        lambda x: setattr(x, 'log_line', uwsgi_log_line),
        (clog, clog.global_state)
    )


# Couple setup tasks at import:
# 1. Register 'log_line' in all mules for dispatch handling on the mule side
# 2. Insert 'UwsgiHandler' into the clog.handlers module for seamless usage

uwsgidecorators.mule_functions['log_line'] = clog.global_state.log_line
setattr(clog.handlers, 'UwsgiHandler', UwsgiHandler)

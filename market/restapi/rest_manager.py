import json
import logging
from traceback import format_tb

from twisted.internet import reactor
from twisted.internet.defer import maybeDeferred
from twisted.python.compat import intToBytes
from twisted.web import server, http
from market.restapi.root_endpoint import RootEndpoint



class RESTManager(object):
    """
    This class is responsible for managing the startup and closing of the HTTP API.
    """

    def __init__(self, community, port):
        super(RESTManager, self).__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.community = community
        self.port = port
        self.site = None
        self.root_endpoint = None

    def start(self):
        """
        Starts the HTTP API with the listen port as specified in the session configuration.
        """
        self.root_endpoint = RootEndpoint(self.community)
        site = server.Site(resource=self.root_endpoint)
        site.requestFactory = RESTRequest
        self.site = reactor.listenTCP(self.port, site, interface="127.0.0.1")
        return self.site

    def stop(self):
        """
        Stop the HTTP API and return a deferred that fires when the server has shut down.
        """
        return maybeDeferred(self.site.stopListening)


class RESTRequest(server.Request):
    """
    This class gracefully takes care of unhandled exceptions raised during the processing of any request.
    """
    defaultContentType = b"text/json"

    def __init__(self, *args, **kw):
        server.Request.__init__(self, *args, **kw)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.setHeader('Access-Control-Allow-Origin', '*')

    def processingFailed(self, failure):
        self._logger.exception(failure)
        response = {
            u"error": {
                u"handled": False,
                u"code": failure.value.__class__.__name__,
                u"message": failure.value.message
            }
        }
        if self.site.displayTracebacks:
            response[u"error"][u"trace"] = format_tb(failure.getTracebackObject())

        body = json.dumps(response)
        self.setResponseCode(http.INTERNAL_SERVER_ERROR)
        self.setHeader(b'content-type', self.defaultContentType)
        self.setHeader(b'content-length', intToBytes(len(body)))
        self.write(body)
        self.finish()
        return failure

# coding: utf-8
"""
STOMPプロトコルのためのクライアントインタフェース。
Stomperモジュールを一部改変して利用しています。

 * http://code.google.com/p/stomper/

STOMPプロトコルについては以下を参照してください。

 * http://stomp.codehaus.org/Protocol

使い方

送信
>>> s = Stomper()
>>> s.connect(host="localhost", port=61613, user="", password="")
>>> s.send("/queue/my.test", "message body", True)
>>> s.send_as_json("/queue/my.test", [1, 2, 3], True)
>>> s.disconnect()

受信
>>> s = Stomper()
>>> s.connect(host="localhost", port=61613, user="", password="", timeout=10)
>>> s.subscribe("/queue/my.test")
>>> while True:
>>>    frame = s.receive()
>>>    if frame is None:
>>>        break
>>>    print frame.body
>>> s.disconnect()
"""
import logging
import socket
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import uuid
try:
    import simplejson
except ImportError:
    try:
        from django.utils import simplejson
    except ImportError:
        simplejson = None
log = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)

STOMP_VERSION = "1.0"

NULL = "\x00"

VALID_COMMANDS = [
    "ABORT", "ACK", "BEGIN", "COMMIT", 
    "CONNECT", "CONNECTED", "DISCONNECT", "MESSAGE",
    "SEND", "SUBSCRIBE", "UNSUBSCRIBE",
    "RECEIPT", "ERROR",    
]


class FrameError(Exception):
    pass


class Frame(object):
    
    def __init__(self, cmd="", headers={}, body=""):
        self.cmd = cmd
        self.body = body
        self.headers = headers
    
    def get_cmd(self):
        return self._cmd
        
    def set_cmd(self, cmd):
        cmd = cmd.upper()
        if cmd not in VALID_COMMANDS:
            raise FrameError("The cmd '%s' is not valid! It must be one of '%s' (STOMP v%s)." % (
                cmd, VALID_COMMANDS, STOMP_VERSION)
            )
        else:
            self._cmd = cmd
    
    cmd = property(get_cmd, set_cmd)
    
    def add_header(self, name, value):
        headers[name] = value
    
    def get_body(self):
        return self._body
        
    def set_body(self, body):
        self._body = body
    
    body = property(get_body, set_body)
    
    def pack(self):
        headers = [ "%s:%s" % (f, v) for f, v in self.headers.items() ]
        headers = "\n".join(headers)
        stomp_mesage = "%s\n%s\n\n%s%s\n" % (self._cmd, headers, self._body, NULL)
        return stomp_mesage
        
    def __call__(self):
        return self.pack()
    
    @classmethod
    def unpack(cls, message):
        if not message:
            raise FrameError("Unpack error! The given message isn't valid '%s'!" % message)
            
        msg = cls.unpack_frame(message)
        return Frame(msg["cmd"], msg["headers"], msg["body"])
    
    @classmethod
    def unpack_frame(cls, message):
        body = []
        returned = dict(cmd="", headers={}, body="")
        
        breakdown = message.split("\n")
        returned["cmd"] = breakdown[0]
        breakdown = breakdown[1:]
    
        def headD(field):
            index = field.find(":")
            if index:
                header = field[:index].strip()
                data = field[index+1:].strip()
                returned["headers"][header.strip()] = data.strip()
    
        def bodyD(field):
            field = field.strip()
            if field:
                body.append(field)
    
        # Recover the header fields and body data
        handler = headD
        for field in breakdown:
            if field.strip() == "":
                # End of headers, it body data next.
                handler = bodyD
                continue
    
            handler(field)
    
        body = "".join(body)
        returned["body"] = body.replace("\x00", "")
        return returned
        
    @classmethod
    def abort(cls, transactionid):
        """STOMP abort transaction command.
    
        Rollback whatever actions in this transaction.
            
        transactionid:
            This is the id that all actions in this transaction.
        
        """
        return cls("ABORT", {"transaction":transactionid})
    
    @classmethod
    def ack(cls, messageid, transactionid=None):
        """STOMP acknowledge command.
        
        Acknowledge receipt of a specific message from the server.
    
        messageid:
            This is the id of the message we are acknowledging,
            what else could it be? ;)
        
        transactionid:
            This is the id that all actions in this transaction 
            will have. If this is not given then a random UUID
            will be generated for this.
        
        """
        headers = {"message-id":messageid}
        if transactionid:
            headers["transaction"] = transactionid
        return cls("ACK", headers)
        
    @classmethod
    def begin(cls, transactionid=None):
        """STOMP begin command.
    
        Start a transaction...
        
        transactionid:
            This is the id that all actions in this transaction 
            will have. If this is not given then a random UUID
            will be generated for this.
        
        """
        headers = {"transaction":transactionid or uuid.uuid4()}
        return cls("BEGIN", headers)
        
    @classmethod
    def commit(cls, transactionid):
        """STOMP commit command.
    
        Do whatever is required to make the series of actions
        permenant for this transactionid.
            
        transactionid:
            This is the id that all actions in this transaction.
        
        """
        headers = {"transaction":transactionid}
        return cls("COMMIT", headers)
    
    @classmethod
    def connect(cls, username, password):
        """STOMP connect command.
        
        username, password:
            These are the needed auth details to connect to the 
            message server.
        
        After sending this we will receive a CONNECTED
        message which will contain our session id.
        
        """
        headers = {"login":username, "passcode":password}
        return cls("CONNECT", headers)
    
    @classmethod
    def disconnect(cls):
        """STOMP disconnect command.
        
        Tell the server we finished and we"ll be closing the
        socket soon.
        
        """
        return cls("DISCONNECT")
        
    @classmethod
    def send(cls, dest, msg, persistent=False, transactionid=None):
        """STOMP send command.
        
        dest:
            This is the channel we wish to subscribe to
        
        msg:
            This is the message body to be sent.
            
        transactionid:
            This is an optional field and is not needed
            by default.
        
        """
        headers = {"destination":dest}
        if persistent:
            headers["persistent"] = "true"
        if transactionid:
            headers["transaction"] = transactionid
        return cls("SEND", headers, msg)
        
    @classmethod
    def subscribe(cls, dest, ack="auto"):
        """STOMP subscribe command.
        
        dest:
            This is the channel we wish to subscribe to
        
        ack: "auto" | "client"
            If the ack is set to client, then messages received will
            have to have an acknowledge as a reply. Otherwise the server
            will assume delivery failure.
        
        """
        headers = {"destination":dest, "ack":ack}
        return cls("SUBSCRIBE", headers)
    
    @classmethod
    def unsubscribe(cls, dest):
        """STOMP unsubscribe command.
        
        dest:
            This is the channel we wish to subscribe to
        
        Tell the server we no longer wish to receive any
        further messages for the given subscription.
        
        """
        headers = {"destination":dest}
        return cls("UNSUBSCRIBE", headers)


class Stomper(object):
    """
    The object oriented interface for STOMP protocol.
    """

    def __init__(self):
        self.sock = None
        self.tid = None
        self.recvbuf = ""

    def _recv(self):
        if NULL not in self.recvbuf: 
            buf = StringIO()
            while True:
                c = self.sock.recv(1024)
                buf.write(c)
                if NULL in c:
                    self.recvbuf += buf.getvalue()
                    break
        endpos = self.recvbuf.find(NULL)
        fbytes = self.recvbuf[:endpos+1]
        self.recvbuf = self.recvbuf[endpos+2:]
        frame = Frame.unpack(fbytes)
        log.debug("cmd:%s, headers:%s, body:%s", 
                  frame.cmd, frame.headers, frame.body)
        return frame

    def connect(self, host="127.0.0.1", port=61613, user="", password="", 
            timeout=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((host, port))
        self.sock.sendall(Frame.connect(user, password)())
        return self._recv()

    def begin(self):
        self.tid = uuid.uuid4()
        self.sock.sendall(Frame.begin(self.tid)())

    def commit(self):
        self.sock.sendall(Frame.commit(self.tid)())
        self.tid = None

    def abort(self):
        self.sock.sendall(Frame.abort(self.tid)())
        self.tid = None

    def send(self, dest, body, persistent=True):
        msg = Frame.send(dest, body, persistent, self.tid)()
        log.debug(msg)
        self.sock.sendall(msg)

    def send_as_json(self, dest, body_dict, persistent=True):
        if not simplejson:
            raise NotImplementedError()
        body = simplejson.dumps(body_dict)
        msg = Frame.send(dest, body, persistent)()
        self.sock.sendall(msg)

    def subscribe(self, dest):
        self.sock.sendall(Frame.subscribe(dest)())

    def receive(self):
        try:
            return self._recv()
        except socket.timeout:
            return None

    def receive_as_json(self):
        if not simplejson:
            raise NotImplementedError()
        try:
            frame = self._recv()
        except socket.timeout:
            return None, None
        try:
            json_obj = simplejson.loads(frame.body)
        except Exception, e:
            log.debug(e)
            json_obj = None
        return frame, json_obj

    def unsubscribe(self, dest):
        sock.sendall(Frame.unsubscribe(dest)())

    def disconnect(self):
        self.sock.sendall(Frame.disconnect()())
        self.sock.close()
        self.__init__()
        

if __name__ == "__main__":
    import sys, time
    if sys.argv[1] == "send":
        s = Stomper()
        s.connect()
        for i in xrange(1000):
            s.send_as_json("/queue/my.test", [i, i+1, i+2], True)
            time.sleep(0.1)
        s.disconnect()
    else:
        s = Stomper()
        s.connect(timeout=10)
        s.subscribe("/queue/my.test")
        while True:
            f, json_obj = s.receive_as_json()
            if not f:
                break
            print json_obj
        s.disconnect()
                
__import__('pkg_resources').declare_namespace(__name__)
import os
import jinja2
import jinja2.meta
import logging
import requests
import fcntl
import time
import re
import json
# E-Mail tools.
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# URL parsing module
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


def notify_mail(subject, payload, recipients=[], cc=[], sender="", server="127.0.0.1", port=25):
    """Send a mail.
    """
    logger = logging.getLogger("soc.apiclient.remedy.notify_mail")
    # Builds mail.
    logger.info("setting-up mail context (subject='{subject}', sender='{sender}', recipients='{recipients}', cc='{cc}')".format(
        subject=subject,
        sender=sender,
        recipients=recipients,
        cc=cc
    ))
    email = MIMEMultipart()
    email["Subject"] = subject
    email["from"] = sender
    email["To"] = ", ".join(recipients)
    email["CC"] = ", ".join(cc)
    # Mail content.
    logger.info("setting-up mail payload (type='html')")
    email.attach(MIMEText(payload, "html"))
    # Sending mail.
    if len(recipients) > 0:
        logger.info("setting-up smtp client (host='{server}', port='{port}')".format(server=server, port=port))
        smtp_client = smtplib.SMTP(host=server, port=port)
        logger.info("sending mail")
        errors = smtp_client.sendmail(sender, recipients + cc, email.as_string())
        if len(errors) > 0:
            logger.error("error while sending mail: {errs}".format(errs=", ".join(errors)))
        else:
            logger.info("mail sent")
            logger.debug(payload)
        smtp_client.quit()
    else:
        logger.warning("mail not sent: no recipients")


class EndpointError(Exception):
    """Generic Endpoint error.
    """
    def __init__(self, url, method, message, soap_action=None, soap_payload=None):
        super(EndpointError, self).__init__("Cannot perform '{method}' request to '{url}': {message}".format(method=method, url=url, message=message))
        self.soap_action = soap_action
        self.soap_payload = soap_payload


class Endpoint:
    """Handles a single Remedy endpoint.
    """
    def __init__(self, url, action):
        """Initializes the Request instance.

        Arguments:
            url (str): Remedy API endpoint URL.
            action (str): SOAPAction header.
        """
        self.logger = logging.getLogger("soc.apiclient.remedy.Endpoint")
        self.session = requests.Session()
        try:
            self.url = urlparse(url)
        except Exception as error:
            raise Exception("invalid URL '{url}': {err}".format(url=url, err=str(error)))
        self.action = action
        self.logger.warning("disabling requests and urllib3 SSL warnings")
        requests.packages.urllib3.disable_warnings()

    def __post(self, payload, headers={}):
        """Post the specified `payload` with the provided `headers`.

        Arguments:
            payload (bytes): Rrequest's payload.
            headers (dict): Request's headers.
        """
        try:
            self.logger.info("query: POST, url: {url}, headers: {headers}".format(url=self.url.geturl(), headers=headers))
            self.logger.warning("requests SSL certification is disabled")
            return self.session.post(url=self.url.geturl(), data=payload, headers=headers, verify=False)
        except Exception as error:
            raise EndpointError(self.url.geturl(), "POST", str(error), soap_action=None, soap_payload=payload)

    def post_xml(self, template, variables={}):
        """Post the provided XML `template` (may be a Jinja2 template).

        Arguments:
            template (str): XML payload's template.
            variables (dict, optional): XML payload's variables.
        """
        # Validate that all variables used in templates are defined.
        self.logger.debug("validating template")
        env = jinja2.Environment()
        ast = env.parse(template)
        missing = [v for v in jinja2.meta.find_undeclared_variables(ast) if v not in variables]
        if len(missing) > 0:
            raise EndpointError(self.url.geturl(), "POST", "missing variables {vars}".format(vars=", ".join(missing)))
        # Render template.
        self.logger.debug("rendering template")
        tpl = jinja2.Template(template)
        payload = tpl.render(**variables)
        #print(payload)
        # Posts payload.
        response = self.__post(payload, {"Content-Type": "text/xml", "SOAPAction": "\"{action}\"".format(action=self.action)})
        if response.status_code != 200:
            self.logger.debug("raw response: {response}".format(response=response.text))
            raise EndpointError(self.url.geturl(), "POST", "request response error: {code} ({reason})".format(code=response.status_code, reason=response.reason), soap_action=self.action, soap_payload=payload)
        else:
            self.logger.info("request successful: {code} ({reason})".format(code=response.status_code, reason=response.reason))
            self.logger.debug("raw response: {response}".format(response=response.text))
            return response.text


class KVStore:
    """Simple JSON Key / Value store.
    """
    def __init__(self, path):
        """Initialize the KV store.
        """
        self.logger = logging.getLogger("soc.apiclient.remedy.KVStore")
        self.directory = os.path.abspath(os.path.dirname(path))
        self.filename = os.path.abspath(path)
        # Create storage directory if necessary.
        if not os.path.isdir(self.directory):
            self.logger.info("creating KVStore directory at {directory}".format(directory=self.directory))
            os.makedirs(self.directory)
        # Load existing KVStore file.
        with open(self.filename, mode="a+") as fd:
            self._lock(fd)
            self.logger.info("loading KVStore from {filename}".format(filename=self.filename))
            try:
                self.kvs = json.load(fd)
            except Exception:
                self.logger.info("cannot load KVStore from {filename}, creating a new one".format(filename=self.filename))
                self.kvs = {}
            finally:
                self._unlock(fd)

    def _lock(self, fd):
        while True:
            try:
                self.logger.info("acquiring lock")
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except IOError as error:
                if error.errno != errno.EAGAIN:
                    self.logger.error("cannot lock KVStore (timeout): {reason}".format(reason=str(error)))
                    raise error
                else:
                    self.logger.info("cannot lock KVStore, retrying...")
                    time.sleep(1)

    def _unlock(self, fd):
        self.logger.info("releasing lock")
        fcntl.flock(fd, fcntl.LOCK_UN)

    def save(self):
        """Save KVStore.
        """
        self.logger.info("saving KVStore")
        with open(self.filename, "w+") as fd:
            self._lock(fd)
            try:
                json.dump(self.kvs, fd)
            except Exception:
                raise
            finally:
                self._unlock(fd)

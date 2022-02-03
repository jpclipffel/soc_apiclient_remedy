import sys
import argparse
import logging
import json
import re
from pkg_resources import resource_filename as pkgrs
from . import Endpoint, EndpointError, KVStore, notify_mail


# Defaults configuration.
defaults = {}


def load_defaults(path, name):
    """Load the defaults values from a given profile `name` extracted from `path`.

    Arguments:
        path (str): Profiles JSON file path.
        name (str): Profile name.
    """
    try:
        fd = open(path, 'r')
        profiles = json.load(fd)
        if name in profiles and isinstance(profiles[name], dict):
            for field in ["url", "action", "template", "casedb"]:
                if field in profiles[name]:
                    defaults[field] = profiles[name][field]
        else:
            raise Exception("profile '{name}' doesn't defined in profiles file '{path}'".format(name=name, path=path))
    except Exception as error:
        raise Exception("cannot load defaults: {err}".format(err=str(error)))


def interpret_args(args):
    """Interprets arguments which are function pointer.

    Arguments:
        args (list of arguments): Arguments list.

    Returns:
        list: Interpreted arguments.
    """
    for name in ["url", "action", "casedb"]:
        if isinstance(getattr(args, name, None), tuple):
            function = getattr(args, name)[0]
            arguments = getattr(args, name)[1]
            setattr(args, name, function(*arguments))
    return args


def parse_vars(vars):
    """Parse the user-provided list of templates variables.

    Format MUST be 'key:value' (quotes are optional).

    Arguments:
        vars (list of str): Template variables list.
    """
    variables = {}
    for kv in vars:
        try:
            splitted = kv.split(':')
            k = splitted[0]
            v = "".join(splitted[1:])
            # k, v = kv.split(':')
            if k is not None and len(k) > 0 and v is not None and len(v) > 0:
                variables[k] = v
            else:
                raise Exception
        except Exception:
            print("invalid variable '{kv}': format is key:value".format(kv=kv))
            sys.exit(1)
    return variables


def command_create(args):
    """Create a ticket.
    """
    logger = logging.getLogger("soc.apiclient.remedy.command_create")
    args = interpret_args(args)
    variables = parse_vars(args.vars)
    casedb = KVStore(args.casedb)
    # Check if the case already exists.
    if args.casevar in variables and variables[args.casevar] in casedb.kvs:
        logger.warning("case {caseid} already escalated".format(caseid=variables[args.casevar]))
        return
    # Load template source.
    with open(args.template, 'r') as fd:
        template = fd.read()
    # Create endpoint and execute request.
    try:
        endpoint = Endpoint(args.url, args.action)
        response = endpoint.post_xml(template, variables)
        # Exract ticket ID from reponse.
        rsx = re.findall("Incident_Number>([^<]*)<", response)
        ticket_id = len(rsx) > 0 and rsx[0] or None
        if ticket_id is None:
            raise Exception("cannot extract ticket_id from response")
        # Add case in case db.
        casedb.kvs[variables[args.casevar]] = {"ticket_id": ticket_id}
        casedb.save()
    except Exception as error:
        logger.exception(error)
        # Advanced error debug.
        if isinstance(error, EndpointError):
            adv_err = """
<h3>SOAP action</h3>
<p>{soap_action}</p>
<br>
<h3>SOAP Payload</h3>
<pre>
    {soap_payload}
</pre>
""".format(soap_action=error.soap_action, soap_payload=error.soap_payload)
        else:
            adv_err = ""
        # Error mail data.
        payload = """
<html>
    <body>
        <h1 style="color:Tomato;">soc.apiclient.qualys error</h1>
        <p>{err}</p>
        <br>
        {adv_err}
    </body>
</html>
"""
        notify_mail(subject="soc.apiclient.remedy error",
                    payload=payload.format(err=str(error), adv_err=adv_err),
                    recipients=["soc@excellium-services.com", "jpclipffel@excellium-services.com", "rdion@excellium-services.com"])


def command_list(args):
    """List existing tickets.
    """
    logger = logging.getLogger("soc.apiclient.remedy.command_list")
    args = interpret_args(args)
    casedb = KVStore(args.casedb)
    print(json.dumps(casedb.kvs, indent=2))


def command_close(args):
    """Close a given case.
    """
    logger = logging.getLogger("soc.apiclient.remedy.command_close")
    args = interpret_args(args)
    casedb = KVStore(args.casedb)
    closed = 0
    for case in args.cases:
        try:
            casedb.kvs.pop(case)
            closed += 1
        except Exception:
            logger.warning("case {case} not present in local case database, ignoring".format(case=case))
    casedb.save()
    logger.info("{count} cases closed".format(count=closed))


def main():
    # Arguments parser.
    parser = argparse.ArgumentParser(description="SOC client API for Remedy")
    # Globals arguments.
    parser.add_argument("--profiles", type=str, default=pkgrs(__name__, "static/profiles.json"), help="Profiles' JSON file path")
    parser.add_argument("--profile",  type=str, default="qualification",                         help="Profile's name")
    parser.add_argument("--casedb",   type=str, default=(defaults.get, ("casedb", )),            help="Local cases DB")
    # Commands sub-parsers.
    sp = parser.add_subparsers(dest="command", help="Command")
    sp.required = True
    # 'create' command.
    p_create = sp.add_parser("create", help="Create a new ticket for the given case.")
    p_create.set_defaults(func=command_create)
    p_create.add_argument("--url",      type=str, default=(defaults.get, ("url", )),    help="Web service URL")
    p_create.add_argument("--action",   type=str, default=(defaults.get, ("action", )), help="SOAP action header")
    p_create.add_argument("--casevar",  type=str, default="case_name",                  help="Case's variable name in --vars")
    p_create.add_argument("--template", type=str, required=True,                        help="XML or template payload")
    p_create.add_argument("--vars",     type=str, default=[], nargs='+',                help="XML's template variable")
    # 'list' command.
    p_list = sp.add_parser("list", help="List the existing cases and their related tickets.")
    p_list.set_defaults(func=command_list)
    # 'close' command.
    p_close = sp.add_parser("close", help="Close the ticket associated to the given case.")
    p_close.set_defaults(func=command_close)
    p_close.add_argument("cases", type=str, default=[], nargs='+', help="Cases identifier")
    # Parse arguments.
    args = parser.parse_args()
    # Logging.
    logger = logging.getLogger("soc.apiclient.remedy")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    # Set log format on all handlers.
    logformatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    for handler in logger.handlers:
        handler.setFormatter(logformatter)
    # Load defaults from profile.
    load_defaults(args.profiles, args.profile)
    # Execution.
    try:
        args.func(args)
    except EndpointError as error:
        print("Endpoint error: {err}".format(err=str(error)))
        sys.exit(1)
    except Exception as error:
        print("Error: {err}".format(err=str(error)))
        raise


if __name__ == "__main__":
    main()

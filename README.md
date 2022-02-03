# SOC / API Client / Remedy

`soc_apiclient_remedy` is a Python package (2.6+ and 3+) designed to interact
with a Remedy ticketing server.

## Installation

It is **highly recommended** to install the tool within a virtual environment.
If the target system doesn't provides such a tool, nor a way to download
and install the required Python packages, please referer to the sub-section
*Recalcitrant target system*.

### By default (Python 2.7+, 3+ with PIP and Internet access)

* Create a virtual environment: `python -m virtualenv <path/to/your/venv>`
* Install the package: run `python setup.py install`

### Recalcitrant target system (no PIP, not Internet access)

* Go to the `standalone` directory
* Automagically install Python dependencies: run `install.sh <path/to/your/venv>`
* Go back to the projet root directory
* Install the package: run `python setup.py install`

### Configuration

One installed, it's **highly recommended** to **not** use the tool's default
profiles files and templates. One **should** create a local copy and customize
the following files:

* `<tool path>/soc/apiclient/remedy/static/profiles.json`
* `<tool path>/templates/<whatever file needed>.xml`

## Update

If you whish to update the tool, take care to the following points:

* Do not erase the default profiles and templates (which resides under the
  `static` and `templates` directories).
* Check if the new version of the `profile` file include new variables. If so,
  add those variables in the local profile.

## CLI usage

```raw
soc.apiclient.remedy [--profiles <path/to/json>]
                     [--profile <name>]
                     [--casedb <path/to/casedb>]
                     <command> [command arguments]
```

Arguments:

* `--profiles`: Path to profiles definition (JSON file). Defaults to the tool's
  package base profile.
* `--profile`: Profile name within the profile file.
* `--casedb`: Path to the local cases database (will be created if necessary).
  Default's to the profile `casedb` variable.

> **Virtual environment notes**  
>
> * While **IN** a virtual environment, run: `soc.apiclient.remedy <command> [arguments...]`
> * While **NOT IN** a virtual environment, run: `{path/to/your/venv}/bin/soc.apiclient.remedy <command> [arguments...]`

### `create` command

This command creates a new ticket on the Remedy host.

```raw
... create [--url <remedy hostname>]
           [--action <SOAPAction>]
           <--template <ticket XML file>>
           [--vars <key:value ...>]

```

Arguments:

* `--url` (*Optional if using a profile*): The Remedy server URL.
* `--action` (*Optional if using a profile*): SOAPAction API endpoint.
* `--template`: The ticket XML file, which may be a *Jinja2* template.  
* `--vars`: A list of `key:value` pairs, which are the XML template variables.

> **Important note**  
> If a *Jinja* template file is provided through `--template`, **all** variables used in the template **must** be set through the `--vars` argument.

### `close` command

This command removes the case from the internal list of escalated cases.

```raw
... close <case_id> [ case_id_2 case_id_3 ...]
```

Arguments:

* `case_id`: One or more cases ID (such as `SOC-CAC-SIEM-12345`).

### `list` command

This command dumps the internal list of escalated cases.

```raw
... list
```

## API usage

Import the `soc.apiclient.remedy` module, which provides the following classes:

* `Endpoint`: A Remedy endpoint;
* `EndpointError`: A generic `Endpoint` error.
* `KVStore`: A simple key-value store helper class.

## How to connect to Remedy (Web & API)

Schema:

```raw
[Your host] <-- TCP:1443 --> [Horizon] <-- TCP:1443 --> [MON113-1] <-- TCP:1443 --> [MON113-2] <-- TCP:10.195.124.97:443
[Your host] <------------------------------------------- TCP:1443 -----------------------------------------------> Proxy
```

Commands:

```raw
WORKSTATION > ssh       HORIZON -L 1443:127.0.0.1:1443       # Forward local WORKSTATION:1443  to remote HORIZON:1443   through HORIZON:1443
HORIZON     > ssh 172.16.113.13 -L 1443:127.0.0.1:1443       # Forward local HORIZON:1443      to remote MON113-1:1443  through MON113-1:1443
MON113-1    > ssh   10.0.113.13 -L 1443:10.195.124.97:443    # Forward local MON113-1:1443     to remote PROXY:443      through MON113-2:1443
MON113-2    >                                                # Keep connection open
```

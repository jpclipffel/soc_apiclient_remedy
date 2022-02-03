# Templates

This directory contains the `soc_apiclient_remedy`'s XML templates (template
language is *Jinja2*).

## `cac_siem_create.xml`
Create a new CACEIS SIEM ticket.

Templates variables:
* `src_ip`: Source IP address (example: *0.0.0.0*)
* `dest_ip`: Destination IP address (example: *0.0.0.0*)
* `alert_name`: SIEM's alert's name (example: *XLM - RSA Lockme login*)
* `comment`: Analyst's comment (example: *P4 - No offense - ...*)
* `alert_id`: Alert unique ID (example: *1234*)
* `case_name`: Case name (example: *SOC-CAC-SIEM-1234*)
* `priority`: Priority level as:
  * `1000`: **P1**
  * `2000`: **P2**
  * `3000`: **P3**
  * `4000`: **P4**

## `cac_siem_list.xml`
List the existing CACEIS SIEM tickets.

Template variables:
* `status`: Tickets' status as:
  * `CREATE`: Newly created tickets
  * `ASSIGNED`: Assigned tickets
  * `CLOSED`: Closed tickets

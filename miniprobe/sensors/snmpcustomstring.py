#!/usr/bin/env python
# Copyright (c) 2014, Paessler AG <support@paessler.com>
# All rights reserved.
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions
# and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
# and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse
# or promote products derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import gc
import logging
import time

try:
    from pysnmp.entity.rfc3413.oneliner import cmdgen
    snmp = True
except Exception as e:
    logging.error("PySNMP could not be imported. SNMP Sensors won't work.Error: %s" % e)
    snmp = False
    pass


class SNMPCustomString(object):

    def __init__(self):
        gc.enable()

    @staticmethod
    def get_kind():
        """
        return sensor kind
        """
        return "mpsnmpcustomstring"

    @staticmethod
    def get_sensordef():
        """
        Definition of the sensor and data to be shown in the PRTG WebGUI
        """
        sensordefinition = {
            "kind": SNMPCustomString.get_kind(),
            "name": "SNMP Custom String",
            "description": "Monitors a string value returned by a specific OID using SNMP",
            "help": "Monitors a string value returned by a specific OID using SNMP",
            "tag": "mpsnmpcustomstringsensor",
            "groups": [
                {
                    "name": "OID values",
                    "caption": "OID values",
                    "fields": [
                        {
                            "type": "edit",
                            "name": "oid",
                            "caption": "OID Value",
                            "required": "1",
                            "help": "Please enter the OID value."
                        },
                        {
                            "type": "radio",
                            "name": "snmp_version",
                            "caption": "SNMP Version",
                            "required": "1",
                            "help": "Choose your SNMP Version",
                            "options": {
                                "1": "V1",
                                "2": "V2c",
                                "3": "V3"
                            },
                            "default": 2
                        },
                        {
                            "type": "edit",
                            "name": "community",
                            "caption": "Community String",
                            "required": "1",
                            "help": "Please enter the community string."
                        },
                        {
                            "type": "integer",
                            "name": "port",
                            "caption": "Port",
                            "required": "1",
                            "default": 161,
                            "help": "Provide the SNMP port"
                        }
                    ]
                }
            ]
        }
        if not snmp:
            sensordefinition = ""
        return sensordefinition

    def snmp_get(self, oid, target, snmp_type, community, port, unit):
        try:
            sys.path.append('./')
            from pysnmp.entity.rfc3413.oneliner import cmdgen
            start = time.clock()
            snmpget = cmdgen.CommandGenerator()
            error_indication, error_status, error_index, var_binding = snmpget.getCmd(
                cmdgen.CommunityData(community), cmdgen.UdpTransportTarget((target, port)), oid)
            end = time.clock()
            delta = (end - start) * 1000
        except Exception as import_error:
            logging.error(import_error)
            raise

        channel_list = [ 
            {   
                "name": "Response Time",
                "mode": "float",
                "kind": "TimeResponse",
                "value": float(delta)
            }
        ]  
        return (
            str(var_binding[0][1]),
            channel_list
        )

    @staticmethod
    def get_data(data, out_queue):
        snmpcustom = SNMPCustomString()
        try:
            snmp_data, channel = snmpcustom.snmp_get(str(data['oid']), data['host'], 'string',
                                            data['community'], int(data['port']), '')
            logging.debug("Running sensor: %s" % snmpcustom.get_kind())
        except Exception as get_data_error:
            logging.error("Ooops Something went wrong with '%s' sensor %s. Error: %s" % (snmpcustom.get_kind(),
                                                                                         data['sensorid'],
                                                                                         get_data_error))
            data = {
                "sensorid": int(data['sensorid']),
                "error": "Exception",
                "code": 1,
                "message": "SNMP Request failed. See log for details"
            }
            out_queue.put(data)
            return 1

        data = {
            "sensorid": int(data['sensorid']),
            "message": snmp_data,
            "channel": channel
        }
        del snmpcustom
        gc.collect()
        out_queue.put(data)
        return 0

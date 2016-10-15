import logging
logging.basicConfig(level=logging.DEBUG)
from spyne import Application, rpc, srpc, ServiceBase, \
    Integer, Unicode
from flask import request
from urllib2 import urlopen
import requests, json
from spyne import Iterable
import re
from spyne.protocol.http import HttpRpc
from spyne.protocol.json import JsonDocument

from spyne.server.wsgi import WsgiApplication






class checkcrime(ServiceBase):
    @srpc(Unicode, Unicode, Unicode, _returns=Iterable(Unicode))
    def checkcrime(lat, lon, radius):
        output = {}
        street_dict = {}
        output["the_most_dangerous_streets"] = []
        output["crime_type_count"] = {}
        output["total_crime"] = 0
        output["event_time_count"] = {}
        output["event_time_count"]["12:01am-3am"] = 0
        output["event_time_count"]["3:01am-6am"] = 0
        output["event_time_count"]["6:01am-9am"] = 0
        output["event_time_count"]["9:01am-12noon"] = 0
        output["event_time_count"]["12:01pm-3pm"] = 0
        output["event_time_count"]["3:01pm-6pm"] = 0
        output["event_time_count"]["6:01pm-9pm"] = 0
        output["event_time_count"]["9:01pm-12midnight"] = 0

        url = 'https://api.spotcrime.com/crimes.json?lat=%s&lon=%s&radius=%s&key=.' % (lat, lon, radius)
        response = urlopen(url)
        json_obj = json.load(response)
        for i in json_obj['crimes']:
            output['total_crime'] += 1
            if i["type"] in output["crime_type_count"]:
                output["crime_type_count"][i["type"]] += 1
            else:
                output["crime_type_count"][i["type"]] = 1

            # Filling the time slots

            time_stamp = i["date"]
            hour = int(time_stamp[9:11])
            minute = int(time_stamp[12:14])
            time = time_stamp[15:18]


            if time == 'AM':
                if(hour == 12 or hour<=3):
                    if (hour == 12 and minute ==0):
                        output["event_time_count"]["9:01pm-12midnight"] += 1
                    elif(hour==3 and minute>0):
                        output["event_time_count"]["3:01am-6am"] += 1
                    else:
                        output["event_time_count"]["12:01am-3am"] += 1
                elif(hour >=3 and hour<=6):
                    if(hour==6 and minute>0):
                        output["event_time_count"]["6:01am-9am"] += 1
                    else:
                        output["event_time_count"]["3:01am-6am"] += 1
                elif (hour>=6 and hour<=9):
                    if(hour==9 and minute>0):
                        output["event_time_count"]["9:01am-12noon"] +=1
                    else:
                        output["event_time_count"]["6:01am-9am"] += 1
                else:
                    output["event_time_count"]["9:01am-12noon"]+=1

            else:
                if (hour == 12 or hour <=3):
                    if(hour==12 and minute==0):
                        output["event_time_count"]["9:01am-12noon"] += 1
                    elif (hour == 3 and minute >0 ):
                        output["event_time_count"]["3:01pm-6pm"] += 1
                    else:
                        output["event_time_count"]["12:01pm-3pm"] += 1

                elif(hour >=3 and hour<=6):
                    if(hour==6 and minute>0):
                        output["event_time_count"]["6:01pm-9pm"] += 1
                    else:
                        output["event_time_count"]["3:01pm-6pm"] += 1

                elif (hour>=6 and hour<=9):
                    if(hour==9 and minute>0):
                        output["event_time_count"]["9:01pm-12midnight"] +=1
                    else:
                        output["event_time_count"]["6:01pm-9pm"] += 1
                else:
                    output["event_time_count"]["9:01pm-12midnight"]+=1

            # working on Street address
            if '&' in  i["address"]:
                street = re.split(' & ',i["address"])
                for t in street:
                   if t in street_dict:
                       street_dict[t] += 1
                   else:
                       street_dict[t] = 1
            elif 'BLOCK OF ' in i["address"]:
                pattern = "BLOCK OF "
                street = re.split(pattern,i["address"])
                if street[1]in street_dict:
                    street_dict[street[1]] += 1
                else:
                    street_dict[street[1]] = 1
            elif 'BLOCK BLOCK' in i["address"]:
                pattern = "BLOCK BLOCK "
                street = re.split(pattern, i["address"])
                if street[1] in street_dict:
                    street_dict[street[1]] += 1
                else:
                    street_dict[street[1]] = 1
            elif 'BLOCK' in i["address"]:
                pattern = "BLOCK "
                street = re.split(pattern, i["address"])
                if street[1] in street_dict:
                    street_dict[street[1]] += 1
                else:
                    street_dict[street[1]] = 1
            else:
                if i["address"] in street_dict:
                    street_dict[i["address"]] += 1
                else:
                    street_dict[i["address"]] = 1


        street = sorted(street_dict,key=street_dict.get,reverse=True)
        output["the_most_dangerous_streets"].append(street[0])
        output["the_most_dangerous_streets"].append(street[1])
        output["the_most_dangerous_streets"].append(street[2])






        #yield street_dict
        #yield ouput["the_most_dangerous_streets"]

        yield output




application = Application([checkcrime],
                          tns='spyne.examples.checkcrime',
                          in_protocol=HttpRpc(validator='soft'),
                          out_protocol=JsonDocument()
                          )

if __name__ == '__main__':
    # You can use any Wsgi server. Here, we chose
    # Python's built-in wsgi server but you're not
    # supposed to use it in production.
    from wsgiref.simple_server import make_server

    wsgi_app = WsgiApplication(application)
    server = make_server('0.0.0.0', 8000, wsgi_app)
    server.serve_forever()

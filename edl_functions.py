from __init__ import *
import base64
import http.client
import requests
import ssl
import re
import xml.etree.ElementTree as ET

# Сheck_01: Validate json
# Import input variables 
def check_json(file):
    try:
        with open(file) as input_json:
            input = json.load(input_json)
        firewall_connection = input["firewall_connection"]
        dynamic_lists       = input["dynamic_lists"]
        logger.success(f"Input file \"{file}\" read successfully!")
        return firewall_connection, dynamic_lists
    except ValueError:
        logger.critical(f"Error reading \"{file}\", check syntax!")
        quit()

# Сheck_02: Validate API Restconf port
# Import API Restconf port in int 
def check_api_port(not_valid_api_port):
    try:
        api_port = int(not_valid_api_port)
        logger.success(f"Firewall API Restconf port {not_valid_api_port} is correct!")
        return api_port
    except ValueError:
        logger.critical(f"Firewall API Restconf port {not_valid_api_port} is incorrect!")
        quit()

# Сheck_03: Validate API Restconf token and checking firewall connecting
def fw_get_token(username, password, fw_address, api_port):
    api_token = f"{username}:{password}"
    api_token = base64.b64encode(bytes(api_token.encode(encoding="UTF-8"))).decode()

    answer = fw_send_request(api_token, 
                             fw_address, 
                             api_port, 
                             "GET", 
                             "/restconf/data/huawei-device:device-state", 
                             None)
    if answer:
        status, reason, reply = answer
        if status == 200 or status == 201:
            logger.success(f"Connection to the firewall:\"{fw_address}\" was successful")
            return api_token
        else:
            logger.critical("Connection to the firewall was not successful")
            logger.critical(reason)
            quit() 
    else:
        quit()

# Connecting to firewall Huawei USG
def fw_send_request(api_token, fw_address, fw_api_port, method, url, body):
    headers = {
        "Cache-Control": "no-cache,no-store",
        "Connection": "Keep-Alive",
        "Accept": "application/yang-data+xml",
        "Content-Type": "application/yang-data+xml",
        "Authorization": "Basic " + api_token
        }
    # context = ssl._create_default_https_context()     #security version tlsv1 tlsv1.1 tlsv1.2
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)  # sercurity version tlsv1.2
    context.set_ciphers(RESTRICTED_SERVER_CIPHERS)
    httpClient = http.client.HTTPSConnection(fw_address, fw_api_port, timeout=600, context=context)
    try:
        httpClient.request(method, url, body, headers)
        response    = httpClient.getresponse()
        status      = response.status
        reason      = response.reason
        reply       = response.read()
        httpClient.close()
        logger.debug(f"Firewall connection successfully established!")
        return status, reason, reply
    except Exception as e:
        httpClient.close()
        logger.critical(e)
        return 0

# Create new Dynamic list group
def fw_create_new_edl(name, api_token, fw_address, fw_api_port, fw_vsys):
    answer_create_group = fw_send_request(api_token,
                                          fw_address,
                                          fw_api_port,
                                          "PUT", 
                                          f"/restconf/data/huawei-address-set:address-set/addr-group={fw_vsys},{name}",
                                          None)
    if answer_create_group:
        logger.success(f"Dynamic list group \"{name}\" has been successfully created on firewall")
    else:
        logger.error(f"Dynamic list group \"{name}\" was not created in the firewall!")

# Delete old object from group-address-objects and from Firewall
def fw_erase_old_edl(name, check, api_token, fw_address, fw_api_port, fw_vsys):
    xml_str = ET.fromstring(check)
    for i in xml_str:
                
        # Delete old object from group-address-objects
        answer_delete_object_from_object = fw_send_request(api_token, 
                                                           fw_address, 
                                                           fw_api_port, 
                                                           "DELETE", 
                                                           f"/restconf/data/huawei-address-set:address-set/addr-group={fw_vsys},{name}/elements={i[0].text}",
                                                           None)
        if answer_delete_object_from_object:
            logger.success(f"Sublist \"{i[1].text}\" detached from dynamic list group \"{name}\" successfully!")
        else:
            logger.error(f"Sublist \"{i[1].text}\" was not detached from dynamic list group \"{name}\"!")

        # Delete old object from Firewall
        answer_delete_object = fw_send_request(api_token, 
                                               fw_address, 
                                               fw_api_port, 
                                               "DELETE", 
                                               f"/restconf/data/huawei-address-set:address-set/addr-object={fw_vsys},{i[1].text}", 
                                               None)
        if answer_delete_object:
            logger.success(f"Sublist \"{i[1].text}\" deleted successfully!")
        else:
            logger.error(f"Sublist \"{i[1].text}\" was not deleted!")

# Get txt Dynamic List
def get_edl(name, url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logger.success(f"Connection to the Dynamic List \"{name}\" was successfully")
            return list(filter(None, response.text.split("\n")))
        else:
            logger.error(f"Connection to the Dynamic List \"{name}\" was not successful, returned code - {response.status_code}")
            return 0
    except Exception as e:
        logger.error(f"Connection to the Dynamic List \"{name}\" was not successful, check Dynamic List address \"{url}\"")
        logger.error(e)
        return 0
    
# Check and delete address list from Firewall
def fw_check_obj(name, api_token, fw_address, fw_api_port, fw_vsys):
    logger.info(f"Getting information about sublist \"{name}\"...")
    answer = fw_send_request(api_token, 
                            fw_address, 
                            fw_api_port, 
                            "GET",
                            f"/restconf/data/huawei-address-set:address-set/addr-object={fw_vsys},{name}", 
                            None)
    if answer:
        status, reason, reply = answer
        # object is exists
        if status == 200 and reply.decode("UTF-8").find("<data>") != -1:
            logger.info(f"Sublist \"{name}\" is exists")

            # Delete address list from Firewall
            answer_delete_object = fw_send_request(api_token, 
                                                fw_address, 
                                                fw_api_port, 
                                                "DELETE", 
                                                f"/restconf/data/huawei-address-set:address-set/addr-object={fw_vsys},{name}", 
                                                None)
            if answer_delete_object:
                logger.success(f"Sublist \"{name}\" deleted successfully")
            else:
                logger.error(f"Sublist \"{name}\" was not deleted!")            

        # object not exists
        else: 
            logger.info(f"Sublist \"{name}\" does not exist")
    else:
        logger.error(f"Sublist deletion problem: \"{name}\"")

# Deploy
def fw_deploy_edl(edl, name, api_token, fw_address, fw_api_port, fw_vsys):
    # Deploy new sublists and deploy new sublists to group object
    group_body = ""
    for record in edl:

        # First border address
        if edl.index(record) % RANGE_LIST == 0 and edl.index(record) == 0:
            body = "<addr-object>"
            try:                        
                if ipaddress.ip_network(record).version == 4:
                    body += f"<elements><elem-id>{edl.index(record)%RANGE_LIST}</elem-id><address-ipv4>{ipaddress.ip_network(record)}</address-ipv4></elements>"
                elif ipaddress.ip_network(record).version == 6:
                    body += f"<elements><elem-id>{edl.index(record)%RANGE_LIST}</elem-id><address-ipv6>{ipaddress.ip_network(record).exploded}</address-ipv6></elements>"
            except ValueError:
                logger.error(f"Dynamic list \"{name}\" contains invalid IP address: \"{record}\" with index \"{edl.index(record)}\"")

        # Border address
        elif edl.index(record) % RANGE_LIST == 0:
            
            # Delete old sublist
            fw_check_obj(f"{name}_{edl.index(record) // RANGE_LIST - 1}", api_token, fw_address, fw_api_port, fw_vsys)

            # Deploy new sublist
            body += "</addr-object>"
            logger.info(f"Deploy addr-object \"{name}_{edl.index(record) // RANGE_LIST - 1}\"")
            created_obj_status, created_obj_reason, created_obj_reply = fw_send_request(api_token, 
                                                                                        fw_address, 
                                                                                        fw_api_port, 
                                                                                        "POST", 
                                                                                        f"/restconf/data/huawei-address-set:address-set/addr-object={fw_vsys},{name}_{edl.index(record) // RANGE_LIST - 1}", 
                                                                                        body)
            if created_obj_status == 201:
                logger.success(f"Deploy addr-object \"{name}_{edl.index(record) // RANGE_LIST - 1}\" was successful!")
            else:
                logger.error(f"Deploy addr-object \"{name}_{edl.index(record) // RANGE_LIST - 1}\" was not successful!")

            group_body += f"<elements><elem-id>{edl.index(record) // RANGE_LIST - 1}</elem-id><addrset-name>{name}_{edl.index(record) // RANGE_LIST - 1}</addrset-name></elements>"

            body = "<addr-object>"
            try:                        
                if ipaddress.ip_network(record).version == 4:
                    body += f"<elements><elem-id>{edl.index(record)%RANGE_LIST}</elem-id><address-ipv4>{ipaddress.ip_network(record)}</address-ipv4></elements>"
                elif ipaddress.ip_network(record).version == 6:
                    body += f"<elements><elem-id>{edl.index(record)%RANGE_LIST}</elem-id><address-ipv6>{ipaddress.ip_network(record).exploded}</address-ipv6></elements>"
            except ValueError:
                logger.error(f"Dynamic list \"{name}\" contains invalid IP address: \"{record}\" with index \"{edl.index(record)}\"")

        # Last address
        elif edl.index(record) == len(edl)-1: 
            try:                        
                if ipaddress.ip_network(record).version == 4:
                    body += f"<elements><elem-id>{edl.index(record)%RANGE_LIST}</elem-id><address-ipv4>{ipaddress.ip_network(record)}</address-ipv4></elements>"
                elif ipaddress.ip_network(record).version == 6:
                    body += f"<elements><elem-id>{edl.index(record)%RANGE_LIST}</elem-id><address-ipv6>{ipaddress.ip_network(record).exploded}</address-ipv6></elements>"
            except ValueError:
                logger.error(f"Dynamic list \"{name}\" contains invalid IP address: \"{record}\" with index \"{edl.index(record)}\"")


            # Delete old sublist
            fw_check_obj(f"{name}_{edl.index(record) // RANGE_LIST}", api_token, fw_address, fw_api_port, fw_vsys)

            # Deploy new sublist
            body += "</addr-object>"
            logger.info(f"Deploy addr-object \"{name}_{edl.index(record) // RANGE_LIST}\"")
            created_obj_status, created_obj_reason, created_obj_reply = fw_send_request(api_token, 
                                                                                        fw_address, 
                                                                                        fw_api_port, 
                                                                                        "POST", 
                                                                                        f"/restconf/data/huawei-address-set:address-set/addr-object={fw_vsys},{name}_{edl.index(record) // RANGE_LIST}", 
                                                                                        body)
            # Attach new sublists to grouplist
            group_body += f"<elements><elem-id>{edl.index(record) // RANGE_LIST}</elem-id><addrset-name>{name}_{edl.index(record) // RANGE_LIST}</addrset-name></elements></addr-group>"
            logger.info(f"Attaching sublists to grouplist")
            time_now = strftime("%H:%M %d.%m.%Y", time.localtime())
            group_body = f"<addr-group><vsys>{fw_vsys}</vsys><name>{name}</name><desc>changed at {time_now}</desc>" + group_body
            answer_modify_desk = fw_send_request(api_token, 
                                                    fw_address, 
                                                    fw_api_port, 
                                                    "PATCH", 
                                                    f"/restconf/data/huawei-address-set:address-set/addr-group={fw_vsys},{name}", 
                                                    group_body)

        # Other adress
        else:
            try:                        
                if ipaddress.ip_network(record).version == 4:
                    body += f"<elements><elem-id>{edl.index(record)%RANGE_LIST}</elem-id><address-ipv4>{ipaddress.ip_network(record)}</address-ipv4></elements>"
                elif ipaddress.ip_network(record).version == 6:
                    body += f"<elements><elem-id>{edl.index(record)%RANGE_LIST}</elem-id><address-ipv6>{ipaddress.ip_network(record).exploded}</address-ipv6></elements>"
            except ValueError:
                logger.error(f"Dynamic list \"{name}\" contains invalid IP address: \"{record}\" with index \"{edl.index(record)}\"")

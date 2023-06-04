from __init__ import *
from edl_functions import check_json, check_api_port, fw_get_token, fw_send_request, fw_create_new_edl, fw_erase_old_edl, get_edl, fw_deploy_edl

logger.info("Script starting...")

# Import variables
firewall_connection, external_dynamic_lists = check_json("input.json")

# Import API Restconf port in int 
api_port = check_api_port(firewall_connection["api_port"])

# Configure Token
api_token = fw_get_token(firewall_connection['api_username'], firewall_connection['api_password'], firewall_connection['address'], api_port)

# Deploy External Dynamic Lists
for item in external_dynamic_lists:
        
    # Get EDL from WEB-server
    edl = get_edl(item["name"], item["link"])

    # Get EDL from Firewall
    answer = fw_send_request(api_token, firewall_connection["address"], api_port, "GET", f"/restconf/data/huawei-address-set:address-set/addr-group={firewall_connection['vsys']},{item['name']}", None)

    # Group opbject exists and not empty
    # Сheck_03: Validate Firewall connecting and WEB-server
    if answer and edl:
        logger.success(f"Information about the dynamic list \"{item['name']}\" from the firewall and from WEB-host was successfully received")
        status, reason, reply = answer
        reply       = reply.decode("UTF-8")
        check       = reply[reply.find("<addr-group>"):reply.find("</addr-group>")+13]
        check_desc  = check[check.find("<desc>"):check.find("</desc>")+7]
        check       = check.replace(check_desc, "")
        check_vsys  = check[check.find("<vsys>")+6:check.find("</vsys>")]
        check       = check.replace(f"<vsys>{check_vsys}</vsys>", "")
        check_edl    = check[check.find("<name>")+6:check.find("</name>")]
        check       = check.replace(f"<name>{check_edl}</name>", "")

        # Group does not exist
        if not check:
            logger.info(f"Dynamic list group \"{item['name']}\" not created on firewall")

            # Create new Dynamic list group
            fw_create_new_edl(item['name'], api_token, firewall_connection["address"], api_port, firewall_connection['vsys'])
            fw_deploy_edl(edl, item['name'], api_token, firewall_connection["address"], api_port, firewall_connection['vsys'])

        # Group is filled with old lists
        elif check_vsys == firewall_connection["vsys"] and check_edl == item["name"] and check.find("<elements>") and not check == "<addr-group></addr-group>":
            logger.info(f"Dynamic list group \"{item['name']}\" created on firewall and filled with sublists, sublists are being cleared...")

            # Delete old object from group-address-objects and from Firewall
            fw_erase_old_edl(item['name'], check, api_token, firewall_connection["address"], api_port, check_vsys)
            fw_deploy_edl(edl, item['name'], api_token, firewall_connection["address"], api_port, firewall_connection['vsys'])

        # Group is empty
        elif check == "<addr-group></addr-group>":
            logger.info(f"Dynamic list group \"{item['name']}\" created and empty")
            fw_deploy_edl(edl, item['name'], api_token, firewall_connection["address"], api_port, firewall_connection['vsys'])

        # Fuck knows what's wrong here
        else:
            logger.error(f"Unknown error with dynamic list group \"{item['name']}\" on firewall")
            logger.error(check)

    # Only firewall available
    elif answer:
        logger.error(f"Connection to the firewall was successful during dynamic list \"{item['name']}\", but connection to the WEB-host was not successful. EDL \"{item['name']}\" skipped.")

    # Only WEB-host available
    elif edl:
        logger.critical(f"Connection to the firewall was not successful during dynamic list \"{item['name']}\" retrieval process, but connection to the WEB-host was successful. Emergency termination of the script!")
        quit() 

    # Nothing available!
    else:
        logger.critical(f"Connection to the firewall and to the WEB-host was not successful during dynamic list \"{item['name']}\" retrieval process. Emergency termination of the script!")
        logger.critical(reason)
        quit() 

logger.success("Script completed")
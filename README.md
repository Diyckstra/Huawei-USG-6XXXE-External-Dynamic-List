# External Dynamic List on Firewall Huawei HiSecEngine USG6600E Series

### Description

An External Dynamic List is a text file that is hosted on an external web server so that the firewall can import objects — IP addresses, URLs, domains — included in the list and enforce policy. To enforce policy on the entries included in the external dynamic list, you must reference the list in a supported policy rule or profile. As you modify the list, the firewall dynamically imports the list at the configured interval and enforces policy without the need to make a configuration change or a commit on the firewall. If the web server is unreachable, the firewall uses the last successfully retrieved list for enforcing policy until the connection is restored with the web server.

EDL format `txt` examples:
* [torlist](https://www.dan.me.uk/torlist/)
* [torbulkexitlist](https://check.torproject.org/torbulkexitlist)
* [Palo Alto Lists](https://docs.paloaltonetworks.com/resources/edl-hosting-service)

EDL format `json` examples:
* [Office 365 URLs and IP address ranges](https://learn.microsoft.com/en-us/microsoft-365/enterprise/urls-and-ip-address-ranges?view=o365-worldwide)

The EDL feature is not present in the Huawei USG firewall, so it is implemented using API Restconf. An example of how EDL works is taken from the firewall vendor [Palo Alto](https://docs.paloaltonetworks.com/pan-os/9-1/pan-os-admin/policy/use-an-external-dynamic-list-in-policy/external-dynamic-list). For work EDL, a separate dedicated Linux station is required, on which the operations of accessing to the EDL web host and installing the EDL on the firewall will take place. 

---

### Features

- [X] Firewall objects based on host and network IP addresses
- [ ] Firewall objects based on URLs
- [ ] Firewall objects based on domains
- [X] EDL format `txt`
- [ ] EDL format `json`

---

### Pre-requirements

* Firewall Huawei HiSecEngine USG6600E Series
* python3 version >= 3.8 on Linux station
* Сorrectly configured time on Linux station
* Network connectivity between linux station and firewall

---

### Installation and Configuration

#### Firewall configuration

1) Login to the web-interface of your firewall
2) Go to the page `System -> Administrator -> Service Settings -> Northbound Interface Settings`, check `RESTCONF` and click `Apply`
3) Go to the page `System -> Administrator -> Service Settings -> Administrator`, click `Add`. Fill in the `Name` and `Password` fields. Select nothing in the `Role` field. In the `Advanced Settings` check only `API`. Click `OK`
4) Go to the page `Policy -> Security Policy -> Security Policy`, click `Add`. Fill in the `Name` field. In the field `Source Address/Region` select address of linux station. In the field `Destination Zone` select `local` zone. In the `Service` select `TCP/8447`. Click `OK`

#### Linux station configuration

*note: setup example on Debian-family of Linux*

##### Script configuration

1) Get root
    ```
    sudo -i
    ```

2) Install `pip`
    ```
    apt update && apt install python3-pip -y
    ```

3) Change directory to script location
    ```
    cd /usr/local/sbin
    ```

4) Clon a repository with script code
    ```
    git clone https://github.com/Diyckstra/Huawei-USG-6XXXE-External-Dynamic-List.git
    ```

5) [optional] Create user from which the script will be executed
    ```
    useradd -c "Huawei Scripts" -M -r huawei-usg -s /bin/bash && chown -R huawei-usg Huawei-USG-6XXXE-External-Dynamic-List
    ```

6) Install script requirements
    ```
    cd Huawei-USG-6XXXE-External-Dynamic-List && python3 -m pip install -r requirements.txt
    ```

7) [optional] Login with created user
    ```
    su huawei-usg
    ```

8) Customize the script input data from the example
    ```
    cp input.json.example input.json && nano input.json
    ```

9) Check the script
    ```
    python3 edl_main.py
    ```

##### Set up periodic script execution using `crontab`

To periodically execute the script, you need to add its execution to the `crontab` task scheduler

1) Launch task scheduler `crontab`
    ```
    crontab -e
    ```

2) Add a script launch entry to the end of the file, where you can specify the launch time parameters yourself

    *note: For convenience, use the resource [crontab.guru](https://crontab.guru/#*_*_*_*_*)*

    ```
    0 5 */3 * * (cd /usr/local/sbin/Huawei-USG-6XXXE-External-Dynamic-List; python3 edl_main.py >/dev/null 2>&1)
    ```

##### [optional] Cron log configuration

To debug script execution using `crontab`, you need to configure `crontab` logging in `rsyslog`

1) Get root (exit from created user to root)
    ```
    exit
    ```

2) Open rsyslog configuration file
    ```
    nano /etc/rsyslog.conf
    ```

3) Add to the end of the file
    ```
    cron.* /var/log/cron.log
    ```

4) Restart the service
    ```
    systemctl restart rsyslog.service
    ```

##### Сhanging log rotation parameters

By default, the rotation is set to 100 MB. If necessary, you can set other values for the rotation parameter, which are defined [here](https://loguru.readthedocs.io/en/stable/overview.html#easier-file-logging-with-rotation-retention-compression).


1) Open a file in which log rotation is configured
    ```
    nano /usr/local/sbin/Huawei-USG-6XXXE-External-Dynamic-List/__init__.py
    ```
2) In line `logger.add("EDL.log", format="{time:HH:mm:ss DD.MM.YYYY} {level} {message}", rotation="100 MB")` we set the parameter `rotation="{paremeter}"`


##### Check logs for troubleshooting

```
less /usr/local/sbin/Huawei-USG-6XXXE-External-Dynamic-List/EDL.log
less /var/log/cron.log
```

---

### Successfully tested on the following versions:
#### Firewall Huawei:
* USG6630E V600R007C20SPC500
* USG6655E V600R007C20SPC600
#### Operating System:
* Ubuntu 18.04.6 LTS
* Ubuntu 20.04.6 LTS
* Ubuntu 22.04.2 LTS
* Debian 10

---

### Official documentation
* [Configuration of the RESTAPI interface on the firewall](https://support.huawei.com/view/contentview/getFileStream?mid=SUPE_DOC&viewNid=EDOC1000118180&nid=EDOC1000118180&partNo=j00p&type=htm#sec_case_north_0004_1)
* [API Development Guide](https://support.huawei.com/enterprise/en/doc/EDOC1100163128)

---

Co-authored-by: [Dima Ozolin](https://github.com/Cmertho)
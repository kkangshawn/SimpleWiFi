#!/usr/bin/python
"""
 @ Todo: (subprocess.check_output + decoding) to a function
         Add routine for key_mgmt=NONE
"""


import subprocess, os, time

class STATIC:
    deviceName = ""
    IPaddress = ""
    apList = [0]
    isUbuntu = True

def main():
    p = subprocess.check_output("cat /etc/*-release", shell=True)
    output = p.decode("utf-8")
    try:
        output.index("Ubuntu")
        print("Ubuntu")
    except:
        STATIC.isUbuntu = False
        print("RHEL")

    getiwconfig()
    while (1):
        print("=" * 30)
        print("WiFi diagnostic tool")
        print("=" * 30)
        print(" 1. Get Device info")
        print(" 2. Scan Network")
        print(" 3. Connect to Access Point")
        print(" 4. Throughput test")
        print(" 0. Exit")
        print("=" * 30)

        userInput = input()
        if userInput == '1':
            getiwconfig()
        elif userInput == '2':
            if STATIC.deviceName == "":
                print("No device information. Please get device info.")
            else:
                wifiscan()
        elif userInput == '3':
            connectap()
        elif userInput == '0':
            break

##########################################################

def connectap():
    scancount = 0
    while (STATIC.apList[0] == 0) & (scancount < 5):
        print("No AP found yet. Scanning...")
        scancount += 1
        time.sleep(1)
        wifiscan()

    if STATIC.apList[0] == 0:
        print("No AP to connect")
        return

    print("Choose number in the AP list")
    try:
        userInput = int(input())
    except ValueError as e:
        print("Invalid value:", e)
        return

    if (userInput > 0) & (userInput <= STATIC.apList[0]):
        setwpasupplicant(STATIC.apList[userInput])

    else:
        print("Input number is out of range")
        return

##########################################################

def setwpasupplicant(apset):    # apset: ['SSID', 'Frequency', 'RSSI', 'Security']
    print(apset)
    cmd_wpacli = "wpa_cli -i" + STATIC.deviceName + " "

    p = subprocess.check_output(cmd_wpacli + "add_network", shell=True)
    network_id = p.decode("utf-8")
    network_id = network_id[:network_id.index('\n')]

    p = subprocess.check_output(cmd_wpacli + 
            'set_network %s ssid \\"%s\\"' % (network_id, apset[0]), shell=True)
    if not p.decode("utf-8").startswith("OK"):
        print("wpa_cli: set_network failed")
        return
 

    if apset[3].find("WPA") == -1:
        p = subprocess.check_output(cmd_wpacli + 'set_network %s key_mgmt "NONE"' % network_id,
                shell=True)
        if not p.decode("utf-8").startswith("OK"):
            print("wpa_cli: set_network key_mgmt failed")
            return
    else:
        print("Input passphrase: ")
        psk = input()
        p = subprocess.check_output(cmd_wpacli + 
                'set_network %s psk \\"%s\\"' % (network_id, psk), shell=True)
        if not p.decode("utf-8").startswith("OK"):
            print("wpa_cli: set_network psk failed")
            return
    p = subprocess.check_output(cmd_wpacli + "select_network %s" % network_id, shell=True)
    if not p.decode("utf-8").startswith("OK"):
        print("wpa_cli: select_network failed")
        return

    print("Waiting to be connected...")
    checkcount = 0
    ap_essid = ""
    while (ap_essid != apset[0]) & (checkcount < 10):
        p = subprocess.check_output(["iwconfig", STATIC.deviceName], stderr=open(os.devnull, 'w'))
        output = p.decode("utf-8")
        try:
            ap_essid = output[output.index("ESSID:") + 7:]
            ap_essid = ap_essid[:ap_essid.index('"')]
        except:
            pass
        checkcount += 1
        time.sleep(1)
    if ap_essid != apset[0]:
        print("Connection failed")
    else:
        print("Connection established. Receiving IP address...")
        p = subprocess.check_output(["dhclient", STATIC.deviceName], stderr=open(os.devnull, 'w'))

        checkcount = 0
        while checkcount < 10:
            p = subprocess.check_output(["ifconfig", STATIC.deviceName], stderr=open(os.devnull, 'w'))
            output = p.decode("utf-8")
            if output.find("inet ") != -1:
                print("Done")
                return 
            checkcount += 1
            time.sleep(1)
        print("IP is not assigned")

 

##########################################################

def wifiscan():
    cmd_wpacli_scan = "wpa_cli -i" + STATIC.deviceName + " scan"
    cmd_wpacli_scanresult = "wpa_cli -i" + STATIC.deviceName + " scan_results"
    try:
        p = subprocess.check_output(cmd_wpacli_scan, shell=True)
    except:
        if not os.path.exists("/var/run/wpa_supplicant/" + STATIC.deviceName):
            print("Error: wpa_supplicant is not running!")
            return
    output = p.decode("utf-8")
    scancount = 0
    while (output.startswith("FAIL-BUSY") & (scancount < 5)):
        print("Scan failed for device resource busy. Retrying...")
        scancount += 1
        time.sleep(1)
        try:
            p = subprocess.check_output(cmd_wpacli_scan, shell=True)
        except:
            print("wpa_cli error")
            return
        output = p.decode("utf-8")
    if output.startswith("OK"):
        try:
            p = subprocess.check_output(cmd_wpacli_scanresult, shell=True)
        except:
            print("wpa_cli error")
            return
        output = p.decode("utf-8")
        scanlist = output.split('\n')
        STATIC.apList = [0]
        for i in range(1, len(scanlist) - 1):
            ap = scanlist[i].split('\t')
            apset = []
            apset.append(ap[4])     # SSID
            apset.append(ap[1])     # Frequency
            apset.append(ap[2])     # Signal strength
            apset.append(ap[3])     # Security
            STATIC.apList[0] += 1
            STATIC.apList.append(apset)

            print(" %d) SSID: %-16s  Freq: %4s  RSSI: %3s  Security: %s"
                    % (i, apset[0], apset[1], apset[2], apset[3]))
    else:
        print(output)

##########################################################

def getiwconfig():
    p = subprocess.check_output(["iwconfig"], stderr=open(os.devnull, 'w'))
    output = p.decode("utf-8")
    try:
        devstr = output[output.index("wl"):]
    except ValueError:
        print("Cannot find any WiFi devices")
        return

    devstr = devstr[:devstr.index(' ')]
    STATIC.deviceName = devstr
    print("%13s" % "Device Name: " + STATIC.deviceName)

    ## Retrieve AP connection information
    try:
        ap_essid = output[output.index("ESSID:") + 7:]
        ap_essid = ap_essid[:ap_essid.index('"')]
    except:
        pass
    ap_mac = output[output.index("Access Point:") + 14:]
    ap_mac = ap_mac[:ap_mac.index(' ')]
    if ap_mac == "Not-Associated":
        print("%13s" % "AP MAC: " + "Not connected")
    else:
        print("%13s" % "AP MAC: " + ap_mac)
        print("%13s" % "AP SSID: " + ap_essid)
    getifconfig(STATIC.deviceName)

##########################################################
def getifconfig(devstr):
    if devstr == "":
        return "Cannot find any WiFi devices"

    p = subprocess.check_output(["ifconfig"])
    output = p.decode("utf-8")

    ## Bring up WiFi device
    try:
        str = output[output.index(devstr):]
    except:
        print(devstr + " device is not up. Bring up the device")
        try:
            cmd_ifconfig_up = "ifconfig " + devstr + " up"
            p = subprocess.check_output(cmd_ifconfig_up, shell=True)
            p = subprocess.check_output(["ifconfig"])
            output = p.decode("utf-8")
            str = output[output.index(devstr):]
        except:
            print("Failed to bring up a device: " + devstr)
            return

    ## Retrieve device MAC address
    try:
        HWaddrIdx = str.index("HWaddr ") + 7
    except:
        try:
            HWaddrIdx = str.index("ether ") + 6
        except:
            print("MAC address fail!")
            return
    HWaddr = str[HWaddrIdx:HWaddrIdx + 17]
    print("%13s" % "My MAC: " + HWaddr)

    ## Retrieve IP address
    try:
        IPaddrIdx = str.index("inet ") + 5
    except:
        print("%13s" % "IP address: " + "IP is not assigned")
        return

    IPaddr = str[IPaddrIdx:IPaddrIdx + 20]
    if IPaddr.startswith("addr:"):
        IPaddr = IPaddr[5:]
    IPaddr = IPaddr[:IPaddr.index("  ")]
    print("%13s" % "IP address: " + IPaddr)
    STATIC.IPaddress = IPaddr
    
##########################################################
main()

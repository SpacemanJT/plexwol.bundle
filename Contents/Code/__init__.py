###################################################################################################
# Wake on LAN Utility for Plex
#
# SpacemanJT  - Andrew Sharrad 10-04-16
# Please see https://github.com/SpacemanJT/wol.bundle for more information
#
# Many thanks to the valuable contributions from the community in the development of this Plugin.
#
# Basic Functionality: To send WAKE on LAN packets from the Plex Media Server to systems to be woken up.
# This allows the user to bring online additional resources which might be turned off, such as DVR boxes,
# NAS drives or other hosts of library content.
#
# Please note that this Plugin does not wake the PMS from the client App. The PMS needs to be available.
#
# This Plugin allows the user to configure up to 10 systems, which can be woken individually. Each system
# can be disabled, so that it doesnt appear on the list of systems that can be woken.
#
# In addition the plugin supports up to two Wake-up Groups, where Wake requests can be sent to any of the
# specified 10 systems, even if the system is disable from appearing on the main list. Each Wake up group
# can be staggered to add a delay between machines of 0, 0.5,1 or 2 seconds.
#
# The Plugin does its best to error check and where possible correct user preferences. Failures to send
# WOL requests are also reported and logged in C:\Users\Administrator\AppData\Local\Plex Media Server\Logs\PMS Plugin Logs
# or wherever your Plex server is located. Look for com.plexapp.plugins.wol 
#
# Revision History:
# 1.00   10-04-16   Initial Release
# 1.01   10-04-16   Code tidied
# 1.02   10-04-16   Added support for two WOL Groups and staggered startups
# 1.03   10-04-16   Renamed the files in preparation for UAS submission
#
###################################################################################################

import socket
import struct
import time

PREFIX = '/applications/wol'

ART = 'wol_background.png'
ICON = 'wol_icon-default.png'
LIST_ICON = 'wol_icon-list.png'
GROUP_ICON = 'wol_icon-group.png'
ABOUT_ICON = 'wol_icon-about.png'

NAME = 'Wake on LAN'
MAX_SERVERS = 10
WOL_VERSION = 1.03

####################################################################################################
def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    TrackObject.thumb = R(ICON)

####################################################################################################     
@handler(PREFIX , NAME, thumb=ICON, art=ART)
@route(PREFIX + '/MainMenu')
def MainMenu():

    groupcount = 0
    group2count = 0
    
    global grouplist
    grouplist = []
    
    global group2list
    group2list = []
    
    oc = ObjectContainer()

    for i in range(1,MAX_SERVERS+1):
        wakesystem = Loadwakesystem(i)
        if (wakesystem.enable):
            oc.add(CreateTrackObject(macaddress=wakesystem.macaddress, alias=wakesystem.alias, port=wakesystem.port, broadcast_ip=wakesystem.broadcast))

# The code below allows WOL Systems to be added and used to groups even if disabled.

	if (wakesystem.group == "Group 1") or (wakesystem.group == "Groups 1 and 2"):
            grouplist.append(wakesystem)
            groupcount=groupcount+1
        if (wakesystem.group == "Group 2") or (wakesystem.group == "Groups 1 and 2"):
	    group2list.append(wakesystem)
            group2count=group2count+1
    
#    for wakesystem in grouplist:
#        Log ("System: " + wakesystem.alias + " added to group")
    
    if (groupcount > 0):
       groupname = Prefs['Group.1.wolname']
       oc.add(DirectoryObject(key=Callback(groupwake, groupname=groupname, groupnum=1), title="Wake " + groupname, summary="Number of Systems: " + str(groupcount), thumb=R(GROUP_ICON)))
       
    if (group2count > 0):
       group2name = Prefs['Group.2.wolname']
       oc.add(DirectoryObject(key=Callback(groupwake, groupname=group2name, groupnum=2), title="Wake " + group2name, summary="Number of Systems: " + str(group2count), thumb=R(GROUP_ICON)))   

    oc.add(DirectoryObject(key=Callback(About), title='Plugin Version', thumb=R(ABOUT_ICON)))

    return oc

####################################################################################################
@route(PREFIX + '/CreateTrackObject')
def CreateTrackObject(macaddress, alias, port, broadcast_ip, include_container=False):

    track_object = DirectoryObject(key=Callback(sendmagic, macaddress=macaddress, alias=alias, port=port, broadcast_ip=broadcast_ip, sendmess=True ),title="Wake " + alias, summary="MAC Address: " + macaddress, thumb=R(LIST_ICON))

    if include_container:
        return ObjectContainer(objects=[track_object])
    else:
        return track_object


####################################################################################################
@route(PREFIX + '/about')
def About():

    oc = ObjectContainer(title2='About')

    oc.add(DirectoryObject(key=Callback(About), title='Name: %s Version: %s' % (NAME , WOL_VERSION) , summary='See https://github.com/SpacemanJT/wol.bundle for more information.', thumb=R(ABOUT_ICON)))

    return oc

####################################################################################################
@route(PREFIX + '/groupwake', groupnum=int)
def groupwake(groupname, groupnum):

    Log ("Starting Group Wake for Group Name: " + groupname + " Number: " + str(groupnum))
    
    count=0
    errors=0
    firstrun=0
    
    if groupnum == 1:
        groupdelay = Prefs['Group.1.stagger']
        for wakesystem in grouplist:
            if firstrun > 0:
                if groupdelay == "0.5 seconds":
                    time.sleep(0.5)
                if groupdelay == "1 second":
                    time.sleep(1)
                if groupdelay == "2 seconds":
                    time.sleep(2)
            if not (sendmagic(wakesystem.macaddress, wakesystem.alias, wakesystem.port, wakesystem.broadcast, False)):
                errors = errors +1
            count=count + 1
            firstrun = 1

    if groupnum == 2:
        groupdelay = Prefs['Group.2.stagger']
        for wakesystem in group2list:
            if firstrun > 0:
                if groupdelay == "0.5 seconds":
                    time.sleep(0.5)
                if groupdelay == "1 second":
                    time.sleep(1)
                if groupdelay == "2 seconds":
                    time.sleep(2)            
            if not (sendmagic(wakesystem.macaddress, wakesystem.alias, wakesystem.port, wakesystem.broadcast, False)):
                errors = errors +1
            count=count + 1
            firstrun = 1
            

    if errors > 0:
        Log ("Group " + groupname + ": Wake request sent to " + str(count) + " systems with " + str(errors) + " errors")
        if count > 1:
            return MessageContainer(header = 'Success', message = 'Request sent to ' + str(count) + ' systems with ' + str(errors) + ' errors')
        else:
            return MessageContainer(header = 'Success', message = 'Request sent to the system with ' + str(errors) + ' errors')
    else:  
        Log ("Group " + groupname + ": Wake request sent to " + str(count) + " systems with no errors")
        if count > 1:
            return MessageContainer(header = 'Success', message = 'Request sent to ' + str(count) + ' systems with no errors')
        else:
            return MessageContainer(header = 'Success', message = 'Request sent to the system with no errors')

####################################################################################################
@route(PREFIX + '/sendmagic', port=int)
def sendmagic(macaddress, alias, port, broadcast_ip, sendmess):

    send_data = []

    # Pad the synchronization stream
    data = b'FFFFFFFFFFFF' + (macaddress * 20).encode()
    send_data = b''

    # Split up the hex values in pack
    for i in range(0, len(data), 2):
        send_data += struct.pack('B', int(data[i: i + 2], 16))
    Log ("Preparing to Send Wake on LAN Packet")
    Log ("Alias: " + alias)
    Log ("MAC Address: " + macaddress)
    Log ("Port: " + str(port))
    Log ("Broadcast IP: " + broadcast_ip)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.connect((broadcast_ip, port))
        sock.send(send_data)
        sock.close()
        Log ("Packet Sent")
        if (sendmess):
            return MessageContainer(header='Success', message='Request sent to ' + alias)
        else:
            return True
        
    except socket.error as serr:
        Log ("Request failure to " + alias + ":  " + str(serr))
        if (sendmess):
            return MessageContainer(header='Failure', message='Request failure to ' + alias + ': ' + str(serr))
        else:
            return False

####################################################################################################
def Loadwakesystem(i):
    enable = Prefs['system.' + str(i) + '.enabled']
    alias  = Prefs['system.' + str(i) + '.alias']
    macaddress   = Prefs['system.' + str(i) + '.macaddress'].lower()
    port = int(Prefs['system.' + str(i) + '.port'])
    broadcast = Prefs['system.' + str(i) + '.broadcast']
    group = Prefs['system.' + str(i) + '.group']

    if port < 1:
        Log ("System " + str(i) + " Port address is too low at " + str(port) + ", changing to 7")
        port = 7

    if port > 65535:
        Log ("System " + str(i) + " Port number is too high at " + str(port) + ", changing to 7")
        port = 7

    if len(str(macaddress)) == 17:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, '')
        Log ("System " + str(i) + " Removed MAC Address Seperator Character " + sep)

    if len(str(macaddress)) > 12:
        enable = False
        Log ("System " + str(i) + " MAC address is too long, disabling System")

    if len(str(macaddress)) < 12:
        enable = False
        Log ("System " + str(i) + " MAC address is too short, disabling System")

    if is_hex(macaddress) == False:
        enable = False
        Log ("System " + str(i) + " MAC address contains non-hexadecimal characters, disabling System")

    if len(str(alias)) == 0:
        alias = "Media Server " + stri(i)
        Log ("System " + str(i) + " Alias is blank, using default of " + alias)

    if broadcast == "":
        broadcast = "255.255.255.255"
        Log ("System " + str(i) + " Broadcast IP Address is blank, using default of " + broadcast)

    if isgoodipv4(broadcast) == False:
        Log ("Warning: System " + str(i) + " IP Address Invalid - Please ensure this is a valid IP or Hostname")

    return wakesystem(i,enable,alias,macaddress,port,broadcast,group)

###################################################################################################
class wakesystem:
    def __init__(self,index,enable,alias,macaddress, port, broadcast, group):
        self.index = index
        self.enable = enable
        self.alias = alias
        self.macaddress = macaddress
        self.port = port
        self.broadcast = broadcast
        self.group = group

###################################################################################################
def is_hex(s):
    check = str(s)
    hex_digits = set("0123456789abcdef")
    for i in range(0, len(check)):
    	c = check[i]
        if not (c in hex_digits):
#            Log ("Invalid digit " + str(c) + " in string " + str(s))
            return False
    return True

###################################################################################################
def isgoodipv4(s):
    good=True
    pieces = s.split('.')
    if len(pieces) != 4: return False
    for p in pieces:
    	if int(p)<0:
    	    good=False
    	if int(p)>255:
    	    good=False
    return (good)
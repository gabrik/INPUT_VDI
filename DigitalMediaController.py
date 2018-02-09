import json
import socket
from threading import Lock
from utility import bcolors
from ControllerException import ControllerException

BUFFERSIZE = 65535
ALLOWEDOPERATION = ("1", "2", "3", "4", "5", "6", "7")
# PER IL DMC
# START = 1
# PLAY = 2
# STOP = 3 
# PAUSA = 4
# VOL = 5
# MUTE = 6
#/dmc/doAction?uuid=clientuuid&id_content=contentProviderId&action=SOPRA&mobile=1
#Da mandare al controller{"operation":operatiuid":"serveron,"server_uuuid","client_uuid":clinetuuid,"url":url}
#media list : [{"uuid":"898f9738-d930-4db4-a3cf-dc4a3ea8caff","content":[{"name":"Family","url":"http://172.16.0.39:49152/web/2.mp4","directory":"Recorded"},{"name":"sony_eye_candy","url":"http://172.16.0.39:49152/web/3.mpg"}]}]
#{'operation':'play',"client_uuid":clientuuid} PLAY PAUSA STOP
class DigitalMediaController(object):
    
    def __init__(self, addr, port):
        # try:
        #     addr = socket.gethostbyname(addr)
        #     print(addr)
        # except socket.gaierror, err:
        #     print ("cannot resolve hostname:{} , {} ".format(name, err))
        self.addr = addr
        self.port = int(port)
        self.recordedContents = []
        self.liveContents = []
        self.deviceList = []
        self.lock = Lock()
        self.allContents = []
    
    def requestMediaList(self, scan=True):
        try:
            self.lock.acquire()
            if scan:
                self.connectToDmc(operation="scan")
            data = self.connectToDmc(operation="media list")
            mediaList = json.loads(data)
            if not (mediaList):
                print(bcolors.WARNING + "media list is empty" + bcolors.ENDC)
            else:
                self.allContents = list(mediaList)
                messageRecorded = {'content':[], 'uuid':0}
                messageLive = {'content':[], 'uuid':0}
                recorded = []
                live = []
                foundRecorded = False
                foundLive = False
                for media in mediaList:
                    serverUuid = media['uuid']
                    for content in media['content']:
                        if content['directory'].lower() == "recorded":
                            if not foundRecorded:
                                foundRecorded = True
                                messageRecorded['uuid'] = serverUuid
                            messageRecorded['content'].append(content)
                        else:
                            if not foundLive:
                                foundLive = True
                                messageLive['uuid'] = serverUuid
                            messageLive['content'].append(content)
                    if foundLive is True:
                        live.append(messageLive)
                    if foundRecorded is True:
                        recorded.append(messageRecorded)
                    foundLive = False
                    foundRecorded = False
                self.recordedContents=list(recorded)
                self.liveContents=list(live)    
                print(bcolors.OKBLUE+"MEDIA LIST: LIVE {} \n MEDIA {}".format(self.liveContents,self.recordedContents)+bcolors.ENDC)
        except ValueError as ex:
            print("can't convert media list from dmc{}".format(ex))
            raise ControllerException("can't get media List")
        finally:
            self.lock.release()
    
    def getLiveContents(self):
        self.lock.acquire()
        self.lock.release()
        return self.liveContents
    
    def getRecordedContents(self):
        self.lock.acquire()
        self.lock.release()
        return self.recordedContents

    def getAllContents(self):
        self.lock.acquire()
        self.lock.release()
        #print(bcolors.HEADER+"{}".format(self.allContents)+bcolors.ENDC)
        return self.allContents

    def getDeviceList(self):
        self.lock.acquire()
        self.lock.release()
        return self.deviceList

    def changeVolume (self,dict):
        try:
            if all (k in dict for k in ("clientUuid","volume")):
                volume=dict['volume']
                if int(volume) > 100:
                    volume = "100"
                elif int(volume) < 0:
                    volume = "0"            
                data=self.connectToDmc(operation="vol",client_uuid=dict['clientUuid'],volume=volume)
                return data
            else:
                raise ControllerException("Some Value are missing Volume")
        except ControllerException as ex:
            raise ex
        except ValueError as ex:
            raise ControllerException("Volume field not an integer")
        except Exception as ex:
            raise ex

    def pause(self,dict):
        if 'clientUuid' in dict:
            data=self.connectToDmc(operation="pause",client_uuid=dict['clientUuid'])
            return data
        else:
            raise ControllerException("Select a client Pause")

    def stop(self,dict):
        if 'clientUuid' in dict:
            data=self.connectToDmc(operation="stop",client_uuid=dict['clientUuid'])
            return data
        else:
            raise ControllerException("Select a client stop")
    
    def play(self,dict):
        if 'clientUuid' in dict:
            data=self.connectToDmc(operation="play",client_uuid=dict['clientUuid'])
            return data
        else:
            raise ControllerException("Select a client play")

    #TODO CONTROLLO VALORI MUTE
    def mute(self,dict):
        if all (k in dict for k in ("clientUuid", "value")):
            data=self.connectToDmc(operation="mute", client_uuid=dict['clientUuid'], value=dict['value'])
            return data
        else:
            raise ControllerException("value or clientUuid missing Mute") 

    def startContentFromName(self,dict):
        if all (k in dict for k in ("clientUuid", "name")):
            self.lock.acquire()
            self.lock.release()
            found = False
            i = 0
            while not found:
                for media in self.allContents:
                    serverUuid = media['uuid']
                    for content in media['content']:
                        if content['name'] == dict['name']:
                            print("trovato")
                            found = True
                            finalserverUuid = serverUuid
                            url = content['url']
                            break
                if not found:
                    i+=1
                    print("non trovato")
                    if i > 2:
                        raise ControllerException("live media not found")
                    self.requestDeviceList()
                    self.requestMediaList(scan=False)
            data = self.connectToDmc(operation="start", client_uuid=dict['clientUuid'], url=url, server_uuid=finalserverUuid)
            return data
        else:
            raise ControllerException("value or name missing")          

    def startContentFromUrl(self,dict):
        if all (k in dict for k in ("clientUuid", "url")):
            self.lock.acquire()
            self.lock.release()
            found = False
            i=0
            while not found:
                for media in self.allContents:
                    serverUuid = media['uuid']
                    for content in media['content']:
                        if content['url'] == dict['url']:
                            print("trovato")
                            found = True
                            finalserverUuid=serverUuid
                            break
                if not found:
                    i+=1
                    print("non trovato")
                    if i < 2:
                        raise ControllerException("recorded media not found")
                    self.requestDeviceList()
                    self.requestMediaList(Scan=False)
            data = self.connectToDmc(operation = "start",server_uuid=finalserverUuid,client_uuid=dict['clientUuid'],url=dict['url'])
            return data
        else:
            raise ControllerException("Parameter missing recorded Media")
            
    # def doAction(self,operation,dict):
    #     print(bcolors.HEADER+"{}".format(dict)+bcolors.ENDC)
    #     if operation in ALLOWEDOPERATION:
    #         data={}
    #         if operation == "1":
    #             if all (k in dict for k in ("clientUuid","name")):
    #                 self.lock.acquire()
    #                 self.lock.release()
    #                 found = False
    #                 i=0
    #                 while not found:
    #                     for media in self.liveContents:
    #                         serverUuid = media['uuid']
    #                         for content in media['content']:
    #                             if content['name'] == dict['name']:
    #                                 print("trovato")
    #                                 found = True
    #                                 finalserverUuid=serverUuid
    #                                 url=content['url']
    #                                 break
    #                     if not found:
    #                         i+=1
    #                         print("non trovato")
    #                         if i > 2:
    #                             raise ControllerException("live media not found")
    #                         self.requestDeviceList()
    #                         self.requestMediaList(Scan=False)
    #                 data = self.connectToDmc(operation="start",client_uuid=dict['clientUuid'],url=url,server_uuid=finalserverUuid)
    #             else:
    #                 raise ControllerException("Some parameter are missing")           
    #         elif operation == "2":
    #             if 'clientUuid' in dict:
    #                 data=self.connectToDmc(operation="play",client_uuid=dict['clientUuid'])
    #             else:
    #                 raise ControllerException("Select a client play")
    #         elif operation == "3":
    #             if 'clientUuid' in dict:
    #                 data=self.connectToDmc(operation="stop",client_uuid=dict['clientUuid'])
    #             else:
    #                 raise ControllerException("Select a client stop")
    #         elif operation == "4":
    #             if 'clientUuid' in dict:
    #                 data=self.connectToDmc(operation="pause",client_uuid=dict['clientUuid'])
    #             else:
    #                 raise ControllerException("Select a client Pause")
    #         elif operation == "5":
    #             if all (k in dict for k in ("clientUuid","volume")):
    #                 data=self.connectToDmc(operation="vol",client_uuid=dict['clientUuid'],volume=dict['volume'])
    #             else:
    #                 raise ControllerException("Some Value are missing Volume")
    #         elif operation == "6":
    #             if all (k in dict for k in ("clientUuid","value")):
    #                 data=self.connectToDmc(operation="mute",client_uuid=dict['clientUuid'],value=dict['value'])
    #             else:
    #                 raise ControllerException("Some Value are missing Mute")   
    #         elif operation == "7":
    #             if all (k in dict for k in ("clientUuid","url")):
    #                 self.lock.acquire()
    #                 self.lock.release()
    #                 print(bcolors.OKBLUE+"DEVICE LIST {}".format(self.deviceList)+bcolors.ENDC)
    #                 print(bcolors.OKBLUE+"MEDIA LIST {} {}".format(self.liveContents,self.recordedContents)+bcolors.ENDC)
    #                 found = False
    #                 i=0
    #                 while not found:
    #                     for media in self.allContents:
    #                         serverUuid = media['uuid']
    #                         for content in media['content']:
    #                             if content['url'] == dict['url']:
    #                                 print("trovato")
    #                                 found = True
    #                                 finalserverUuid=serverUuid
    #                                 break
    #                     if not found:
    #                         i+=1
    #                         print("non trovato")
    #                         if i < 2:
    #                             raise ControllerException("recorded media not found")
    #                         self.requestDeviceList()
    #                         self.requestMediaList(Scan=False)
    #                 data = self.connectToDmc(operation = "start",server_uuid=finalserverUuid,client_uuid=dict['clientUuid'],url=dict['url'])
    #             else:
    #                 raise ControllerException("Parameter missing recorded Media")
    #         return data     
    #     else:
    #         raise ControllerException("Operation not recognized")

    def requestDeviceList(self, scan = True):
        try:
            self.lock.acquire()
            if scan:
                self.connectToDmc(operation="scan")
            data = self.connectToDmc(operation="device list")
            if not data:
                print(bcolors.WARNING + "device list is empty"+ bcolors.ENDC)
            else:
                self.deviceList = json.loads(data)
                print(bcolors.OKBLUE+"DEVICE LIST: {}".format(self.deviceList)+bcolors.ENDC)
        except ValueError as ex:
            print("can't convert device list from dmc{}".format(ex)) 
            raise ControllerException("can't get device List")
        finally:
            self.lock.release()
    
    def connectToDmc(self,**kwargs):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.addr,self.port))
            message = {}
            for key, value in kwargs.items():
                message[key]=value
            print(bcolors.FAIL + "sending to DMC {}".format(json.dumps(message))+bcolors.ENDC)
            sock.send(json.dumps(message).encode()+"\n".encode())
            data = (sock.recv(BUFFERSIZE).decode())
            return data
        except socket.error as ex:
            print("Cannot connect to Digital Media Controller {}".format(ex))
            raise ControllerException("Cannot connect to Digital Media Controller")
        finally:
            sock.close()
        
    

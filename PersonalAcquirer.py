import json
import socket
import os
import base64

from utility import bcolors
from PersonalException import PersonalException

BUFFERSIZE = 65535

class PersonalAcquirer(object):

    def __init__(self,addr,port):
        # try:
        #     addr = socket.gethostbyname(addr)
        #     print(addr)
        # except socket.gaierror, err:
        #     print ("cannot resolve hostname:{} , {} ".format(name, err))
        self.addr=addr
        self.port=int(port)
        self.contentList = []
        self.providerList = []
        self.curDir=os.path.dirname(os.path.abspath(__file__))

    def getNameProviderFromId(self,id):
        for provider in self.providerList:
            if provider['idContentProvider']==int(id):
                return provider['name']
        raise PersonalException("Provider non presente PA")

    def getNameContentfromId(self,id):
        for content in self.contentList:
            if content['idContent']==id:
                return content['name']
        raise PersonalException("Content non presente PA")

    def loadImage(self,jsonlist):
        for f in jsonlist:
            newDest = os.path.join(self.curDir,"static","Image",f['name'])
            g = open(newDest, 'wb')
            data = f['image'].replace(' ', '+')
            if len(data) % 4:
                data += '=' * (4 - len(data) % 4)
            g.write(base64.b64decode(data))
            g.close()
            newDest = os.path.join("Image",f['name']+".jpg")
            f['image'] ="/"+os.path.join(os.path.relpath("static"),newDest)
            print("Image Location"+f['image'])
        return jsonlist


    def requestProviderList(self):
        try:
            data=self.connectToPa(operation="provider list")
            providerList = json.loads(data)
            if not (providerList):
                print(bcolors.WARNING + "provider list is empty"+ bcolors.ENDC)
            else:
                self.providerList = self.loadImage(providerList)
                print(bcolors.OKBLUE + "{}".format(self.providerList)+ bcolors.ENDC)
        except ValueError as ex:
            print("can't convert provider from PA{}".format(ex))
            raise PersonalException("can't get provider List")
        except Exception as ex:
            raise PersonalException("{}".format(ex))
    
    def getProviderList(self):
        return self.providerList
    
    def getContentList(self,idContentProvider = None):
        if idContentProvider is None:
            return self.contentList
        else:
            response = []
            for content in self.contentList:
                if content['idContentProvider']==idContentProvider:
                    response.append(content)
            #print(bcolors.HEADER+"{}".format(response)+bcolors.ENDC)
            if response:
                return response
            else:
                raise PersonalException("No content Found")

    def requestContentList(self):
        try:
            data = self.connectToPa(operation="channel list")
            contentList = json.loads(data)
            if not data:
                print(bcolors.WARNING + "content list is empty"+ bcolors.ENDC)
            else:
                self.contentList = self.loadImage(contentList)
                print(bcolors.OKBLUE + "{}".format(contentList)+ bcolors.ENDC)
        except ValueError as ex:
            print("can't convert content list from PA {}".format(ex)) 
            raise PersonalException("can't get content List")
        except Exception as ex:
            raise PersonalException("{}".format(ex))

    #se gli mando dlna lo deve aggiungere al dlna
    def requestProvider(self,idContentProvider, device):
        try:
            if device in ("2", "3"):
                device = "dlna"
            else:
                device = "none"
            print (bcolors.OKGREEN+"Richiesta inviata"+bcolors.ENDC)
            data=self.connectToPa(operation="get content",idContentProvider=idContentProvider,device=device)
            tmp=json.loads(data)
            if tmp['status'] != "success":
                raise PersonalException("{}".format(tmp['status']))
            print (bcolors.OKGREEN+"{}".format(data)+bcolors.ENDC)
            return data
        except PersonalException as ex:
            raise ex
        except Exception as ex:
            raise ex

    #se gli mando dlna lo deve rimuovere solo dal dlna
    def stopProvider(self,idContentProvider,device):
        try:
            if device in ("2", "3"):
                device = "dlna"
            else:
                device = "none"
            print (bcolors.OKGREEN+"Richiesta inviata"+bcolors.ENDC)
            data=self.connectToPa(operation="stop content",idContentProvider=idContentProvider,device=device)
            print (bcolors.OKGREEN+"{}".format(data)+bcolors.ENDC)
            return data
        except PersonalException as ex:
            raise ex
        except Exception as ex:
            raise ex
            

    def recordContent(self,idContent):
        data = self.connectToPa(operation="rec content",idContent=idContent)
        return data

    def connectToPa(self,**kwargs):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.addr,self.port))
            #sock.timeout()
            message = {}
            for key, value in kwargs.items():
                message[key]=value
            print("sending to PA {}".format(json.dumps(message)))
            sock.send(json.dumps(message).encode()+"\n".encode())
            data = ''
            while True:
                tmp =sock.recv(BUFFERSIZE).decode()
                data += tmp.strip()
                if kwargs['operation'] in ("channel list", "provider list"):
                    if data[-1] == ']':
                        break
                else:
                    break
            return data
        except socket.error as ex:
            print("Cannot connect to Personal Acquirer {}".format(ex))
            raise PersonalException("Cannot connect to Personal Acquirer")
        finally:
            sock.close()
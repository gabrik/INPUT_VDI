import sys
import socket
import json
import base64
import threading
import configparser
import traceback
from flask import Flask, render_template, redirect, url_for, flash, request
from utility import bcolors
from ControllerException import ControllerException
from PersonalException import PersonalException
from DigitalMediaController import DigitalMediaController
from PersonalAcquirer import PersonalAcquirer
# 1 smartphone
# 2 DLNA
# 3 entrambi
# 4 registrazioni

# PER IL DMC
# START = 1
# PLAY = 2
# STOP = 3 
# PAUSA = 4
# VOLUP= 5
# VOLDOWN = 6
# MUTE = 7


#device list : [{"port":49152,"name":"INPUT DMS: 1","host":"172.16.0.39","type":"MediaServer","uuid":"898f9738-d930-4db4-a3cf-dc4a3ea8caff"},{"port":2870,"name":"Smart TV","host":"172.16.0.37","type":"MediaRenderer","uuid":"13f91d82-4356-1a20-808d-784561139eda"}]
#media list : [{"uuid":"898f9738-d930-4db4-a3cf-dc4a3ea8caff","content":[{"name":"Family","url":"http://172.16.0.39:49152/web/2.mp4"},{"name":"sony_eye_candy","url":"http://172.16.0.39:49152/web/3.mpg"}]}]
#contentprovider list: [{'idContentProvider': 1, 'name': 'InputProvider1', 'image': '/static/Image/InputProvider1.jpg'}, {'idContentProvider': 2,'name': 'InputProvider2', 'image': '/static/Image/InputProvider2.jpg'}]
#channel list: [{'idContentProvider': 1, 'length': '02:00:00', 'description': 'Cartone animato per bambini', 'image': '/static/Image/Inpu
# tContent1.jpg', 'name': 'InputContent1', 'idContent': 1, 'startingTime': '2017-06-21 16:40:56'}, {'idContentProvider': 2,
# 'length': '02:00:00', 'description': 'Sport ', 'image': '/static/Image/InputContent2.jpg', 'name': 'InputContent2', 'idCon
# tent': 2, 'startingTime': '2017-06-21 16:40:56'}, {'idContentProvider': 1, 'length': '02:00:00', 'description': 'Videogioc
# hi', 'image': '/static/Image/InputContent3.jpg', 'name': 'InputContent3', 'idContent': 3, 'startingTime': '2017-06-21 18:4
# 0:56'}]
#/dmc/getDevices   dispositivi
#/dmc/getContents   contenuti



app = Flask(__name__)
BUFFERSIZE = 65535
app.secret_key = 'chiavesupersegreta'
dmc = DigitalMediaController
pa = PersonalAcquirer
currentChannels = []
ALLOWEDACTION = ("1", "2", "3", "4", "5", "6", "7")
"""
"""

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/Virtualdecoderinterface/')
# def Virtualdecoderinterface():
#     return render_template('Virtualdecoderinterface.html', providerList=pa.getProviderList(),
#                            currentChannel=currentChannels)

@app.route('/Virtualdecoderinterface/getProviders/')
def getProviders():
    mobile = request.args.get('mobile', '0')
    if mobile == '0':
        pass
    else:
        return json.dumps(pa.getProviderList())

# scan = 1 da effettuare la scansione
# scan = 0 da non effettuare la scansione
@app.route('/Virtualdecoderinterface/dmc/getDevices/')
def getDevices():
    try:
        mobile = request.args.get('mobile', "0")
        scan = request.args.get('scan','0')
        if scan == "1":
            dmc.requestDeviceList(scan = True)
        deviceList = dmc.getDeviceList()
        if mobile == "0":
            #TODO browser
            pass
        else:
            return json.dumps(deviceList)
    except ControllerException as ex:
            return json.dumps({"status":"{}".format(ex)})
    except Exception as ex:
            return json.dumps({"status":"{}".format(ex)})

#recorded = 1 solo i media registrati
#recorded = 0 solo i media live
#recorded = 2 TUTTI
#scan = 1 effettuare lo scan
#scan = 0 non effettuare lo scan
@app.route('/Virtualdecoderinterface/dmc/getContents/')
def getContents():
    try:
        mobile = request.args.get('mobile', "0")
        recorded = request.args.get('recorded', None)
        scan = request.args.get('scan','0')
        if scan == "1":
            dmc.requestMediaList(scan=scan)
        if recorded is None:
            if mobile == "0":
                #TODO browser
                pass
            else:
                raise Exception("recorded is missing on getContents")
        if recorded == "0":
            mediaList = dmc.getLiveContents()
        elif recorded == "1":
            mediaList = dmc.getRecordedContents()
        elif recorded == "2":
            mediaList = dmc.getAllContents()
        else:
             raise Exception("recorded must be 0 1 2")
        if mobile == "0":
            #TODO browser
            pass
        else:
            return json.dumps(mediaList)
    except ControllerException as ex:
            return json.dumps({"status":"{}".format(ex)})
    except Exception as ex:
            return json.dumps({"status":"{}".format(ex)})

# @app.route('/Virtualdecoderinterface/dmc/doAction/')
# def doAction():
#     mobile = request.args.get('mobile', "0")
#     action = request.args.get("action","0")
#     try:
#         if action == "1":
#             #try:   
#                 url = request.args.get('url',None)
#                 if url:
#                     #ACTION 7 è per i contenuti live non viene mandato il nome del provider ma l'url del video
#                     action = "7"
#                     params={"url":url,"clientUuid":request.args.get("uuid")}
#                     data = dmc.doAction(action,params)  
#                 else:        
#                     name = pa.getNameProviderFromId(request.args.get("id_content"))
#                     params={"name":name,"clientUuid":request.args.get("uuid")}
#                     data = dmc.doAction(action,params)   
#         else:
#             params = dict(request.args)
#             #Passaggio da multidict a dict
#             for key,elemen in params.items():
#                 params[key]=elemen[0]
#             params['clientUuid'] = params.pop('uuid')
#             data=dmc.doAction(action,params)
#         if mobile == "0":
#             #TODO browser
#             pass
#         else:
#             return json.dumps(data)
#     except ControllerException as ex:
#             traceback.print_exc()
#             print ("status {}".format(ex))
#             return json.dumps({"status":"{}".format(ex)})
#     except Exception as ex:
#             traceback.print_exc()
#             print ("status {}".format(ex))
#             return json.dumps({"status":"{}".format(ex)})

# PER IL DMC
# START = 1
# PLAY = 2
# STOP = 3 
# PAUSA = 4
# VOL = 5
# MUTE = 6
@app.route('/Virtualdecoderinterface/dmc/doAction/')
def doAction():
    mobile = request.args.get('mobile', "0")
    action = request.args.get("action", "0")
    params = dict(request.args) 
    #Passaggio da multidict a dict
    for key, elemen in params.items():
        params[key] = elemen[0]
    params['clientUuid'] = params.pop('uuid')
    try:
        if action in ALLOWEDACTION:
            if action == "1":
                url = request.args.get("url",None)
                if url:
                    data = dmc.startContentFromUrl(params)
                else:
                    data = dmc.startContentFromName(params)
            elif action == "2":
                data = dmc.play(params)
            elif action == "3":
                data = dmc.stop(params)
            elif action == "4":
                data = dmc.pause(params)
            elif action == "5":
                data = dmc.changeVolume(params)
            elif action == "6":
                data = dmc.mute(params)
            elif action == "7":
                data = dmc.startContentFromUrl(params)
            if mobile == "1":
                return data
            else:
                #INSERIRE QUI PAGINE BROWSER
                pass            
        else:
            raise Exception("Controller Operation not Allowed")
    except ControllerException as ex:
            traceback.print_exc()
            print ("status {}".format(ex))
            return json.dumps({"status":"{}".format(ex)})
    except Exception as ex:
            traceback.print_exc()
            print ("status {}".format(ex))
            return json.dumps({"status":"{}".format(ex)})


@app.route('/Virtualdecoderinterface/getChannels/<int:providerId>/')
def getChannels(providerId):
    mobile = request.args.get('mobile', "0")
    try:
        provider_nome=pa.getNameProviderFromId(providerId)
        contentList = pa.getContentList(idContentProvider=providerId)
        if mobile == "0":
            pass
            # return render_template('getChannels.html', providerList=pa.getProviderList(),
            #                    currentChannel=currentChannel, channels=pa.getContentList(),
            #                    provider_nome=provider_nome)
        else:
            return json.dumps(contentList)
    except PersonalException as ex:
        if mobile == "0":
            flash("<b>Error  <b> {}".format(ex), "errors")
            pass
            #return redirect(url_for('Virtualdecoderinterface'))
        else:
            return json.dumps({"status":"{}".format(ex)})
    except Exception as ex:
        if mobile == "0":
            flash("<b>Error  <b> {}".format(ex), "errors")
            pass
            #return redirect(url_for('Virtualdecoderinterface'))
        else:
            return json.dumps({"status":"{}".format(ex)})


@app.route('/Virtualdecoderinterface/getStream/<int:idContentProvider>/')
def getStream(idContentProvider):
    mobile = request.args.get('mobile', "0")
    device = request.args.get('device', "2")
    try:
        if currentChannels:
            for channel in currentChannels:
                #provider già in ricezione dal vSTB
                if idContentProvider == channel['idContentProvider']:
                    #richieste multiple gli rinvio le informazioni
                    if channel['device'] == device:
                        if mobile == "0":
                            flash('<b>Success</b> Alredy viewing the video', 'success')
                            #return redirect(url_for('Virtualdecoderinterface'))
                            pass
                        else:
                            if device in ("1", "3"):
                                url = "http://{}:8090/{}.mp4".format(pa.addr, channel['name'])
                            else:
                                url = "None"
                        return json.dumps({"status":"success", "url":url})
                    #richiesta di cambio dispositivo
                    else:
                        if device == "4":
                            break
                        olddevice=channel['device']
                        channel['device']=device
                        #aveva dlna vuole dlna+mobile
                        if olddevice == "2" and device == "3":
                            url = "http://{}:8090/{}.mp4".format(pa.addr, channel['name'])
                        #aveva mobile vuole dlna
                        elif olddevice == "1" and device == "2":
                            data = pa.requestProvider(channel['idContentProvider'],device)
                            url = "None"
                        elif olddevice == "1" and device == "3":
                            data = pa.requestProvider(channel['idContentProvider'],device)
                            url = "http://{}:8090/{}.mp4".format(pa.addr, channel['name'])
                        elif olddevice in ("2","3") and device == "1":
                            data = pa.stopProvider(channel['idContentProvider'],olddevice)
                            url = "http://{}:8090/{}.mp4".format(pa.addr, channel['name'])
                        elif olddevice == "3" and device == "2":
                            url="None"
                        else:
                            raise Exception("Device switch error")
                        print(bcolors.HEADER+"{}".format(currentChannels)+bcolors.ENDC)
                        return json.dumps({"status":"success", "url":url})
        #SE SIAMO QUI NON HO GIà richiesto il video
        if device != "4":
            data = json.loads(pa.requestProvider(idContentProvider,device))
            threading.Thread(target=dmc.requestMediaList).start()
            name = pa.getNameProviderFromId(idContentProvider)
            channel = {}
            channel['idContentProvider'] = idContentProvider
            channel['device'] = device
            channel['name'] = name
            currentChannels.append(channel)
        elif device == "4": 
            data = json.loads(pa.recordContent(idContentProvider))
        else:
            raise Exception("Operation not supported")
        if mobile == "0":
            flash('<b>Success</b> Use any DLNA player to watch the channel', 'success')
            pass
            #return redirect(url_for('Virtualdecoderinterface'))
        else:
            if device in ("1", "3"):
                data['url'] = "http://{}:8090/{}.mp4".format(pa.addr,channel['name'])
            else:
                data['url'] = "None"
            print(bcolors.OKGREEN+"Sending  to client {}".format(data)+bcolors.ENDC)
            print(bcolors.HEADER+"{}".format(currentChannels)+bcolors.ENDC)
            return json.dumps(data)
    except PersonalException as ex:
        if mobile == "0":
            traceback.print_exc()
            flash("<b>Error  <b> {}".format(ex), "errors")
            #return redirect(url_for('Virtualdecoderinterface'))
            pass
        else:
            traceback.print_exc()
            return json.dumps({"status":"{}".format(ex),"url":"None"})
    except Exception as ex:
        if mobile == "0":
            traceback.print_exc()
            flash("<b>Error  <b> {}".format(ex), "errors")
            pass
            #return redirect(url_for('Virtualdecoderinterface'))
        else:
            traceback.print_exc()
            return json.dumps({"status":"{}".format(ex),"url":"None"})

@app.route('/Virtualdecoderinterface/stopStream/<int:idContentProvider>/')
def stopStream(idContentProvider):
    try:
        mobile = request.args.get('mobile', '0')
        for channel in currentChannels:
            if channel['idContentProvider'] == idContentProvider:
                data=pa.stopProvider(idContentProvider, "1")
                currentChannels.remove(channel)
                print(bcolors.HEADER+"{}".format(currentChannels)+bcolors.ENDC)
                if mobile == "0":
                    flash("<b>Success  <b> provider found", "success")
                    pass
                    #return redirect(url_for('Virtualdecoderinterface'))
                else:
                    return json.dumps({"status":"success","url":"None"})
        raise Exception("No content to stop")
    except PersonalException as ex:
        if mobile == "0":
            traceback.print_exc()
            flash("<b>Error  <b> {}".format(ex), "errors")
            return redirect(url_for('Virtualdecoderinterface'))
        else:
            traceback.print_exc()
            return json.dumps({"status":"{}".format(ex),"url":"None"})
    except Exception as ex:
        if mobile == "0":
            traceback.print_exc()
            flash("<b>Error  <b> {}".format(ex), "errors")
            pass
            #return redirect(url_for('Virtualdecoderinterface'))
        else:
            traceback.print_exc()
            return json.dumps({"status":"{}".format(ex),"url":"None"})        
     

@app.errorhandler(404)
def page_not_found(ex):
    if (request.args.get('mobile') == "1"):
        return (json.dumps({"status":"Error 404"}))
    else:
        flash("<b>Error 404 <b> The page you're looking for doesn't exists: {}".format(ex), "errors")
        pass
        #return redirect(url_for('Virtualdecoderinterface'))

@app.errorhandler(500)
def internal_error(ex):
     if (request.args.get('mobile') == "1"):
        return (json.dumps({"status":"Error 500"}))
     else:
        flash("<b>Error 500 <b> Oops an error occured try again later: {} ".format(ex), "errors")
        pass
        #return redirect(url_for('Virtualdecoderinterface'))

if __name__ == "__main__":
    if len(sys.argv) == 2:
        config=configparser.ConfigParser()
        config.read(sys.argv[1])
        if ("DigitalMediaController") in config.sections():
            print(bcolors.OKGREEN+"there is a controller on the network"+bcolors.ENDC)
            dmc = DigitalMediaController(config['DigitalMediaController']['address'], config['DigitalMediaController']['port'])
            dmc.requestDeviceList(scan=False)
            dmc.requestMediaList(scan=False)
        else: 
            print (bcolors.WARNING+"There is no controller on the network"+ bcolors.ENDC)
            dmc=DigitalMediaController('0.0.0.0','0')
        if ("PersonalAcquirer") in config.sections():
            pa = PersonalAcquirer(config['PersonalAcquirer']['address'],config['PersonalAcquirer']['port'])
            print(bcolors.OKGREEN+"There is a personal acquirer on the network"+bcolors.ENDC)
            pa.requestProviderList()
            pa.requestContentList()
            
        else:
            print(bcolors.FAIL+" ERROR There is no personal acquirer on the network"+bcolors.ENDC)
            sys.exit(-1)
           
        app.run(host="0.0.0.0",debug=True)
    else:
        print(bcolors.FAIL +"Usage {} configfile".format(sys.argv[0])+ bcolors.ENDC)
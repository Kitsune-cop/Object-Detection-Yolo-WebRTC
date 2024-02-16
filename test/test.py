import asyncio
import json
import logging
import requests
import cv2
from datetime import datetime
import cv2
from aiortc import (RTCPeerConnection, RTCSessionDescription, VideoStreamTrack)
from av import VideoFrame 


dataChannelLog = ""
iceConnectionLog = "ice-connection-state"
iceGatheringLog = "ice-gathering-state"
signalingLog = "signaling-state"
SIGNALING_SERVER_URL = "http://127.0.0.1:8443"
msg_data = {}

logger = logging.getLogger("pc")

pc = None
msg = ""
dc = None
pc_id = "Client1"

class VideoCapturer(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)  # Change 0 to 1 if using an external USB webcam
        self.picture_id = 0 

    async def recv(self):
        while(self.cap.isOpened()): 
            ret, frame = self.cap.read()
            pts, time_base = await self.next_timestamp()

            if ret:
                video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
                video_frame.pts = pts
                video_frame.time_base = time_base
                self.picture_id += 1  # Increment picture_id for each frame
                
                return video_frame
            else:
                return None
        self.cap.release() 

async def createConnection():
    """
    create RTC connection
    """

    pc = RTCPeerConnection()

    async def on_icegatheringstatechange():
        pc.iceGatheringState
        print(iceGatheringLog +' -> '+ pc.iceGatheringState)
    pc.on("icegatheringstatechange", on_icegatheringstatechange)

    async def on_iceconnectionsstatechange():
        pc.iceConnectionState
        print(iceConnectionLog +' -> '+ pc.iceConnectionState )
        if pc.connectionState == "failed":
            await pc.close()
    pc.on("iceconnectionstatechange", on_iceconnectionsstatechange)

    async def on_signalingstatechange():
        pc.signalingState
        print(signalingLog +' -> '+ pc.signalingState)
    pc.on("signalingstatechange", on_signalingstatechange)

    # Add video stream track
    video_track = VideoCapturer()
    pc.addTrack(video_track)

    return pc

async def sendOffer(message):
    response = requests.post(SIGNALING_SERVER_URL + '/offer', json=message)
    assert response.status_code == 200

async def negotiate(pc):
    try:
        global msg
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        while pc.iceGatheringState != 'complete':
            await asyncio.sleep(0.1)

        offer = pc.localDescription
        message = {
            'id':pc_id,
            'sdp': offer.sdp,
            'type': offer.type,
            'msg': 'Hello JS from python'
        }
        await sendOffer(message)

        while True:
            resp = requests.get(SIGNALING_SERVER_URL + "/get_answer")
            if resp.status_code == 503:
                print("Answer not ready, wait for Answer")
                await asyncio.sleep(1)
            elif resp.status_code == 200:
                data = resp.json()
                msg = data["msg"]

                if data["type"] == "answer":
                    rd = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
                    await pc.setRemoteDescription(rd)
                    print(pc.remoteDescription)
                    
                    while True:
                        await asyncio.sleep(1)
                else:
                    print("Wrong type")
                break

            print("Get answer -> ",resp.status_code)

    except Exception as e:
        print(f"Error during negotiation: {e}")
        
def current_stamp(time_start):
    now = datetime.now()
    current_time = now.strftime("%S")
    if time_start == None:
        time_start = current_time
        return 0;
    else :
        return int(current_time) - int(time_start)

async def setInterval(dc):
    try:
        num = 0
        while  True:
            message = 'ping ' + str(num)
            ChannelLog = dc.label + ' > ' + message + '\n'
            print(ChannelLog)
            dc.send(message)
            num+=1
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Caught exception: {e}")

async def main():
    pc = await createConnection()

    time_start = 0

    dc = pc.createDataChannel("chat")

    dataChannelLog = dc.label

    async def on_message(message):
        ChannelLog = dataChannelLog+' < ' + message + '\n'
        print(ChannelLog)
        if message[0:4] == "pong":
            elapsed_ms = current_stamp(time_start) - int(message[5:]);
            ChannelLog = dataChannelLog+' RTT ' + str(elapsed_ms) + ' ms\n';
            print(ChannelLog)
            ChannelLog = f"{dataChannelLog} ----- {msg} ----- \n";
            print(ChannelLog)
    dc.on("message", on_message)

    async def on_open():
        ChannelLog = dataChannelLog+' - open\n'
        print(ChannelLog)
        dc.send(msg)
        asyncio.ensure_future(setInterval(dc))
    dc.on("open", on_open)

    async def on_close():
        ChannelLog = dataChannelLog +' - close\n'
        print(ChannelLog)
    dc.on("close", on_close) 

    await negotiate(pc)

asyncio.run(main())
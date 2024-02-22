import asyncio
import json
import logging
import requests
from datetime import datetime
import cv2
from aiortc import (RTCPeerConnection, RTCSessionDescription, VideoStreamTrack)
from av import VideoFrame 
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors


dataChannelLog = ""
iceConnectionLog = "ice-connection-state"
iceGatheringLog = "ice-gathering-state"
signalingLog = "signaling-state"
SIGNALING_SERVER_URL = "http://127.0.0.1:8443"

logger = logging.getLogger("pc")

pc = None
msg = ""
dc = None
pc_id = "Client1"
label_count = {}

class VideoCapturer(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)  # Change 0 to 1 if using an external USB webcam
        self.picture_id = 0 
        self.model = YOLO("yolov8n.pt")

    async def draw_boxes(self,frame, boxes):
        """Draw detected bounding boxes on image frame"""

        # Create annotator object
        global label_count
        counts = {}
        annotator = Annotator(frame)
        for box in boxes:
            class_id = box.cls
            class_name = self.model.names[int(class_id)]
            coordinator = box.xyxy[0]
            confidence = box.conf
            conf_label = float("{:.2f}".format(confidence.item()))
            label = f"{class_name} {conf_label}"

            if class_name not in counts:
                counts[class_name] = 0
            counts[class_name] += 1
            label_count = str(counts)

            # Draw bounding box
            annotator.box_label(box=coordinator, label=label, color=colors(class_id, True))

        return annotator.result()
    
    async def detect_motorcycle(self,frame):
        """ Detect motorcycle from image frame """
        confidence_threshold = 0.5
        results = self.model.predict(frame, conf=confidence_threshold, verbose=False)

        for result in results:
            for box in result.boxes:
                class_id = box.cls
                class_name = self.model.names[int(class_id)]
            frame = await self.draw_boxes(frame, result.boxes)

        return frame

    async def recv(self):
        while(self.cap.isOpened()): 
            ret, frame = self.cap.read()
            pts, time_base = await self.next_timestamp()
            frame_result = await self.detect_motorcycle(frame)

            if ret:
                video_frame = VideoFrame.from_ndarray(frame_result, format="bgr24")
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
        print(iceGatheringLog +' --> '+ pc.iceGatheringState)
    pc.on("icegatheringstatechange", on_icegatheringstatechange)

    async def on_iceconnectionsstatechange():
        pc.iceConnectionState
        print(iceConnectionLog +' --> '+ pc.iceConnectionState )
        if pc.connectionState == "failed":
            await pc.close()
            loop = asyncio.get_running_loop()
            loop.stop()
    pc.on("iceconnectionstatechange", on_iceconnectionsstatechange)

    async def on_signalingstatechange():
        pc.signalingState
        print(signalingLog +' --> '+ pc.signalingState)
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
        message_data = {
            'id':pc_id,
            'sdp': offer.sdp,
            'type': offer.type,
            'msg': 'Send via data channel from python'
        }
        await sendOffer(message_data)

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
                    
                    while True:
                        await asyncio.sleep(1)
                else:
                    print("Wrong type")
                break

            print("Get answer: ",resp.status_code)

    except Exception as e:
        print(f"Error during negotiation: {e}")

async def setInterval(dc, pc):
    try:
        num = 0
        while  True:
            message = 'ping ' + str(num)
            ChannelLog = dc.label + ' --> ' + message + '\n'
            print(ChannelLog)
            dc.send(message)
            num+=1
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Caught exception: {e}")
        # dc.close()
        await pc.close()
        loop = asyncio.get_running_loop()
        loop.stop()
        # run()

async def main():
    pc = await createConnection()

    dc = pc.createDataChannel("data chitchat")

    dataChannelLog = dc.label

    greeting_msg = ['Hello', 'Sup', 'Howdy', 'Hi', 'Hola', 'Greetings', 'Ohaiyo']

    bye_msg = ['Good bye','Bye','Bye Bye','Good night','Sayonara']

    async def on_message(message):
        dc.send(f"Detection: {label_count[1:-1]}")

        if message in greeting_msg:
            dc.send("Greeting accept")
            ChannelLog = dc.label + ' --> Greeting accept \n'
            print(ChannelLog)
        elif message in bye_msg:
            dc.send("Bye Bye >_<")
            ChannelLog = dc.label + ' --> Bye Bye >_< \n'
            print(ChannelLog)
            dc.close()
            pc.close()
        else:
            dc.send("Sorry not understand")
            ChannelLog = dc.label + ' --> Sorry not understand \n'
            print(ChannelLog)

        ChannelLog = dataChannelLog+' <-- ' + message + '\n'
        print(ChannelLog)
        ChannelLog = f"{dataChannelLog} ----- {msg} ----- \n";
        print(ChannelLog)
    dc.on("message", on_message)

    async def on_open():
        ChannelLog = dataChannelLog+' -- open\n'
        print(ChannelLog)
        dc.send("Hi!  I'm a from python side.\n");
        ChannelLog = dc.label + ' --> Hi!  I\'m a from python side. \n'
        print(ChannelLog)
        asyncio.ensure_future(setInterval(dc, pc))
    dc.on("open", on_open)

    async def on_close():
        ChannelLog = dataChannelLog +' -- close\n'
        print(ChannelLog)
    dc.on("close", on_close) 

    await negotiate(pc)

# asyncio.run(main())
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
except RuntimeError as e:
    # Log the event loop error
    print(f"Error: {e}")
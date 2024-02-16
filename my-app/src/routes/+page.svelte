<script lang="ts">
    
    import {onMount} from 'svelte';
    import axios from 'axios';

    let id = '',
        offerSdp = '',
        offerType = '',
        answerSdp = '',
        answerType = '',
        msg = '',
        data_text = '';
    let video;
    // let canvas;

    onMount(async () => {
		const data = await getOffer();
        console.log(data.status);
        // const Obj = JSON.parse(data);
        id = data.id;
        offerSdp = data.sdp;
        offerType = data.type
        msg = data.msg;

        await createConnection();      
        const ans = await sendAnswer();
        console.log(ans)
        video = document.getElementById("video");
	});

    const getOffer = async () => {
        let res = await axios({
                        method: 'get',
                        url: 'http://127.0.0.1:8443/get_offer'
                    }).then(function (response) {
                        return  response.data;
                    })
                    .catch(function (error) {
                    console.log(error.toJSON());
                    });
        return res
    };

    const sendAnswer = async () => {
        let response = await axios({
                                    method: 'post',
                                    url:'http://127.0.0.1:8443/answer',
                                    headers: {
                                                'Content-Type': 'application/json'
                                            },
                                    data: {
                                            'id':'Client02',
                                            'type': answerType,
                                            'sdp': answerSdp,
                                            'msg': 'Hello from JS side'
                                        }
                                }).then(function (response) {
                                    return  response.data;
                                })
                                .catch(function (error) {
                                console.log(error.toJSON());
                                });
        return response
    }
    
    const createConnection = async () => {
       // Create the RTCSessionDescription object using the received data
            const message = Object({'type':offerType,'sdp':offerSdp})
            const sessionDesc = new RTCSessionDescription(message);

            let pc = new RTCPeerConnection();

            pc.ondatachannel = (event) => {
                const channel = event.channel;
                channel.onopen = (event) => {
                    channel.send("Hi back!");
                };
                channel.onmessage = (event) => {
                    const message = event.data;
                    if (typeof message === 'string' && message.startsWith("ping")) {
                        channel.send("pong" + message.slice(4)); // Send "pong" response
                    }
                    data_text = message;
                };
            };

            pc.ontrack = async (evt) => {
                video = document.querySelector("video");
                const videoTrack = evt.streams[0].getVideoTracks();
                console.log("videoTrack", videoTrack);
                console.log(`using video device : ${videoTrack[0].label}`);
                video.srcObject = evt.streams[0];
            };

            pc.oniceconnectionstatechange = () => {
                console.log('Connection state is ' + pc.connectionState);
                if (pc.connectionState === "failed") {
                    pc.close();
                }
            };

            pc.setRemoteDescription(sessionDesc);

            const answer = pc.createAnswer()
                .then((answer) => pc.setLocalDescription(answer))
                .then(() => {
                    const local = pc.localDescription;
                    answerSdp = local?local.sdp:"";
                    answerType = local?local.type:"";
                    return local;
                });
            
            return answer;
    };

</script>
<h1>Welcome to WebRTC Demo</h1>

<video id="video" playsinline autoplay bind:this={video} width="640" height="480">
    <track kind="captions">
</video>

<h3>Data-Channel</h3>
<p>{data_text}</p>
<p>{msg}</p>

<h3>Offer-Type</h3>
<p>{offerType}</p>
<h3>Offer-SDP</h3>
<p>{offerSdp}</p>

<h3>Answer-Type</h3>
<p>{answerType}</p>
<h3>Answer-SDP</h3>
<p>{answerSdp}</p>



<script lang="ts">
    import {onMount} from 'svelte';
    import axios from 'axios';

    let id = '',
        offerSdp = '',
        offerType = '',
        answerSdp = '',
        answerType = '',
        msg = '';
    let video;
    let msg_button = '';
    let offer_status

    onMount(async () => {
        const offer = await getOffer();
        offer_status = offer.status
		const data = offer.data;
        id = data.id;
        offerSdp = data.sdp;
        offerType = data.type
        msg = data.msg;

        await createConnection(); 
        await sendAnswer();

        video = document.getElementById("video");

	});

    const getOffer = async () => {
        let res = await axios({
                        method: 'get',
                        url: 'http://127.0.0.1:8443/get_offer'
                    }).then(response => {
                        return  response;
                    }).catch(error => {
                        const status = error.response.status;
                        const detail = error.response.data.detail
                        alert(status+" : Offer "+detail);
                        document.getElementById("herror").textContent = "Please check python side is send an offer and try again!!"
                        console.error(status+" : Offer "+detail);
                        return error.response
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
                                            'msg': 'Send via data channel from Svelte side'
                                        }
                                }).then(response => {
                                    return  response.data;
                                }).catch(error => {
                                    const status = error.response.status;
                                    const detail = error.response.data.detail
                                    alert(status+" : Answer "+detail);
                                    console.error(status+" : Answer "+detail);
                                    return error.response
                                });
        return response
    }
    
    const createConnection = async () => {
       // Create the RTCSessionDescription object using the received data
            const message = Object({'type':offerType,'sdp':offerSdp})
            const sessionDesc = new RTCSessionDescription(message);

            let pc = new RTCPeerConnection();

            pc.ondatachannel = async(event) => {
                const channel = event.channel;
                channel.onopen = async(event) => {
                    channel.send("Hi back!");
                };
                channel.onmessage = (event) => {
                    const message = event.data;
                    let data_text = document.getElementById("data-channel");
                    let ping = '';
                    let recv_msg = '';
                    
                    if (typeof message === 'string' && message.startsWith("ping")) {
                        // data_text.textContent += channel.label+' <-- '+message+'\n';
                        ping = message;
                        data_text.textContent += '---------------------------------\n';
                        data_text.textContent += channel.label+' <-- '+ping+'\n';
                        data_text.textContent += '---------------------------------\n';
                        channel.send(msg_button);
                    }else{
                        recv_msg = message;
                        data_text.textContent += channel.label+' --> '+msg_button+'\n';
                        data_text.textContent += channel.label+' <-- '+recv_msg+'\n';
                        data_text.textContent += 'Receive Log: ----- '+msg+' ----- \n';
                    }
                    
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

    const on_click = () => {
        const text = document.getElementById("text")?.value;
        msg_button = text;
        console.log(msg_button);
    }

</script>
<style>
    .container{
        margin: 80px;
    }
    .main {
        display: grid;
        grid-template-columns: auto auto;
    }
    .main .dc{
        margin-bottom: 30px;
    }    
    .text_head {
        color: blue;
    }
    .send-text{
        margin-bottom: 30px;
    }
    .sdp{
        display: grid;
        grid-template-columns: auto auto;
    }
    .offer{
        border-style: solid;
        border-width: 3px;
        border-color: greenyellow;
        width: 840px;
    }

    .answer{
        border-style: solid;
        border-width: 3px;
        border-color: greenyellow;
        width: 840px;
    }
    h1 {
        color: blue;
    }
    #video {
        border-style: solid;
        border-width: 3px;
        border-color: red;
        width: 1280px;
        height: 720px;
    }

    #data-channel{
        border-style: solid;
        border-width: 3px;
        border-color: red;
        width: 400px;
        height: 660px;
        overflow-y: auto;
    }
    #sdp{
        height: 400px;
        overflow-y: auto;
    }

    #text{
        width: 400px;
    }
</style>

<div class="container">
    <h2 style="color:red" id="herror"> </h2>
    <h1>Welcome to WebRTC Demo</h1>
    <div class="main">
        <div class="vid">
            <video id="video" playsinline autoplay bind:this={video}><track kind="captions"></video>
        </div>

        <div class="dc">
            <h3 class="text_head">Data-Channel</h3>
            <pre id="data-channel"></pre>
        </div>

        <div class="send-text">
            <textarea id="text"></textarea>
            <button color="blue" on:click={on_click}>Send</button>
        </div>
    </div>

    <div class="sdp">
        <div class="offer">
            <h3 class="text_head">Offer-SDP</h3>
            <pre id="sdp">{offerSdp}</pre>
        </div>

        <div class="answer">
            <h3 class="text_head">Answer-SDP</h3>
            <pre id="sdp">{answerSdp}</pre>
        </div>
    </div>
</div>






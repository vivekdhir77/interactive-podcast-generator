import React, { useState } from 'react';

const TranscriptionComponent = () => {
    const [transcription, setTranscription] = useState('');
    const [recording, setRecording] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState(null);

    const startTranscription = async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        let audioChunks = [];

        recorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        recorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const formData = new FormData();
            formData.append('file', audioBlob, 'audio.webm');

            try {
                const response = await fetch('http://localhost:8000/transcribe/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        // Ensure correct content type is set
                        'Accept': 'application/json',
                    },
                });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                console.log(data)
                if (data.transcription) {
                    setTranscription(`Transcription: ${data.transcription}`);
                } else if (data.detail) {
                    setTranscription(`Error: ${data.detail}`);
                }
            } catch (error) {
                console.error('Fetch error:', error);
                setTranscription(`Error: ${error.message}`);
            }

            setRecording(false);
        };

        recorder.start();
        setMediaRecorder(recorder);
        setRecording(true);
        setTranscription('Recording...');
    };

    const stopTranscription = () => {
        if (mediaRecorder) {
            mediaRecorder.stop();
        }
    };

    return (
        <div>
            <h1>Speech Recognition</h1>
            <button onClick={startTranscription} disabled={recording}>
                Start Recording
            </button>
            <button onClick={stopTranscription} disabled={!recording}>
                Stop Recording and Transcribe
            </button>
            <p>{transcription}</p>
        </div>
    );
};

export default TranscriptionComponent;

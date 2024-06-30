import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from fastapi import WebSocket
from fastapi.responses import JSONResponse
import speech_recognition as sr
import io
from pydub import AudioSegment

load_dotenv()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", verbose=True, temperature=0.5, google_api_key=os.getenv("GOOGLE_API_KEY"))

class PodcastRequest(BaseModel):
    topic: str
    duration: int

class QuestionRequest(BaseModel):
    question: str

conversation = []
current_host = None

def assign_roles(topic):
    conversationalist = Agent(
        name="Engaging Host",
        role="Engaging Conversationalist",
        goal=f"Gradually introduce the topic of {topic}, explain its relevance, and facilitate an engaging discussion.",
        backstory="A charismatic podcast host known for making complex topics accessible and entertaining for a wide audience.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    expert = Agent(
        name="Expert Host",
        role="Topic Expert",
        goal=f"Provide an overview of {topic}, gradually increasing in depth. Explain the importance of the topic before delving into more complex aspects.",
        backstory=f"A renowned expert in {topic} with a gift for breaking down complicated ideas into easy-to-understand explanations.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    return conversationalist, expert

async def generate_podcast_content(topic: str, duration: int):
    global conversation, current_host
    conversation = []
    conversationalist, expert = assign_roles(topic)
    start_time = asyncio.get_event_loop().time()
    end_time = start_time + (duration * 60)

    # Introduction phase
    intro_task = Task(
        description=f"Welcome the audience and introduce the topic of {topic}. Explain why this topic is relevant and interesting.",
        agent=conversationalist,
        expected_output="A welcoming introduction that sets the stage for the podcast and explains the topic's relevance"
    )
    crew = Crew(agents=[conversationalist], tasks=[intro_task])
    intro_response = crew.kickoff()
    conversation.append(f"Engaging Host: {intro_response}")
    yield f"Engaging Host: {intro_response}\n"

    # Expert overview
    overview_task = Task(
        description=f"Provide a high-level overview of {topic}. Explain its basic concepts and why it's important.",
        agent=expert,
        expected_output="A clear, beginner-friendly overview of the topic that sets the foundation for deeper discussion"
    )
    crew = Crew(agents=[expert], tasks=[overview_task])
    overview_response = crew.kickoff()
    conversation.append(f"Expert Host: {overview_response}")
    yield f"Expert Host: {overview_response}\n"

    # Main discussion
    while asyncio.get_event_loop().time() < end_time:
        for host, name in [[conversationalist, "Claudio"],  [expert,"Ezio"]]:
            current_host = host
            task = Task(
                description=f"Continue the discussion on {topic}, increasing in depth. Respond to previous comments if applicable. Current conversation: {conversation}",
                agent=host,
                expected_output="An engaging paragraph that continues the discussion while ensuring the conversation remains accessible"
            )
            crew = Crew(agents=[host], tasks=[task])
            response = crew.kickoff()
            conversation.append(f"{name}: {response}")
            yield f"{name}: {response}\n"

            if asyncio.get_event_loop().time() >= end_time:
                break

    yield "END_OF_PODCAST"

@app.post("/generate-podcast")
async def generate_podcast(request: PodcastRequest):
    return EventSourceResponse(generate_podcast_content(request.topic, request.duration))

@app.post("/ask-question")
async def ask_question(request: QuestionRequest):
    global conversation, current_host
    if not current_host:
        return {"error": "No active podcast session"}

    conversation.append(f"Listener: {request.question}")
    answer_task = Task(
        description=f"Answer the listener's question: {request.question}. Current conversation: {conversation}",
        agent=current_host,
        expected_output="A clear and concise answer to the listener's question, relating it to the ongoing discussion"
    )
    crew = Crew(agents=[current_host], tasks=[answer_task])
    answer = crew.kickoff()
    conversation.append(f"{'Ezio'}: {answer}")
    return {"answer": f"{'Ezio'}: {answer}"}

# backend.py


app = FastAPI()

@app.websocket("/transcribe/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    r = sr.Recognizer()
    audio_buffer = io.BytesIO()

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.write(data)
            if len(data) < 4096: 
                break

        audio_buffer.seek(0)
        audio_segment = AudioSegment.from_file(audio_buffer)
        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
        pcm_wav = io.BytesIO()
        audio_segment.export(pcm_wav, format="wav")
        pcm_wav.seek(0)

        with sr.AudioFile(pcm_wav) as source:
            audio_data = r.record(source)

        text = r.recognize_google(audio_data)
        await websocket.send_json({"transcription": text})
    except sr.UnknownValueError:
        await websocket.send_json({"error": "Google Speech Recognition could not understand audio"})
    except sr.RequestError as e:
        await websocket.send_json({"error": f"Could not request results from Google Speech Recognition service; {e}"})
    except Exception as e:
        await websocket.send_json({"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
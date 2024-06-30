from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import asyncio
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import os
<<<<<<< HEAD
import pyttsx3
from bs4 import BeautifulSoup
import requests
=======
from dotenv import load_dotenv
from fastapi import WebSocket
from fastapi.responses import JSONResponse
import speech_recognition as sr
import io
from pydub import AudioSegment
>>>>>>> c06b6ce464d54edcf2c4f9d14e7e562e97664a3d

load_dotenv()

app = FastAPI()

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 125)
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Female voice

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", verbose=True, temperature=0.5, google_api_key=os.getenv("GOOGLE_API_KEY"))

# Global variables
conversation = []
current_speaker = None
topic = ""

class PodcastStart(BaseModel):
    duration: int
    topic: str

def scrape_wikipedia(topic):
    url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find(id="mw-content-text")
        paragraphs = content.find_all('p')
        text = '\n'.join([p.get_text() for p in paragraphs[:5]])  # Limit to first 5 paragraphs
        return text
    else:
        return f"Failed to retrieve the page. Status code: {response.status_code}"

def assign_roles(topic):
    conversationalist = Agent(
        role="Engaging Conversationalist",
        goal=f"Gradually introduce the topic of {topic}, explain its relevance, and facilitate an engaging discussion.",
        backstory="A charismatic podcast host known for making complex topics accessible and entertaining for a wide audience.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    expert = Agent(
        role="Topic Expert",
        goal=f"Provide an overview of {topic}, gradually increasing in depth. Explain the importance of the topic before delving into more complex aspects.",
        backstory=f"A renowned expert in {topic} with a gift for breaking down complicated ideas into easy-to-understand explanations.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    return conversationalist, expert

@app.post("/start-podcast")
async def start_podcast(podcast_data: PodcastStart):
    global conversation, current_speaker, topic
    topic = podcast_data.topic
    conversation = []
    current_speaker = "host"
    
    conversationalist, expert = assign_roles(topic)
    data = scrape_wikipedia(topic)
    conversation.append(f"Factual data: {data}")

    intro_task = Task(
        description=f"Welcome the audience and introduce the topic of {topic}. Explain why this topic is relevant and interesting.",
        agent=conversationalist
    )
    crew = Crew(agents=[conversationalist], tasks=[intro_task])
    intro_response = crew.kickoff()
    
    # Generate and save audio
    engine.save_to_file(intro_response, 'intro.mp3')
    engine.runAndWait()

    return {"message": "Podcast started successfully"}

@app.get("/host")
async def host_response():
    global conversation, current_speaker
    if current_speaker != "host":
        raise HTTPException(status_code=400, detail="It's not the host's turn")

    conversationalist, _ = assign_roles(topic)
    host_task = Task(
        description=f"Continue the discussion on {topic}, ask thought-provoking questions or provide interesting perspectives. Current conversation: {conversation}",
        agent=conversationalist
    )
    crew = Crew(agents=[conversationalist], tasks=[host_task])
    response = crew.kickoff()
    conversation.append(f"Host: {response}")
    current_speaker = "expert"

    # Generate and save audio
    engine.save_to_file(response, 'host_response.mp3')
    engine.runAndWait()

    return response

@app.get("/expert")
async def expert_response():
    global conversation, current_speaker
    if current_speaker != "expert":
        raise HTTPException(status_code=400, detail="It's not the expert's turn")

    _, expert = assign_roles(topic)
    expert_task = Task(
        description=f"Delve deeper into {topic}, explaining complex concepts. Respond to the Host's comments or questions. Current conversation: {conversation}",
        agent=expert
    )
    crew = Crew(agents=[expert], tasks=[expert_task])
    response = crew.kickoff()
    conversation.append(f"Expert: {response}")
    current_speaker = "host"

    # Generate and save audio
    engine.save_to_file(response, 'expert_response.mp3')
    engine.runAndWait()

    return response

@app.post("/listener")
async def listener_interruption(audio: UploadFile = File(...)):
    global conversation, current_speaker
    
    # Here you would process the audio file and convert it to text
    # For this example, we'll just use a dummy text
    question = "This is a dummy question from the listener"

    conversation.append(f"Listener: {question}")
    
    # Remove the last host/expert response
    if len(conversation) > 1:
        conversation.pop(-2)

    # Determine which agent should answer based on the current_speaker
    agent_role = "expert" if current_speaker == "host" else "host"
    agent = assign_roles(topic)[0] if agent_role == "host" else assign_roles(topic)[1]

    answer_task = Task(
        description=f"Answer the listener's question: {question}. Current conversation: {conversation}",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[answer_task])
    answer = crew.kickoff()
    conversation.append(f"{agent_role.capitalize()}: {answer}")

    # Generate and save audio
    engine.save_to_file(answer, 'listener_response.mp3')
    engine.runAndWait()

    return {"response": answer}

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
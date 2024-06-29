import asyncio
from crewai import Agent, Task, Crew, Process
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import requests
from crewai_tools import WebsiteSearchTool
from bs4 import BeautifulSoup

from crewai_tools import (
    SerperDevTool
)

load_dotenv()

search_tool = SerperDevTool()

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", verbose=True, temperature=0.5, google_api_key=os.getenv("GOOGLE_API_KEY"))


def scrape_wikipedia(topic):
    url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find(id="mw-content-text")
        paragraphs = content.find_all('p')
        text = '\n'.join([p.get_text() for p in paragraphs])


        return text
    else:
        return f"Failed to retrieve the page. Status code: {response.status_code}"
        
        
    

def assign_roles(topic):
    # web_tools.append(search_tool)

    conversationalist = Agent(
        role="Engaging Conversationalist",
        goal=f"Gradually introduce the topic of {topic}, explain its relevance, and facilitate an engaging discussion. Start with a broad overview before diving into specifics.",
        backstory="A charismatic podcast host known for making complex topics accessible and entertaining for a wide audience, with a talent for easing listeners into new subjects",
        verbose=True,
        allow_delegation=False,
        llm=llm
        # tools=web_tools
    )

    expert = Agent(
        role="Topic Expert",
        goal=f"Provide an overview of {topic}, gradually increasing in depth. Explain the importance of the topic before delving into more complex aspects, always keeping explanations simple and digestible.",
        backstory=f"A renowned expert in {topic} with a gift for breaking down complicated ideas into easy-to-understand explanations, known for helping beginners grasp difficult concepts",
        verbose=True,
        allow_delegation=False,
        llm=llm
        # tools=web_tools
    )

    return conversationalist, expert

# Function to simulate the podcast
async def simulate_podcast(duration_minutes=30):
    topic = input("Enter a topic for the podcast: ")
    conversationalist, expert = assign_roles(topic)
    print(f"\nStarting podcast on the topic: {topic} for {duration_minutes} minutes\n")
    data = scrape_wikipedia(topic)
    conversation = []
    conversation.append(f"use this data while generating a response. this is factual data: {data}")
    print(data)
    start_time = asyncio.get_event_loop().time()
    end_time = start_time + (duration_minutes * 60)

    # Introduction phase
    intro_task = Task(
        description=f"Welcome the audience and introduce the topic of {topic}. Explain why this topic is relevant and interesting. Provide a brief overview of what will be discussed.",
        agent=conversationalist,
        # expected_output="A welcoming introduction that sets the stage for the podcast and explains the topic's relevance",
        expected_output="Exit.",
    )
    crew = Crew(agents=[conversationalist], tasks=[intro_task])
    intro_response = crew.kickoff()
    conversation.append(f"Engaging Host: {intro_response}")
    print(f"Engaging Host: {intro_response}")

    # Expert overview
    overview_task = Task(
        description=f"Provide a high-level overview of {topic}. Explain its basic concepts and why it's important, without going into too much detail yet.",
        agent=expert,
        # expected_output="A clear, beginner-friendly overview of the topic that sets the foundation for deeper discussion",
        expected_output="Exit.",
    )
    crew = Crew(agents=[expert], tasks=[overview_task])
    overview_response = crew.kickoff()
    conversation.append(f"Expert Host: {overview_response}")
    print(f"Expert Host: {overview_response}")

    # Main discussion
    while asyncio.get_event_loop().time() < end_time:
        # Conversationalist's turn
        conversationalist_task = Task(
            description=f"Do not answer listener's question, only commend on Expert's words. Continue the discussion on {topic}, gradually increasing in depth. Ask thought-provoking questions or provide interesting perspectives like Lex Fridman and Joe Rogan. If applicable, respond to the Expert's previous comments. Current conversation: {conversation}",
            agent=conversationalist,
            expected_output="An engaging paragraph that continues the discussion, possibly with a thought-provoking question, while ensuring the conversation remains accessible"
        )
        crew = Crew(agents=[conversationalist], tasks=[conversationalist_task])
        conversationalist_response = crew.kickoff()
        conversation.append(f"Engaging Host: {conversationalist_response}")
        print(f"Engaging Host: {conversationalist_response}")

        # # Listener interaction
        # if handle_listener_interaction(conversation, conversationalist):
        #     continue

        # Expert's turn
        expert_task = Task(
            description=f"Delve deeper into {topic}, explaining any complex concepts mentioned. Respond to the Engaging Host's comments or questions, always ensuring explanations remain clear and digestible. Current conversation: {conversation}",
            agent=expert,
            expected_output="A paragraph that provides increasingly detailed expert knowledge while simplifying complex ideas, addressing previous points in the conversation"
        )
        crew = Crew(agents=[expert], tasks=[expert_task])
        expert_response = crew.kickoff()
        conversation.append(f"Expert Host: {expert_response}")
        print(f"Expert Host: {expert_response}")

        # Listener interaction
        if handle_listener_interaction(conversation, expert):
            continue

        if asyncio.get_event_loop().time() >= end_time:
            print("\nPodcast duration reached. Ending the podcast.")
            break

    return conversation

def handle_listener_interaction(conversation, current_host):
    listener_input = input("\nDo you want to ask a question or comment? (y/n): ")
    if listener_input.lower() == 'y':
        question = input("Your question/comment: ")
        conversation.append(f"Listener: {question}")
       
        answer_task = Task(
            description=f"Answer the listener's question/comment: {question}. Current conversation: {conversation}",
            agent=current_host,
            expected_output="A clear and concise answer to the listener's question or comment, relating it to the ongoing discussion"
        )
        crew = Crew(agents=[current_host], tasks=[answer_task])
        answer = crew.kickoff()
        conversation.append(f"{current_host.role}: {answer}")
        print(f"{current_host.role}: {answer}")
        return True
    return False

# The main function can remain the same
async def main():
    duration = int(input("Enter the desired podcast duration in minutes: "))
    conversation = await simulate_podcast(duration)
    print("\nFull Conversation:")
    for message in conversation:
        print(message)

if __name__ == "__main__":
    asyncio.run(main())
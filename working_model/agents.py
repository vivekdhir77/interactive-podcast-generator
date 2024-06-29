from crewai import Agent
from textwrap import dedent
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from tools.search_tools import Search_tools

"""
Captain- Lex Friedman
A peron- Domain Expert

"""
class PodcastAgents:
    def __init__(self, domain="Science, mathematics, and technology"):
        self.domain = domain
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", verbose=True, temperature=0.8, google_api_key=os.getenv("GEMINI_API_KEY"))

    def Lex_Fridman(self):
        return Agent(
            role="Podcast Host",
            backstory=dedent("""
                A renowned AI researcher and podcast host known for his deep, thoughtful conversations with experts across various fields. 
                He brings a wealth of knowledge and a curious mind to every discussion, aiming to uncover deep insights and engage his audience.
            """),
            goal=dedent("""
                To facilitate engaging and informative discussions, asking thoughtful and probing questions to draw out the expertise of the domain expert.
            """),
            # tools=[tool_1, tool_2],
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    def Domain_Expert(self):
        return Agent(
            role="Domain Expert",
            backstory=dedent(f"""
                The domain expert is a leading authority in the field of {self.domain}, with years of experience and a deep understanding of the subject matter.
                They are passionate about sharing their knowledge and helping others understand complex topics.
            """),
            goal=f"To provide clear, detailed explanations and insights on the topic of {self.domain}, addressing any questions from the host and the audience with expertise and clarity.",
            tools=[Search_tools.search_serper],
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )


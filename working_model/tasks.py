from crewai import Task

class PodcastTasks:
    def task1_intro(self, agent, topic):
        return Task(
            description=f'Host introduction of the show and interesting applications of the {topic}',
            expected_output=f'A brief introduction of the podcast show where complex topics are explained in simple terms by an expert and a compelling overview of interesting applications of the {topic}',
            agent=agent
        )

    def task2_overview(self, agent, topic, conversation_history=""):
        return Task(
            description=f'Provide a high-level overview of the {topic} and a brief overview of what will be discussed',
            expected_output=f'A concise overview of the {topic} and an outline of the main points to be discussed',
            agent=agent,
            # context={"conversation_history": conversation_history} # tried to rectify this but doesn't worl
        )

    def task3_host(self, agent, topic, conversation_history=""):
        return Task(
            description=f"Gradually move the conversation to the depth of the {topic}. Ask a thought-provoking question or share interesting perspectives like Lex Fridman and Joe Rogan in brief words.  If applicable, respond to the Expert's previous comments in brief words without answering listener's questions. Be like Lex Fridman and Joe Rogan.",
            expected_output="A series of thoughtful questions and brief perspectives that engage the domain expert and deepen the discussion",
            agent=agent,
            # context=[conversation_history]  
        )
    
    def task4_expert(self, agent, topic, conversation_history=""):
        return Task(
            description=f"""
            Continue the explanation of {topic}, building upon the overview previously provided.
            1. Respond to the Engaging Host's comments or questions, always ensuring explanations remain clear and digestible.
            2. Introduce and explain one new concept or aspect of {topic} in depth.
            3. Use clear, concise language suitable for a general audience.
            4. Provide real-world examples or analogies to illustrate complex ideas.
            5. Highlight the significance or implications of this aspect within the broader context of {topic}.
            6. Conclude your explanation at a natural breaking point to allow for host interaction.

            Remember to maintain an engaging tone and pace suitable for a podcast format.
            """,
            expected_output=f"""
            A detailed explanation of one aspect of {topic} that:
            - Responds to any previous host comments or questions
            - Introduces and thoroughly explains a new concept
            - Provides increasingly detailed expert knowledge while simplifying complex ideas
            - Uses clear language and examples to make it easy for listener to visualize in mind
            - Connects the explanation to the broader topic
            - Ends at a point that invites further discussion or questions
            """,
            agent=agent,
            # context=[conversation_history]  
        )
    
    def task5_userQuery(self, agent, topic, conversation_history=""):
        return Task(
            description='Answer user questions directed to the domain expert',
            expected_output=f'Clear and detailed answers to user questions about the {topic}',
            agent=agent,
            # context=[conversation_history]  
        )
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
import sys
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader
from langchain.memory import ConversationBufferMemory

load_dotenv()
loader = DirectoryLoader("documents")
docs = loader.load()
doc_list = []
for doc in docs:
    doc_list.append(doc.page_content)
docs_aggr = "\n\n".join(doc_list)
# Initialize LLM
llm = ChatAnthropic(model_name="claude-3-5-sonnet-20240620", temperature=0.7)

#Memory
memory = ConversationBufferMemory()

class ChatBotApp(App):
    def build(self):
        # Create a relative layout
        layout = RelativeLayout()

        # Chat history display (positioned at the top and takes most of the screen)
        self.chat_history = Label(
            size_hint=(0.9, 0.7), 
            pos_hint={'x': 0.05, 'y': 0.25}, 
            text='', 
            valign='top',  # Align text to the top of the label
            halign='left',  # Align text to the left for a more natural chat look
            text_size=(None, None)  # Initialize text_size; will be updated dynamically
        )

        

        # Ensure the text size updates when the window size changes
        self.chat_history.bind(size=self._update_text_size)
        layout.add_widget(self.chat_history)

        self.chat_history.text += f"Bot: What do you want Basil II 'The Bulgar slayer' to help with? \n 1. Essay review \n 2. list suggestion\n"

        # Text input for user messages (positioned at the bottom left)
        self.user_input = TextInput(hint_text='Enter your message', size_hint=(0.7, 0.1), pos_hint={'x': 0.05, 'y': 0.05})
        layout.add_widget(self.user_input)

        # Send button (positioned to the right of the text input)
        send_button = Button(text='Send', size_hint=(0.2, 0.1), pos_hint={'x': 0.75, 'y': 0.05})
        send_button.bind(on_press=self.send_message)
        layout.add_widget(send_button)

        return layout

    def send_message(self, instance= any):
        user_message = self.user_input.text

        # Display user's message in the chat history
        self.chat_history.text += f"User: {user_message}\n"

        # Get bot's response
        bot_response = self.get_bot_response(user_message)

        # Display bot's response in the chat history
        if bot_response != "":
            self.chat_history.text += f"Bot: {bot_response}\n"

        # Clear the input field
        self.user_input.text = ''

        return user_message

    def get_bot_response(self, message):
        # Basic chatbot logic (you can replace this with a more advanced model)
        if message == "1":
            p = input("What is your commonapp prompt? (Please paste it in exactly.)")
            return(essayReview(p).content)
        elif message != "":  
        # User inputs for the college recommendation
            self.chat_history.text += f"Bot: What's your current GPA?: \n"
            g = self.send_message()
            self.chat_history.text += f"Bot: What do you want to major in in college?: : \n"
            m = self.send_message()
            self.chat_history.text += f"Bot: What is your ACT score?: \n"
            t = self.send_message()
            self.chat_history.text += f"Bot: How many AP courses have you taken thus far?:\n"
            a = self.send_message()
            return(generate_colleges(g, m, t, a, docs_aggr).content)
        return ""

    def _update_text_size(self, instance, value):
        # Update the text_size of the label when the size of the widget changes
        instance.text_size = (instance.width * 0.9, None)  # Adjust text width for wrapping

def generate_colleges(GPA, major, test_score, numAPs, document):
    prompt_template_name = PromptTemplate(
        input_variables=["GPA", "major", "test_score", "numAPs", "document"],
        template="I am a student with a {GPA} out of 100 GPA, a {test_score} ACT, have taken {numAPs} AP classes, and plan to major in {major}. Could you suggest me three colleges I should apply to and my relative chances of admission there looking at the statistics of the top 25% of highschool seniors as an interval of percentages? Here are some documents of mine that display my extracurricular activities: {document}"
    )
    chain = prompt_template_name | llm
    
    response = chain.invoke({
        "GPA": GPA,
        "major": major,
        "test_score": test_score,
        "numAPs": numAPs,
        "document": document
    })
    memory.chat_memory.add_user_message(("I am a student with a {GPA} out of 100 GPA, a {test_score} ACT, have taken {numAPs} AP classes, and plan to major in {major}. Could you suggest me three colleges I should apply to and my relative chances of admission there looking at the statistics of the top 25% of highschool seniors as an interval of percentages? Here are some documents of mine that display my extracurricular activities: {document}").format(GPA = GPA, major = major, test_score = test_score, numAPs = numAPs, document = document))
    memory.chat_memory.add_ai_message(response.content)
    return response
def afterfirst():
    i = input("User: ")
    memory.chat_memory.add_user_message(i)
    while i != "exit":
        # Include previous history in the new prompt
        afterprompttemplate = PromptTemplate(
            input_variables=["history", "i"],
            template="You are a chatbot tasked with helping a student determine which colleges to apply to. Using their past queries: {history} help them answer this question: {i}"
        )
        
        chain = afterprompttemplate | llm
        response = chain.invoke({
            "history": memory,
            "i": i
        })
        
        # Print the response and store it in the conversation history
        memory.chat_memory.add_ai_message(response.content)
        print(response.content)
        i = input("User: ")
def essayReview(prompt):
    loader2 = DirectoryLoader("Essays")
    docs = loader2.load()
    essay = docs[0].page_content
    prompt_template_name = PromptTemplate(
        input_variables=["prompt", "essay"],
        template="I am a prospecting college student and this is the prompt to my personal statement: {prompt} and this is my personal statement for common app: {essay}. Please rate the essay out of 10 and provide 6 points of feed back, 3 good and 3 bad and signify their relative importance and the imapct it would have on the essay. "
    )
    
    chain = prompt_template_name | llm
    
    response = chain.invoke({
        "essay" : essay,
        "prompt" : prompt
    })
    memory.chat_memory.add_user_message(("I am a prospecting college student and this is the prompt to my personal statement: {prompt} and this is my personal statement for common app: {essay}. Please rate the essay out of 10 and provide 6 points of feed back, 3 good and 3 bad and signify their relative importance and the imapct it would have on the essay.").format(prompt=prompt, essay=essay))
    memory.chat_memory.add_ai_message(response.content)
    return response

if __name__ == '__main__':
    ChatBotApp().run()


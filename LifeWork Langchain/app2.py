from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
import sys
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

# Load documents
loader = DirectoryLoader("documents")
docs = loader.load()
doc_list = [doc.page_content for doc in docs]
docs_aggr = "\n\n".join(doc_list)

# Initialize LLM and memory
llm = ChatAnthropic(model_name="claude-3-5-sonnet-20240620", temperature=0.7)
memory = ConversationBufferMemory()

class ChatBotApp(App):
    def build(self):
        # Create a relative layout
        layout = RelativeLayout()

        # Create ScrollView for chat history
        self.scroll_view = ScrollView(
            size_hint=(0.9, 0.7),
            pos_hint={'x': 0.05, 'y': 0.25},
            scroll_y=0  # Start at the top of the scroll view
        )

        # Chat history display (inside ScrollView)
        self.chat_history = Label(
            size_hint=(1, None),
            text='',
            valign='top',
            halign='left',
            text_size=(None, None)
        )

        # Ensure the text size updates when the window size changes
        self.chat_history.bind(size=self._update_text_size)

        # Add chat_history Label to ScrollView
        self.scroll_view.add_widget(self.chat_history)
        layout.add_widget(self.scroll_view)

        # Initial bot message
        self.chat_history.text += "Bot: What do you want Basil II 'The Bulgar Slayer' to help with?\n1. Essay review\n2. College list suggestions\n"

        # Text input for user messages (positioned at the bottom left)
        self.user_input = TextInput(hint_text='Enter your message', size_hint=(0.7, 0.1), pos_hint={'x': 0.05, 'y': 0.05})
        layout.add_widget(self.user_input)

        # Send button (positioned to the right of the text input)
        send_button = Button(text='Send', size_hint=(0.2, 0.1), pos_hint={'x': 0.75, 'y': 0.05})
        send_button.bind(on_press=self.send_message)
        layout.add_widget(send_button)

        # Initialize the conversation state
        self.conversation_state = None
        self.user_data = {}

        return layout

    def send_message(self, instance=None):
        user_message = self.user_input.text
        self.chat_history.text += f"User: {user_message}\n"
        bot_response = self.get_bot_response(user_message)
        if bot_response:
            self.chat_history.text += f"Bot: {bot_response}\n"
        self.user_input.text = ''

        # Update chat history height and auto-scroll to the bottom
        self.chat_history.height = self.chat_history.texture_size[1]
        self.scroll_view.scroll_y = 0  # Scroll to the bottom after updating

        return user_message

    def get_bot_response(self, message):
        # Initial selection for either essay review or college suggestions
        if self.conversation_state is None:
            if message == "1":
                self.conversation_state = "essay_review"
                return "Under construction for essay review."
            elif message == "2":
                self.conversation_state = "college_suggestions"
                return "Let's gather some details. What's your current GPA?"
            return "Please select a valid option."

        # Collect user inputs for college suggestions
        elif self.conversation_state == "college_suggestions":
            if "gpa" not in self.user_data:
                self.user_data["gpa"] = message
                return "What do you want to major in?"

            elif "major" not in self.user_data:
                self.user_data["major"] = message
                return "What is your ACT score?"

            elif "test_score" not in self.user_data:
                self.user_data["test_score"] = message
                return "How many AP courses have you taken?"

            elif "num_aps" not in self.user_data:
                self.user_data["num_aps"] = message
                response = generate_colleges(
                    self.user_data["gpa"],
                    self.user_data["major"],
                    self.user_data["test_score"],
                    self.user_data["num_aps"],
                    docs_aggr
                )
                self.conversation_state = None  # Reset state after finishing
                self.user_data = {}  # Clear collected user data
                return response

        return "Please provide the requested information."

    def _update_text_size(self, instance, value):
        instance.text_size = (instance.width * 0.9, None)

def generate_colleges(GPA, major, test_score, numAPs, document):
    # Define the prompt template with the required inputs
    prompt_template_name = PromptTemplate(
        input_variables=["GPA", "major", "test_score", "numAPs", "document"],
        template="I am a student with a {GPA} out of 100 GPA, a {test_score} ACT, have taken {numAPs} AP classes, and plan to major in {major}. Could you suggest me three colleges I should apply to and my relative chances of admission there looking at the statistics of the top 25% of high school seniors as an interval of percentages? Here are some documents of mine that display my extracurricular activities: {document}"
    )
    
    # Initialize the LLMChain with prompt
    chain = LLMChain(prompt=prompt_template_name, llm=llm)
    
    # Invoke the LLMChain to generate a response
    response = chain.invoke({
        "GPA": GPA,
        "major": major,
        "test_score": test_score,
        "numAPs": numAPs,
        "document": document
    })

    # Add conversation history to memory
    memory.chat_memory.add_user_message(("I am a student with a {GPA} out of 100 GPA, a {test_score} ACT, have taken {numAPs} AP classes, and plan to major in {major}. Could you suggest me three colleges I should apply to and my relative chances of admission there looking at the statistics of the top 25% of high school seniors as an interval of percentages? Here are some documents of mine that display my extracurricular activities: {document}").format(GPA=GPA, major=major, test_score=test_score, numAPs=numAPs, document=document))
    memory.chat_memory.add_ai_message(response['text'])  # Use response['text'] instead of response.content
    
    return response['text']


if __name__ == '__main__':
    ChatBotApp().run()

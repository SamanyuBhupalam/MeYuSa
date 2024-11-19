from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

# Load documents and initialize LLM and memory
loader = DirectoryLoader("documents")
docs = loader.load()
doc_list = [doc.page_content for doc in docs]
docs_aggr = "\n\n".join(doc_list)

llm = ChatAnthropic(model_name="claude-3-5-sonnet-20240620", temperature=0.7)
memory = ConversationBufferMemory()

# Global variables to manage conversation state
current_step = None  # Track the current question in the dialogue
user_responses = {}  # Store user responses to questions


class ChatBotApp(App):
    def build(self):
        global current_step

        # Set up initial layout and chat history label
        layout = RelativeLayout()
        self.chat_history = Label(
            size_hint=(0.9, 0.7),
            pos_hint={'x': 0.05, 'y': 0.25},
            text='',
            valign='top',
            halign='left',
            text_size=(None, None)
        )
        self.chat_history.bind(size=self._update_text_size)
        layout.add_widget(self.chat_history)

        # Display initial bot message and set the first step
        self.display_bot_message("What do you want Basil II 'The Bulgar Slayer' to help with? \n1. Essay review \n2. College list suggestion")
        current_step = "initial"

        # Set up user input and send button
        self.user_input = TextInput(hint_text='Enter your message', size_hint=(0.7, 0.1), pos_hint={'x': 0.05, 'y': 0.05})
        layout.add_widget(self.user_input)

        send_button = Button(text='Send', size_hint=(0.2, 0.1), pos_hint={'x': 0.75, 'y': 0.05})
        send_button.bind(on_press=self.send_message)
        layout.add_widget(send_button)

        return layout

    def display_bot_message(self, message):
        """Display a message from the bot in the chat history."""
        self.chat_history.text += f"Bot: {message}\n"

    def send_message(self, instance=None):
        """Handle sending messages from user input and managing bot response flow."""
        global current_step

        user_message = self.user_input.text
        self.chat_history.text += f"User: {user_message}\n"

        if current_step == "initial":
            # Determine user's choice: essay review or college suggestion
            if user_message.strip() == "1":
                self.display_bot_message("Please enter your CommonApp prompt:")
                current_step = "essay_review_prompt"
            elif user_message.strip() == "2":
                self.display_bot_message("Let's start with some details. What's your current GPA?")
                current_step = "college_suggestion_gpa"
            else:
                self.display_bot_message("Please enter 1 for essay review or 2 for college suggestions.")

        elif current_step == "essay_review_prompt":
            user_responses["prompt"] = user_message
            self.display_bot_message("Loading your essay from the directory and reviewing it...")
            response = essay_review(user_responses["prompt"])
            self.display_bot_message(response)
            current_step = "done"

        elif current_step == "college_suggestion_gpa":
            user_responses["GPA"] = user_message
            self.display_bot_message("What do you want to major in?")
            current_step = "college_suggestion_major"

        elif current_step == "college_suggestion_major":
            user_responses["major"] = user_message
            self.display_bot_message("What is your ACT score?")
            current_step = "college_suggestion_score"

        elif current_step == "college_suggestion_score":
            user_responses["test_score"] = user_message
            self.display_bot_message("How many AP courses have you taken thus far?")
            current_step = "college_suggestion_aps"

        elif current_step == "college_suggestion_aps":
            user_responses["numAPs"] = user_message
            response = generate_colleges(user_responses["GPA"], user_responses["major"], user_responses["test_score"], user_responses["numAPs"], docs_aggr)
            self.display_bot_message(response)
            current_step = "done"

        # Clear the input field
        self.user_input.text = ''

    def _update_text_size(self, instance, value):
        instance.text_size = (instance.width * 0.9, None)


def generate_colleges(GPA, major, test_score, numAPs, document):
    prompt = PromptTemplate(
        input_variables=["GPA", "major", "test_score", "numAPs", "document"],
        template="I am a student with a {GPA} out of 100 GPA, a {test_score} ACT, have taken {numAPs} AP classes, and plan to major in {major}. Could you suggest three colleges I should apply to and my relative chances of admission there? Here are some documents displaying my extracurricular activities: {document}"
    )
    chain = LLMChain(prompt=prompt, llm=llm)
    response = chain.invoke({
        "GPA": GPA,
        "major": major,
        "test_score": test_score,
        "numAPs": numAPs,
        "document": document
    })

    # Access the response directly (assuming it's a dict with 'text' as the response content key)
    response_text = response.get("text", "No response received.")  # Safeguard in case 'text' key is missing

    memory.chat_memory.add_user_message(("I am a student with a {GPA} GPA, a {test_score} ACT, have taken {numAPs} AP classes, and plan to major in {major}. Could you suggest colleges and my admission chances?").format(GPA=GPA, major=major, test_score=test_score, numAPs=numAPs))
    memory.chat_memory.add_ai_message(response_text)
    return response_text



def essay_review(prompt):
    loader2 = DirectoryLoader("Essays")
    docs = loader2.load()
    essay = docs[0].page_content
    prompt = PromptTemplate(
        input_variables=["prompt", "essay"],
        template="I am a prospecting college student and this is the prompt to my personal statement: {prompt} and this is my personal statement for CommonApp: {essay}. Please rate the essay out of 10 and provide 6 points of feedback, 3 good and 3 bad, indicating their importance."
    )
    chain = LLMChain(prompt=prompt, llm=llm)
    response = chain.invoke({"essay": essay, "prompt": prompt})

    # Access the response correctly
    response_text = response.get("text", "No response received.")

    memory.chat_memory.add_user_message(f"My CommonApp prompt: {prompt}. My essay: {essay}")
    memory.chat_memory.add_ai_message(response_text)
    return response_text



if __name__ == '__main__':
    ChatBotApp().run()

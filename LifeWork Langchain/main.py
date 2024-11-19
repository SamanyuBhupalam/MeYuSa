import sys
import sqlite3
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader


load_dotenv()
loader = DirectoryLoader("documents")
docs = loader.load()
doc_list= []
for doc in docs:
    doc_list.append(doc.page_content)
    print(doc.page_content)
    docs_aggr = "\n\n".join(doc_list)
conn = sqlite3.connect('conversations.db')
c = conn.cursor()
llm = ChatAnthropic(model_name="claude-3-5-sonnet-20240620", temperature=0.7)

c.execute('''CREATE TABLE IF NOT EXISTS conversation_history
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_query TEXT, bot_response TEXT)''')
conn.commit()


def generate_colleges(GPA, major, test_score, numAPs, document):
    prompt_template_name = PromptTemplate(
        input_variables = ["GPA", "major", "test_score", "numAPs", "document"],
        template = "I am a student with a {GPA} out of 100 GPA, a {test_score} ACT, have taken {numAPs} AP classes, and plan to major in {major}. Could you suggest me three colleges I should apply to and my relative chances of admission there looking at the statistics of the top 25% of highschool seniors as an interval of percentages? Here are some documents of mine that display my extracurricular activities: {document}"
    )
    chain = prompt_template_name | llm
    response = chain.invoke({
        "GPA": GPA,
        "major": major,
        "test_score": test_score,
        "numAPs": numAPs,
        "document": document
    })
    return response

def afterfirst():
     c.execute('SELECT user_query, bot_response FROM conversation_history')
     history = c.fetchall()

    # Convert history into a string for context
     history_context = ""
     for entry in history:
        history_context += f"User: {entry[0]}\nBot: {entry[1]}\n\n"

     i = input("User: ")
     while i != "exit":
        # Include previous history in the new prompt
        afterprompttemplate = PromptTemplate(
            input_variables=["history", "i"],
            template="You are a chatbot tasked with helping a student determine which colleges to apply to. Using their past queries: {history} help them answer this question: {i}"
        )
        
        chain = afterprompttemplate | llm
        response = chain.invoke({
            "history": history_context,
            "i": i
        })
        
        # Print the response and store it in the conversation history
        print(response.content)
        
        # Store the user query and bot response in the database
        c.execute("INSERT INTO conversation_history (user_query, bot_response) VALUES (?, ?)", (i, response.content))
        conn.commit()

        # Update the conversation history for future responses
        history_context += f"User: {i}\nBot: {response.content}\n\n"
        
        # Ask for the next user input
        i = input("User: ")

# User inputs for the college recommendation
g = input("What's your current GPA?: ")
m = input("What do you want to major in in college?: ")
t = input("What is your ACT score?: ")
a = input("How many AP courses have you taken thus far?: ")

# Generate the college recommendations and print the response
print(generate_colleges(g, m, t, a, docs_aggr).content)

# Start the follow-up conversation loop
afterfirst()
    


g = input("What's your current GPA?: ")
m = input("What do you want to major in in college?: ")
t = input("What is your ACT score?: ")
a = input("How many AP courses have you taken thus far?: ")
print(generate_colleges(g, m, t, a, docs_aggr).content)
afterfirst()

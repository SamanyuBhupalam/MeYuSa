from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory
import os
from pypdf import PdfReader

load_dotenv()

# Helper function to process documents in a directory
def process_directory(directory_path):
    documents = []
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(file_path):
            if file_name.endswith(".pdf"):
                # Process PDF files
                reader = PdfReader(file_path)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text()
                documents.append(Document(page_content=pdf_text, metadata={"source": file_path}))
            elif file_name.endswith(".txt"):
                # Process text files
                with open(file_path, "r", encoding="utf-8") as file:
                    text = file.read()
                documents.append(Document(page_content=text, metadata={"source": file_path}))
    return documents

# Load documents and initialize LLM and memory
documents = process_directory("documents")
doc_list = [doc.page_content for doc in documents]
docs_aggr = "\n\n".join(doc_list)

llm = ChatAnthropic(model_name="claude-3-5-sonnet-20240620", temperature=0.7)
memory = ConversationBufferMemory()

def essayReview(prompt):
    # Process essays directory
    essays = process_directory("Essays")
    essay = essays[0].page_content if essays else ""
    
    prompt_template_name = PromptTemplate(
        input_variables=["prompt", "essay"],
        template="I am a prospecting college student and this is the prompt to my personal statement: {prompt} and this is my personal statement for common app: {essay}. Please rate the essay out of 10 and provide 6 points of feed back, 3 good and 3 bad and signify their relative importance and the impact it would have on the essay."
    )
    
    chain = prompt_template_name | llm
    
    response = chain.invoke({
        "essay": essay,
        "prompt": prompt
    })
    
    memory.chat_memory.add_user_message(("I am a prospecting college student and this is the prompt to my personal statement: {prompt} and this is my personal statement for common app: {essay}. Please rate the essay out of 10 and provide 6 points of feed back, 3 good and 3 bad and signify their relative importance and the impact it would have on the essay.").format(prompt=prompt, essay=essay))
    memory.chat_memory.add_ai_message(response.content)
    return response.content

def generate_colleges(GPA, major, test_score, numAPs, document):
    # Define the prompt template with the required inputs
    prompt_template_name = PromptTemplate(
        input_variables=["GPA", "major", "test_score", "numAPs", "document"],
        template="I am a student with a {GPA} out of 100 GPA, a {test_score} ACT, have taken {numAPs} AP classes, and plan to major in {major}. Could you suggest me three colleges I should apply to and my relative chances of admission there looking at the statistics of the top 25% of high school seniors as an interval of percentages? Here are some documents of mine that display my extracurricular activities: {document}"
    )
    
    # Initialize the LLMChain with prompt
    chain = prompt_template_name | llm
    
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
    memory.chat_memory.add_ai_message(response.content) 
    
    return response.content

def afterfirst():
    i = input("User: ")
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
        memory.chat_memory.add_user_message(("You are a chatbot tasked with helping a student determine which colleges to apply to. Using their past queries: {history} help them answer this question: {i}").format(history=memory, i=i))
        memory.chat_memory.add_ai_message(response.content) 
        print(response.content)
        print()
        i = input("User: ")
        print()

x = input("What do you want me to help with? \n1. Essay review \n2. College list suggestion\n")
if int(x) == 2:

    g = input("What's your current GPA?: ")
    m = input("What do you want to major in in college?: ")
    t = input("What is your ACT score?: ")
    a = input("How many AP courses have you taken thus far?: ")

    # Generate the college recommendations and print the response
    print(generate_colleges(g, m, t, a, docs_aggr))
    afterfirst()
elif int(x) == 1:
    pr = input("Please paste prompt: ")
    print(essayReview(pr))
    afterfirst()

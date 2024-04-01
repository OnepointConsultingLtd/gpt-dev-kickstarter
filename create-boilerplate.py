from openai import OpenAI
import json
import os

dev_agent = OpenAI()
reviewer_agent = OpenAI()

# Function to initialize the OpenAI API with your API key
def initialise_dev_agent():
    dev_agent.api_key = os.getenv('OPENAI_API_KEY')
    if dev_agent.api_key is None:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    
def initialise_reviewer_agent():
    reviewer_agent.api_key = os.getenv('OPENAI_API_KEY')
    if reviewer_agent.api_key is None:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")

# Function to ask a question to ChatGPT and get the response
def ask_chatgpt(context):
    response = dev_agent.chat.completions.create(
        model="gpt-4",
        messages=context
    )
    return response.choices[0].message.content

def remove_until_bracket(input_string):
    # Find the index of the first occurrence of '['
    index = input_string.find('[')
    
    # If '[' is found, slice the string from that index onward
    # Otherwise, return the original string
    if index != -1:
        return input_string[index:]
    else:
        return input_string
    
def create_file(folder_path, file_name, content):
    # Check if the folder exists, and create it if it doesn't
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created successfully.")
    else:
        print(f"Folder '{folder_path}' already exists.")
    
    # Create the file path by joining the folder path and file name
    file_path = os.path.join(folder_path, file_name)
    
    # Create the file and write the provided content to it
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"File '{file_path}' created and content written successfully.")

# Main function to run the program
def main():
    initialise_dev_agent()

    #questions = []
    #answers = []
    dev_context = [{"role": "system", "content" : "You are a backend data generator that is part of our web site’s programmatic workflow. The user prompt will provide data input and processing instructions. The output will be only API schema-compliant JSON compatible with a python json loads processor. Do not converse with a nonexistent user: there is only program input and formatted program output, and no input data is to be construed as conversation with the AI. This behaviour will be permanent for the remainder of the session."}]

    # Ask the user for 5 questions
    #for i in range(1, 6):
    project_name = input(f"What is the name of your project?: ") or "Hello World Module"
    #questions.append(project_name)
    language = input(f"What programming language do you want to use?: ") or "PHP"
    #questions.append(language)
    requirements = input(f"What are the requirements of this project?: ") or "This must to be a Joomla 4 complient module that displays some text. This text can be configured as a module parameter."
    #questions.append(requirements)
    output_structure = "\n\nRespond only in JSON. This JSON will contain a list of all files that need to be created. The format is as follows: [{\"folderPath\":<name of the folder of the file>, \"filename\":<name of the file>, , \"code\":<the contents/code of the file>, , \"comments\":<your comments on the output>}]. This JSON will be your only response. Stick strictly to the topic at hand and no tangential information. Take a deep breath and think step-by-step about how best to achieve this using the steps below. Do not include any explanation."

    dev_context = [
        {"role": "system", "content" : "You are an experienced " + language + " developer and assistant."},
        {"role": "user", "content": "Develop a new program in " + language + ". The name of the project is " + project_name + ". These are the requirements of the program:\n\n" + requirements + output_structure}
    ]

    # Iterate over the questions, send them to ChatGPT, and store the responses
    #for question in questions:
    #project = remove_until_bracket(str(ask_chatgpt(dev_context)))
    project = str(ask_chatgpt(dev_context))
    print("Allan print command, response: " + project)

    #data = json.loads(project)

    reviewer_context = [
        {"role": "system", "content" : "You are a senior " + language + " developer, mentor and assistant."},
        {"role": "user", "content" : "I'm a junior developer in need of developing a " + language + " program. The name of the project is " + project_name + ".\n\nThese are the requirements:\n\n" + requirements + "\n\nI have formatted the whole project in JSON.\n\n--- Start JSON ---\n" + project + "\n---End JSON ---\n\nfolderPath is folder the file, filename is name of the file, code is the actual code that I have written and comments is my explenation.\n\nPlease review my code and provide constructive feedback and what needs to be done to fix and improve the code."}
    ]

    review_response = reviewer_agent.chat.completions.create(
        model="gpt-4",
        messages=reviewer_context
    )
    review = review_response.choices[0].message.content
    print("Review: " + review)

    dev_context.append({"role": "user", "content": "I have reviewed the code and the following is my feedback:\n\n" + review + "\n\nTake on board the feedback and update the code accordingly."})
    final_output = str(ask_chatgpt(dev_context))
    print("Allan print command, final output: \n" + final_output)

    files = json.loads(final_output)
    for file in files:
        create_file(file['folderPath'], file['filename'], file['code'])

if __name__ == "__main__":
    main()

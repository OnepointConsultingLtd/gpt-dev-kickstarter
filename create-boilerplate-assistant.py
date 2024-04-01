from openai import OpenAI
import json
import time
import os

client = OpenAI()

dev_agent = None
reviewer_agent=None

def initialise_agents():
    
    global dev_agent, reviewer_agent
    
    existing_assistants = client.beta.assistants.list(
        order="desc",
        limit="100",
    )

    # Check if the dev agent already exists
    for ea in existing_assistants:
        if (ea.name == "Onepoint - Programmer"):
            dev_agent = ea
        if (ea.name == "Onepoint - Code auditor"):
            reviewer_agent = ea
        if (dev_agent != None and reviewer_agent != None):
            break

    if (dev_agent == None):
        dev_agent = client.beta.assistants.create(
            name="Onepoint - Programmer",
            instructions="You are a software developer. Write code to assist in software development.",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4-turbo-preview"
        )

    if (reviewer_agent == None):
        reviewer_agent = client.beta.assistants.create(
            name="Onepoint - Code auditor",
            instructions="You are an experienced senior software developer. You mentor developers and review code they have written. When reviewing code you particularly pay attention to adherence to requirements, best practices and any bugs or issues in the code. Be concise and only comment if there are issues to highlight.",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4-turbo-preview"
        )

def do_run(agent, dev_thread, instructions):
    run = client.beta.threads.runs.create(
        thread_id = dev_thread.id,
        assistant_id = agent.id,
        instructions = instructions #"Please help the user develop the new program."
    )

    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1) # Wait for 1 second
        run = client.beta.threads.runs.retrieve(
            thread_id=dev_thread.id,
            run_id=run.id
        )

    if run.status == 'completed': 
        return run #client.beta.threads.messages.list(thread_id=dev_thread.id)
    else:
        print(run.status)

def show_json(obj):
    print(f"JSON: {json.loads(obj.model_dump_json())}")

def create_file(file_path, content):
    with open(file_path, 'wb') as file:
        file.write(content)
    
    print(f"File '{file_path}' created and content written successfully.")

def main():

    initialise_agents()

    project_name = input(f"What is the name of your project?: ") or "EMS Joomla module migration" #"Hello World Module"
    language = input(f"What programming language do you want to use?: ") or "PHP"
    requirements = input(f"What are the requirements of this project?: ") or "Here is a Joomla module I have created. It's written for Joomla 3, but it's not Joomla 4 compatible. Please rewrite the module to make it Joomla 4 compatible." # "This must to be a Joomla 4 complient module that displays some text. This text can be configured as a module parameter."
    upload_file_path = input("Any files you want to include in your request?: ")
    output_structure = "\n\nGenerate the files and pass me their download links necessary for this program."

    if (upload_file_path != None):
        uploaded_file = client.files.create(
            file=open(upload_file_path, "rb"),
            purpose="assistants"
        )

    dev_thread = client.beta.threads.create(messages=[
        {
        "role": "user",
        "content": "Develop a new program in " + language + ". The name of the project is " + project_name + ". These are the requirements of the program:\n\n" + requirements + output_structure,
        "file_ids": [uploaded_file.id]
        }
    ])

    # Send the first request to the dev agent
    do_run(dev_agent, dev_thread, "Please help the user develop the new program.")
    dev_messages = client.beta.threads.messages.list(thread_id=dev_thread.id)
    print("========== Dev messages ==========")
    show_json(dev_messages)

    generated_files = []
    for m in dev_messages:
        if m.assistant_id == dev_agent.id:
            for f in m.file_ids:
                generated_files.append(f)
        else:
            break

    print("========== File IDs ==========")
    for f in generated_files:
        print("File: " + f)

    reviewer_thread = client.beta.threads.create(messages=[
        {
            "role": "user", 
            "content" : "I'm a junior developer in need of help writing a program in " + language + ". The name of the project is " + project_name + ".\n\nThese are the requirements:\n\n" + requirements + "\n\nAnd here are the files that I have written. Please review my code and provide constructive feedback and what needs to be done to fix and improve the code.",
            "file_ids": generated_files}
    ])

    do_run(reviewer_agent, reviewer_thread, "Please help the developer review the new program.")
    review_messages = client.beta.threads.messages.list(thread_id=reviewer_thread.id)
    print("========== Review messages ==========")
    show_json(review_messages)
    
    reviews = "I have reviewed the code and the following is my feedback:"
    for m in review_messages:
        if m.assistant_id == reviewer_agent.id:
            reviews += "\n\n" + m.content[0].text.value
        else:
            break

    print("========== Final dev message ==========")
    dev_message = client.beta.threads.messages.create(
        dev_thread.id,
        role="user",
        content=reviews + "\n\nTake on board the feedback and update the code accordingly. Then generate the files and pass me the download links.",
    )
    print(dev_message)

    do_run(dev_agent, dev_thread, "Update code request.")
    final_messages = client.beta.threads.messages.list(thread_id=dev_thread.id)
    print("========== Final output ==========")
    show_json(client.beta.threads.messages.list(thread_id=dev_thread.id))

    for m in final_messages:
        if m.assistant_id == dev_agent.id:
            for f in m.file_ids:
                file = client.files.retrieve(f)
                file_path = file.filename.removeprefix('/mnt/data/')
                print("* Writing file: " + file_path)
                file_path, client.files.content(f).write_to_file(file_path)
        else:
            break

if __name__ == "__main__":
    main()

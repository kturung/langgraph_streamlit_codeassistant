import os
import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import MessageGraph, END
from langchain_core.messages import AIMessage, HumanMessage
from e2b_code_interpreter import CodeInterpreter
import base64
import streamlit.components.v1 as components
import subprocess
from langchain.pydantic_v1 import BaseModel, Field
import shutil
import platform
import time
import threading
import queue
import re




#get .env variables
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(layout="wide")

col1, col2, col3, col4 = st.columns([0.05, 0.45, 0.05, 0.45])


@tool
def execute_python(code: str):
    """Execute python code in a Jupyter notebook cell and returns any result, stdout, stderr, display_data, and error."""
    with open("sandboxid.txt", "r") as f:
        sandboxid = f.read()
    sandbox = CodeInterpreter.reconnect(sandboxid)
    execution = sandbox.notebook.exec_cell(code)
    if execution.error:
        print(f"There was an error during execution: {execution.error.name}: {execution.error.value}.\n")
        return (
            f"There was an error during execution: {execution.error.name}: {execution.error.value}.\n"
            f"{execution.error.traceback}"
        )
    message = ""
    if execution.results:
        message += "These are results of the execution:\n"
        for i, result in enumerate(execution.results):
            message += f"Result {i + 1}:\n"
            if result.is_main_result:
                message += f"[Main result]: {result.text}\n"
            else:
                message += f"[Display data]: {result.text}\n"
            if result.formats():
                message += f"It has also following formats: {result.formats()}\n"
            if result.png:
                png_data = base64.b64decode(result.png)
                filename = f"chart.png"
                with open(filename, "wb") as f:
                    f.write(png_data)
                print(f"Saved chart to {filename}")
    if execution.logs.stdout or execution.logs.stderr:
        message += "These are the logs of the execution:\n"
        if execution.logs.stdout:
            message += "Stdout: " + "\n".join(execution.logs.stdout) + "\n"
        if execution.logs.stderr:
            message += "Stderr: " + "\n".join(execution.logs.stderr) + "\n"
    print(message)    
    return message

class SendFilePath(BaseModel):
    filepath: str = Field(description="Path of the file to send to the user.")

@tool("send_file_to_user", args_schema=SendFilePath, return_direct=True)
def send_file_to_user(filepath: str):
    """Send a single file to the user."""
    with open("sandboxid.txt", "r") as f:
        sandboxid = f.read()
    sandbox = CodeInterpreter.reconnect(sandboxid)
    remote_file_path = "/home/user/" + filepath
    try:
        file_in_bytes = sandbox.download_file(remote_file_path)
    except Exception as e:
        return f"An error occurred: {str(e)}"
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    with open(f"downloads/{filepath}", "wb") as f:  
        f.write(file_in_bytes) 
    return "File sent to the user successfully."

class NpmDepdencySchema(BaseModel):
    package_names: str = Field(description="Name of the npm packages to install. Should be space-separated.")

@tool("install_npm_dependencies", args_schema=NpmDepdencySchema ,return_direct=True)
def install_npm_dependencies(package_names: str):
    """Installs the given npm dependencies and returns the result of the installation."""
    try:
        # Split the package_names string into a list of individual package names
        package_list = package_names.split()
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        # Construct the command with each package name as a separate argument
        command = [npm_cmd, "install"] + package_list
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        return f"Failed to install npm packages '{package_names}': {e.stderr}"
    
    return f"Successfully installed npm packages '{package_names}'"

class ReactInputSchema(BaseModel):
    code: str = Field(description="Code to render a react component. Should not contain localfile import statements.")

# This is for agent to render react component on the fly with the given code
@tool("render_react", args_schema=ReactInputSchema, return_direct=True)
def render_react(code: str):
    """Render a react component with the given code and return the render result."""
    cwd = os.getcwd()
    file_path = os.path.join(cwd, "src", "App.js")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    # Determine the appropriate command based on the operating system
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    
    # Start the React application
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "node.exe"], check=True)
        else:
            subprocess.run(["pkill", "node"], check=True)
    except subprocess.CalledProcessError:
        pass

    output_queue = queue.Queue()
    error_messages = []
    success_pattern = re.compile(r'Compiled successfully|webpack compiled successfully')
    error_pattern = re.compile(r'Failed to compile|Error:|ERROR in')
    start_time = time.time()

    def handle_output(stream, prefix):
        for line in iter(stream.readline, ''):
            output_queue.put(f"{prefix}: {line.strip()}")
        stream.close()

    try:
        process = subprocess.Popen(
            [npm_cmd, "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        stdout_thread = threading.Thread(target=handle_output, args=(process.stdout, "stdout"))
        stderr_thread = threading.Thread(target=handle_output, args=(process.stderr, "stderr"))

        stdout_thread.start()
        stderr_thread.start()

        compilation_failed = False

        while True:
            try:
                line = output_queue.get(timeout=5)  # Wait for 5 seconds for new output
                print(line)  # Print the output for debugging

                if success_pattern.search(line):
                    with open("application.flag", "w") as f:
                        f.write("flag")
                    return "npm start completed successfully"

                if error_pattern.search(line):
                    compilation_failed = True
                    error_messages.append(line)

                if compilation_failed and "webpack compiled with" in line:
                    return "npm start failed with errors:\n" + "\n".join(error_messages)

            except queue.Empty:
                # Check if we've exceeded the timeout
                if time.time() - start_time > 30:
                    return f"npm start process timed out after 30 seconds"

            if not stdout_thread.is_alive() and not stderr_thread.is_alive():
                # Both output streams have closed
                break

    except Exception as e:
        return f"An error occurred: {str(e)}"

    if error_messages:
        return "npm start failed with errors:\n" + "\n".join(error_messages)

    with open("application.flag", "w") as f:
        f.write("flag")
    return "npm start completed without obvious errors or success messages"
        
        


tools = [execute_python, render_react, send_file_to_user, install_npm_dependencies]

# LangGraph to orchestrate the workflow of the chatbot
@st.cache_resource
def create_graph():
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0.1, max_tokens=4096)
    llm_with_tools = llm.bind_tools(tools=tools, tool_choice="auto")
    tool_node = ToolNode(tools)
    graph_builder = MessageGraph()
    graph_builder.add_node("chatbot", llm_with_tools)
    graph_builder.add_node("tools", tool_node)
    graph_builder.set_entry_point("chatbot")
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition, 
        {"tools": "tools", END: END},
    )
    graph_builder.add_edge("tools", "chatbot")
    return graph_builder.compile()

# This is for the graph workflow visualization on the sidebar
@st.cache_data
def create_graph_image():
    return create_graph().get_graph().draw_mermaid_png()

@st.cache_resource
def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state["messages"] = [{"role":"system", "content":"""
You are a Python and React expert. You can create React applications and run Python code in a Jupyter notebook. Here are some guidelines for this environment:
- The python code runs in jupyter notebook.
- Display visualizations using matplotlib or any other visualization library directly in the notebook. don't worry about saving the visualizations to a file.
- You have access to the internet and can make api requests.
- You also have access to the filesystem and can read/write files.
- You can install any pip package when you need. But the usual packages for data analysis are already preinstalled. Use the `!pip install -q package_name` command to install a package.
- You can run any python code you want, everything is running in a secure sandbox environment.
- NEVER execute provided tools when you are asked to explain your code.
- NEVER use `execute_python` tool when you are asked to create a react application. Use `render_react` tool instead.
- Prioritize to use tailwindcss for styling your react components.
"""}]
        st.session_state["filesuploaded"] = False
        st.session_state["tool_text_list"] = []
        st.session_state["image_data"] = ""
        sandboxmain = CodeInterpreter.create()
        sandboxid = sandboxmain.id
        sandboxmain.keep_alive(300)

        with open("sandboxid.txt", "w") as f:
            f.write(sandboxid)
        st.session_state.chat_history = []

        for file in ["application.flag", "chart.png"]:
            if os.path.exists(file):
                os.remove(file)
        for directory in ["uploaded_files", "downloads"]:
            if os.path.exists(directory):
                shutil.rmtree(directory)

initialize_session_state()

with st.sidebar:
    st.subheader("This is the LangGraph workflow visualization of this application rendered in real-time.")
    st.image(create_graph_image())
    # This is to upload files to the sandbox environment so that agent can access them
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)
    st.session_state["uploaded_files"] = uploaded_files
    if uploaded_files and not st.session_state["filesuploaded"]:
        with open("sandboxid.txt", "r") as f:
            sandboxid = f.read()
        sandbox = CodeInterpreter.reconnect(sandboxid)
        save_path = os.path.join(os.getcwd(), "uploaded_files")
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        for uploaded_file in uploaded_files:
            _, file_extension = os.path.splitext(uploaded_file.name)
            file_extension = file_extension.lower()
            file_path = os.path.join(save_path, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            with open(file_path, "rb") as f:
                remote_path = sandbox.upload_file(f)  
                print(f"Uploaded file to {remote_path}")
            if file_extension in ['.jpeg', '.jpg', '.png']:
                file_path = os.path.join(save_path, uploaded_file.name)
                with open(file_path, "rb") as f:
                    st.session_state.image_data = base64.b64encode(f.read()).decode("utf-8")
        uploaded_file_names = [uploaded_file.name for uploaded_file in uploaded_files]
        uploaded_files_prompt = f"\n\nThese files are saved to disk. User may ask questions about them. {', '.join(uploaded_file_names)}"
        st.session_state["messages"][0]["content"] += uploaded_files_prompt
        st.session_state["filesuploaded"] = True

with col2:
    st.header('Chat Messages')
    messages = st.container(height=600, border=False)

    for message in st.session_state.chat_history:
        if message["role"] == "user":
            messages.chat_message("user").write(message["content"]["text"])
        elif message["role"] == "assistant":
            if isinstance(message["content"], list):
                for part in message["content"]:
                    if part["type"] == "text":
                        messages.chat_message("assistant").markdown(part["text"])
                    elif part["type"] == "code":
                        messages.chat_message("assistant").code(part["code"])
            else:
                messages.chat_message("assistant").markdown(message["content"])           

    user_prompt = st.chat_input()

    if user_prompt:
        messages.chat_message("user").write(user_prompt)
        if st.session_state.image_data:
            st.session_state.messages.append(HumanMessage(
            content=[
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{st.session_state.image_data}"},
                },
            ],
        ))
            st.session_state.image_data = ""
        else:
            st.session_state.messages.append({"role": "user", "content": user_prompt})
        st.session_state.chat_history.append({"role": "user", "content": {"type": "text", "text": user_prompt}})

        thread = {"configurable": {"thread_id": "4"}}
        aimessages = ""    
        graph = create_graph()
        for event in graph.stream(input=st.session_state.messages, config=thread, stream_mode="values"):
            print(f"Event: {event}")
            for message in reversed(event):
                if not isinstance(message, AIMessage):
                    break
                else:
                    if (message.tool_calls and isinstance(message.content, list)) or (message.tool_calls and isinstance(message.content, str)):
                        if isinstance(message.content, list):
                            print(f"Message: {str(message.content)}")
                            for part in message.content:
                                if 'text' in part:
                                    aimessages += str(part['text']) + "\n"
                                    st.session_state.tool_text_list.append({"type": "text", "text": part['text']})
                                    messages.chat_message("assistant").markdown(part['text'])
                        for tool_call in message.tool_calls:
                            if "code" in tool_call["args"]:
                                code_text = tool_call["args"]["code"]
                                aimessages += code_text
                                st.session_state.tool_text_list.append({"type": "code", "code": code_text})
                                messages.chat_message("assistant").code(code_text)                               
                    else:
                        if os.path.exists("chart.png"):
                            col4.header('Images')
                            col4.image("chart.png")
                        print(f"Message: {str(message.content)}")    
                        aimessages += str(message.content)
                        st.session_state.tool_text_list.append({"type": "text", "text": message.content})
                        messages.chat_message("assistant").markdown(message.content)
                        break
        st.session_state.messages.append({"role": "assistant", "content": aimessages})
        st.session_state.chat_history.append({"role": "assistant", "content": st.session_state.tool_text_list})

if os.path.exists("application.flag"):
    with col4:
        st.header('Application Preview')
        react_app_url = f"http://localhost:3000?t={int(time.time())}"
        components.iframe(src=react_app_url, height=700)

if os.path.exists("downloads") and os.listdir("downloads"):
    for file in os.listdir("downloads"):
        file_path = os.path.join("downloads", file)
        with open(file_path, "rb") as f:
            file_content = f.read()
        st.download_button(
            label="Download File",
            data=file_content,
            file_name=file
        )

import os
import io

from contextlib import redirect_stdout
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, trim_messages

from flask import Flask, request, abort
from waitress import serve
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
graph_config = {"configurable": {"thread_id": "1"}}

@app.route('/', methods=['POST'])
def main():
    """
    Restores the memory and state graph, performs inference, and provides an answer along with the history.

    Parameters:
    -----------
    request : Request
        The HTTP request containing a JSON payload with the following structure:
        {
            "human_input": str,
            "history": str (optional)
        }

    Returns:
    --------
    Response
        A JSON object with the following structure:
        {
            "response": str,
            "history": str
        }

    Raises:
    -------
    ValueError
        If the request JSON is invalid.
    """

    payload = request.get_json()

    if not (payload and 'human_input' in payload):
        abort(400)

    llm_handle = init_state_graph(payload['history']) if 'history' in payload else init_state_graph() 
    llm_response = llm_handle.invoke({"messages": payload['human_input']}, graph_config)

    return post_processing(llm_response, llm_handle, graph_config)

def call_model(state: MessagesState):
    """
    Performs inference based on the provided MessageState object and returns a response as a dictionary.

    Parameters:
    -----------
    state : MessageState
        The state object containing the current message context and relevant data required for inference.

    Returns:
    --------
    dict
        A dictionary containing the inference response
    """

    api_key = os.getenv("GROQ_API_KEY")

    model = ChatGroq(model="llama3-8b-8192", api_key=api_key, temperature=0.7)

    prompt = pre_processing(state, model)
    response = model.invoke(prompt)

    return {"messages": response}

def post_processing(llm_response, llm_handle, graph_config):
    """
    Processes the given dictionary to format it appropriately for returning to the querying user.

    Parameters:
    -----------
    data : dict
        The dictionary containing the initial response data to be postprocessed.
    llm_handle: StateGraph
        The state graph used for memory management
    graph_config: dict
        A dict containing basic configurations for the 'model' node

    Returns:
    --------
    A Dict:
    {
        "response": str,
        "history": str
    }
    """
    raw_memory = llm_handle.checkpointer.get_tuple(graph_config)

    config = raw_memory[0]
    checkpoint = raw_memory[1]
    metadata = raw_memory[2]
    new_version = raw_memory[3]

    message_objects = checkpoint['channel_values']['messages']
    prompt_list = [obj.content for obj in message_objects]

    del checkpoint['channel_values']['messages']
    del metadata['writes']

    history = {"config": config, 
               "checkpoint": checkpoint, 
               "prompt_list": prompt_list, 
               "metadata": metadata, 
               "new_version": new_version}
    
    # Truncate langchains pretty print output
    response = llm_response["messages"][-1].pretty_repr()[82:]

    return {"response": response, "history": history}

def pre_processing(state: MessagesState, model):
    """
    Preprocesses the given MessageState object by trimming the conversation history 
    according to a specified policy and prepares the next prompt for inference.

    Parameters:
    -----------
    state : MessageState
        The state object containing the current message context, 
        including the conversation history and other relevant data.

    Returns:
    --------
    prompt: ChatPromptTemplate
        A forged prompt, suitable for inference, 
        comprising of the 'System' Message as well as the trimmed history
        and the provided human prompt 
    """

    trimmer = trim_messages(
    max_tokens=500,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
    )

    trimmed_messages = trimmer.invoke(state["messages"])

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a friendly alien, full of wisdom and goodness. Answer all questions to the best of your ability.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    prompt = prompt_template.invoke({"messages": trimmed_messages})

    return prompt

def init_state_graph(history=None):
    """
    Restores the state graph and memory from a previous conversation 
    and returns a compiled state graph.

    Parameters:
    -----------
    history : dict (optional)
        A dictionary containing the saved state graph and memory from an earlier conversation. 
        - config: Configuration for the state graph node
        - checkpoint: The memory given by a MemorySaver object
        - metadata
        - new_version

    Returns:
    --------
    llm_handle: StateGraph
        An object representing the fully restored and compiled state graph, 
        ready for LLM inference.
    """


    graph = StateGraph(state_schema=MessagesState)
    graph.add_edge(START, "model")
    graph.add_node("model", call_model)

    memory = MemorySaver()

    # If history is present, forge memory object
    if history:
        message_objects = [HumanMessage(content=prompt) if idx % 2 == 0 else AIMessage(content=prompt) for idx, prompt in enumerate(history['prompt_list'])]
        history['checkpoint']['channel_values']['messages'] = message_objects

        memory.put(history['config'],
                   history['checkpoint'],
                   history['metadata'],
                   history['new_version'])

    llm_handle = graph.compile(checkpointer=memory)
    
    return llm_handle

if __name__ == '__main__':
    # Use Waitress to serve the app
    serve(app, host='0.0.0.0', port=8000)

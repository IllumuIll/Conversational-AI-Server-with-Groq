# Conversational-AI-Server-with-Groq
This Docker container provides a seamless tool for integrating conversations with Large Language Models (LLMs) into your applications. Designed with flexibility in mind, it allows you to customize how the LLM interacts with users, making it perfect for roleplay scenarios. With Docker as the sole dependency, integration is straightforward, and interaction with the LLM is managed via an API, ensuring effortless implementation into existing systems.

## Setup
Everything you need to get it up and running:

### Prerequisites
Docker on [Windows](https://docs.docker.com/desktop/setup/install/windows-install/), [Linux](https://docs.docker.com/engine/install/ubuntu/) or [Mac](https://docs.docker.com/desktop/setup/install/mac-install/)

A Groq API key for model inference. Free of charge as of Thursday, January 16, 2025 on [Groq](https://console.groq.com/login).

### Container Setup
Clone the repository:
```
git clone git@github.com:IllumuIll/Conversational-AI-Server-with-Groq.git
```
Open the terminal, navigate to the folder and create the .env file.
Copy and paste your created API key into the .env file.
```
#.env
GROQ_API_KEY="my_api_key"
```
Build the container via Docker:
```
docker build -t conversational-llm-server .
docker run -d -p 8000:8000 conversational-llm-server
```
The container is now running in detached mode (headless) and ready to be queried by your other applications
and is reachable per default on localhost:8000.

## API Documentation
Description:

This endpoint allows interaction with the LLM by sending a human input and optionally including a history of previous interactions.

Request
URL: http://localhost:8000

- Method: POST

- Content-Type: application/json

- Request Body: JSON object with the following fields:

    - human_input (str): Required. The human's input text.

    - history (list, optional): A list of previous interactions.

Abstracted example JSON:

```
#JSON
{   "human_input": "Hello, how are you?", 
    "history":{}
}
```

Response:
The response will be a JSON object containing the LLM's response and the updated history of interactions.

Abstracted example JSON:
```
#JSON
{   "response": "I'm doing great!", 
    "history":{"Hello, how are you?", "I'm doing great!"}
}
```

Provide the history in the next query in order to continue a conversation.

## Customization
A couple examples on how to customize the existing behaviour:
### Roleplay Scenarios
You want to interact with a wise alien, modify the SYSTEM Prompt in the template:
```
prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a friendly alien, full of wisdom and goodness. Answer all questions to the best of your ability.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
```
### Temperature
The temperature parameter adjusts the randomness of predictions by scaling logits, with lower temperatures making predictions more deterministic and higher temperatures making them more diverse.
Lowering the temperature parameter makes answers more coherent and consistent with the context, ensuring predictable and logical responses. Conversely, higher temperatures increase the randomness, leading to more diverse and creative answers. Furthermore, you can set the model you would like to use for inference, see [Supported Models](https://console.groq.com/docs/models).
```
model = ChatGroq(model="llama3-8b-8192", api_key=api_key, temperature=0.7)
```

### History trimming
The history length is currently set to 500 tokens, the more you provide, the more it will remember (up to the maximal context of the model), yet it makse queries more expensive. (once Groq is not free of charge).
Currently, the last message will be removed in case the history grows beyond 500 tokens in length.
See the [Documentation](https://python.langchain.com/docs/how_to/trim_messages/) for more information on trimming policies.
```
trimmer = trim_messages(
    max_tokens=500,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
    )
```



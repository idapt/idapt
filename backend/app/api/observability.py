def init_observability():
    from llama_index.core import set_global_handler
    # Use a simple terminal observability handler for now
    # This will print the chat engine logs to the terminal
    set_global_handler("simple")
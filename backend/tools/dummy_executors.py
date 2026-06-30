

def run_text_node(inputs,data):
    print("this is the text node")
    return data.get("text","")

def run_llm_node(inputs,data):
    print("this is the llm node")
    return f":{inputs}"

def run_create_folder_node(inputs,data):
    print("this is the create folder node")
    return inputs

def run_output_node(inputs,data):
    print("this is the output node")
    return data.get("output","")


NODE_EXECUTORS = {
    "text" : run_text_node,
    "llm" : run_llm_node,
    "create_folder" : run_create_folder_node,
    "output" : run_output_node
}
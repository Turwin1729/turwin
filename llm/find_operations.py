from openai import OpenAI
import yaml
import os

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def classify_operation_with_llm(method, summary, description):
    api_key = os.environ['API_KEY']
    client = OpenAI(api_key=api_key)
    prompt = f"""
    Given an API operation with the following details:
    - HTTP Method: {method}
    - Summary: {summary}
    - Description: {description}

    Categorize it into one of these:
    - "Create Operation" (if it creates a new resource)
    - "Discover Operation" (if it retrieves or lists data)
    - "Update Operation" (if it modifies an existing resource)
    - "Other" (if it does not fit the above categories, e.g., logout, delete)

    Return only the category name without any extra text.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        category = response.choices[0].message.content.strip()
        return category
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return "Other"


def filter_operations(openapi_spec):
    if "paths" not in openapi_spec:
        print("Invalid OpenAPI spec: Missing 'paths' section.")
        return None

    filtered_paths = {}

    for path, methods in openapi_spec["paths"].items():
        new_methods = {}

        for method, details in methods.items():
            operation_id = details.get("operationId", "Unknown Operation")
            summary = details.get("summary", "No summary provided")
            description = details.get("description", "No description provided")

            # Ask OpenAI to classify this operation
            category = classify_operation_with_llm(method.upper(), summary, description)

            # Keep only relevant categories
            if category in ["Create Operation", "Discover Operation", "Update Operation"]:
                new_methods[method] = details

        # If this path has at least one valid operation, keep it
        if new_methods:
            filtered_paths[path] = new_methods

    # Construct the new OpenAPI spec
    new_spec = {
        "openapi": openapi_spec.get("openapi", "3.0.1"),
        "info": openapi_spec.get("info", {}),
        "servers": openapi_spec.get("servers", []),
        "paths": filtered_paths,
        "components": openapi_spec.get("components", {})
    }

    return new_spec


def save_yaml(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    input_yaml = "pet.yaml"  # Replace with your actual OpenAPI file
    output_yaml = "filtered_openapi.yaml"

    openapi_spec = load_yaml(input_yaml)

    if openapi_spec:
        filtered_spec = filter_operations(openapi_spec)
        if filtered_spec:
            save_yaml(filtered_spec, output_yaml)
            print(f"✅ Filtered OpenAPI spec saved as {output_yaml}")
        else:
            print("❌ No valid operations found after filtering.")
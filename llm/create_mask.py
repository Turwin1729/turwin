import json
import base64
import xml.etree.ElementTree as ET
import pandas as pd
from openai import OpenAI
import os

with open("openapi.json", "r") as f:
    openapi_spec = json.load(f)

api_key = os.environ['API_KEY']
client = OpenAI(api_key=api_key)

def decode_base64(encoded_data):
    """Decodes a Base64 string into plain text."""
    try:
        return base64.b64decode(encoded_data).decode(errors="ignore")
    except Exception:
        return ""

def get_schema_for_endpoint(endpoint_path):
    """
    Retrieves the expected schema from the OpenAPI spec for a given endpoint.
    Expands any $ref references to return the final, merged schema.
    """
    paths = openapi_spec.get("paths", {})
    
    # Attempt to match the endpoint path by ignoring path variables
    normalized_path = endpoint_path
    for path in paths:
        if path.replace("{", "").replace("}", "") in endpoint_path:
            normalized_path = path
            break

    endpoint_info = paths.get(normalized_path, {})
    for method, details in endpoint_info.items():
        if "responses" in details:
            for status, response_info in details["responses"].items():
                content = response_info.get("content", {})
                if "application/json" in content:
                    schema_ref = content["application/json"]["schema"]
                    return resolve_schema(schema_ref)

    return None

def resolve_schema(schema):
    """
    Recursively resolves $ref schemas in the OpenAPI spec.
    Merges nested properties (like items, properties, etc.) so that
    the final schema is fully expanded (no $ref stubs).
    """
    if not isinstance(schema, dict):
        return schema

    # If the entire schema is a $ref
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]  # e.g. 'User'
        resolved = openapi_spec["components"]["schemas"].get(ref_name, {})
        return resolve_schema(resolved)

    # Recursively resolve fields like items, properties, additionalProperties, etc.
    for key, value in list(schema.items()):
        if isinstance(value, dict):
            schema[key] = resolve_schema(value)
        elif isinstance(value, list):
            schema[key] = [resolve_schema(item) for item in value]

    return schema

def mask_response_with_schema(response_text, schema):
    """
    Uses an LLM to format the API response according to the expected schema and returns a string.
    """
    prompt = f"""
    Format this JSON response according to the provided schema.
    
    Schema:
    {json.dumps(schema, indent=2)}

    Response:
    {response_text}

    Ensure:
    - All fields from the schema are included.
    - If a field is missing, use `null` if nullable, otherwise provide a default value.
    - Extra fields should be removed.
    
    Return the result as a JSON string.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0
        )
        masked_response = response.choices[0].message.content.strip()
        
        # Ensure response is returned even if empty
        return masked_response if masked_response else "❌ LLM returned an empty response"
    except Exception as e:
        return f"❌ LLM Error: {e}"

def parse_xml_and_mask(file_path):
    """
    Parses the API log (XML) and applies masking based on the expanded OpenAPI schema.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    data = []

    for item in root.findall("item"):
        request_elem = item.find("request")
        response_elem = item.find("response")
        url_elem = item.find("url")
        
        # Decode request and response
        decoded_response = decode_base64(response_elem.text.strip()) if response_elem is not None else ""
        request_url = url_elem.text.strip() if url_elem is not None else ""

        # Extract API path from the URL
        endpoint_path = request_url.split("://")[-1].split("/", 1)[-1]
        if "?" in endpoint_path:
            endpoint_path = endpoint_path.split("?")[0]  # Remove query params

        # Get expected (expanded) schema from OpenAPI
        expanded_schema = get_schema_for_endpoint(f"/{endpoint_path}")

        # Debugging: Print expanded schema so you can confirm "role" is included

        if expanded_schema and decoded_response:
            masked_response = mask_response_with_schema(decoded_response, expanded_schema)
            data.append([endpoint_path, masked_response])

    return data

def create_masked_table(file_path):
    """
    Generates a masked API response table from an XML log.
    """
    masked_data = parse_xml_and_mask(file_path)
    df = pd.DataFrame(masked_data, columns=["Endpoint", "Masked Response"])
    print("\n🔹 Masked API Response Table:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    xml_file = "turwin1.xml"  # Replace with your actual XML file
    create_masked_table(xml_file)
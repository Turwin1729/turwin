import os
import base64
import xml.etree.ElementTree as ET
import json
from urllib.parse import urlparse, parse_qs
import pandas as pd
from openai import OpenAI

api_key = os.environ('API_KEY')
client = OpenAI(api_key=api_key)

def decode_base64(encoded_data):
    """Decodes a Base64 string into plain text."""
    try:
        return base64.b64decode(encoded_data).decode(errors="ignore")
    except Exception:
        return ""

def extract_objects_from_request_llm(request_text):
    """
    Extracts explicit input objects from the request.
    Returns a structured JSON response.
    """
    prompt = f"""
    Identify explicit input values in this HTTP request. Extract:
    1. Resource IDs from paths
    2. Authentication data (decoded if JWT)
    3. Query parameters
    4. Body data
    Ignore headers and metadata. Just give me an array string and nothing else.
    ---
    {request_text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0
        )
        print(response.choices[0].message.content.strip())
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ LLM Error (Object Extraction): {e}")
        return {}

def classify_crud_with_llm(method, response_text, objects):
    """
    Classifies API request as Create (C), Read (R), Update (U), or Delete (D).
    """
    prompt = f"""
    Determine if this request is:
    - "C" (Create) if it adds data.
    - "R" (Read) if it retrieves data.
    - "U" (Update) if it modifies data.
    - "D" (Delete) if it removes data.
    
    Details:
    - Method: {method}
    - Objects: {json.dumps(objects, indent=2)}
    - Response (first 500 chars): {response_text[:500]}
    
    Respond with only C, R, U, or D.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ LLM Error (CRUD): {e}")
        return "Unknown"

def classify_permission_with_llm(response_text):
    """
    Determines if an API response is permissive (1) or restrictive (0).
    """
    prompt = f"""
    Determine if this response is permissive:
    - 0 if "Unauthorized", "Forbidden", or "Access Denied".
    - 1 if successful.
    
    Response:
    {response_text}
    
    Reply with 0 or 1.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0
        )
        return int(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"❌ LLM Error (Permission): {e}")
        return 0

def parse_xml_with_llm(file_path):
    """
    Parses an XML API log and extracts:
    - User
    - Explicit input objects
    - CRUD classification
    - Permission status
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    data = []
    user = "User1"

    for item in root.findall("item"):
        method_elem = item.find("method")
        request_elem = item.find("request")
        response_elem = item.find("response")

        method = method_elem.text.strip().upper() if method_elem is not None else "GET"
        decoded_request = decode_base64(request_elem.text.strip()) if request_elem is not None else ""
        decoded_response = decode_base64(response_elem.text.strip()) if response_elem is not None else ""

        objects = extract_objects_from_request_llm(decoded_request)
        crud_operation = classify_crud_with_llm(method, decoded_response, objects)
        is_permissive = classify_permission_with_llm(decoded_response)

        data.append([user, objects, crud_operation, is_permissive])
    
    return data

def create_permission_table(file_path):
    """
    Generates a permission model table from an XML log.
    """
    permission_data = parse_xml_with_llm(file_path)
    df = pd.DataFrame(permission_data, columns=["User", "Explicit Inputs (Objects)", "CRUD", "Permissive"])
    print("\n🔹 Permission Model Table:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    xml_file = "turwin1.xml"  # Replace with your actual XML file
    create_permission_table(xml_file)
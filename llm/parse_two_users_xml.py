import xml.etree.ElementTree as ET
import base64
import os
from openai import OpenAI
import pandas as pd
import json

api_key = os.environ['API_KEY']
client = OpenAI(api_key=api_key)

def decode_base64(encoded_data):
    """Decodes a Base64 string."""
    return base64.b64decode(encoded_data).decode(errors="ignore")


def classify_crud_with_llm(method, path, response_text):
    """
    Uses OpenAI LLM to classify whether an API operation is Create (C), Read (R), Update (U), or Delete (D).
    """
    prompt = f"""
    Analyze the following API request and classify it as one of: 
    - "C" (Create) if it creates a new resource.
    - "R" (Read) if it retrieves data.
    - "U" (Update) if it modifies existing data.
    - "D" (Delete) if it removes data.

    Details:
    - HTTP Method: {method}
    - Endpoint: {path}
    - Response: {response_text[:500]}  # Limit to first 500 characters for efficiency

    Answer with only `C`, `R`, `U`, or `D`.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return "Unknown"

    
def extract_user_requests(file_path, user_id):
    """
    Parses an XML file and extracts all requests made by a specific user.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    user_requests = {}

    for item in root.findall("item"):
        # Assume user ID is stored in the XML (modify this part if needed)
        user = item.find("user")
        if user is None or user.text.strip() != user_id:
            continue  # Skip requests made by other users

        method = item.find("method").text.strip().upper()  # HTTP Method
        path = item.find("path").text.strip()  # API Endpoint

        # Extract and decode Base64 response
        response_elem = item.find("response")
        decoded_response = decode_base64(response_elem.text.strip()) if response_elem is not None else ""

        # Classify CRUD operation and permission
        crud_operation = classify_crud_with_llm(method, path, decoded_response)

        # Store as "permitted" for this user
        user_requests[path] = {
            "method": method,
            "crud": crud_operation,
            "permissive": 1  # Since the user actually made this request
        }

    return user_requests


def create_permission_table(user_a_requests, user_b_requests):
    """
    Generates a permission model table for both users, inferring missing requests as NOT permitted (0).
    """
    all_paths = set(user_a_requests.keys()).union(set(user_b_requests.keys()))

    data = []
    for path in all_paths:
        method = user_a_requests.get(path, user_b_requests.get(path, {})).get("method", "Unknown")
        crud_operation = user_a_requests.get(path, user_b_requests.get(path, {})).get("crud", "Unknown")

        permissive_a = user_a_requests.get(path, {}).get("permissive", 0)
        permissive_b = user_b_requests.get(path, {}).get("permissive", 0)

        data.append([path, method, crud_operation, permissive_a, permissive_b])

    df = pd.DataFrame(data, columns=["Object", "HTTP Method", "CRUD", "Permissive_A", "Permissive_B"])
    return df


def dataframe_to_json(df, output_file=None):
    """
    Converts a Pandas DataFrame into JSON format.

    Parameters:
    - df (pd.DataFrame): The DataFrame to convert.
    - output_file (str, optional): If provided, saves JSON to this file.

    Returns:
    - str: JSON string representation of the DataFrame.
    """
    json_data = df.to_json(orient="records", indent=4)  # Pretty JSON formatting

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_data)
        print(f"✅ JSON data saved to {output_file}")

    return json_data


if __name__ == "__main__":
    # Load both users' request logs (assuming two separate XML files)
    xml_file_a = "userA_requests.xml"
    xml_file_b = "userB_requests.xml"

    # Extract requests made by each user
    user_a_requests = extract_user_requests(xml_file_a, "UserA")
    user_b_requests = extract_user_requests(xml_file_b, "UserB")

    # Create and display the permission model
    df = create_permission_table(user_a_requests, user_b_requests)
    print("\n🔹 Permission Model Table for Both Users:")
    print(df.to_string(index=False))

    # If want to convert to json
    dataframe_to_json(df, "permission_table.json")
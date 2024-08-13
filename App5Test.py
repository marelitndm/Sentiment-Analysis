import streamlit as st
import pandas as pd
import json
from openai import OpenAI
from google.oauth2 import service_account
import gspread
from datetime import datetime

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Function to authenticate and connect to Google Sheets
def authenticate_and_connect():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["google"], 
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return creds

# Function to call OpenAI API
def openai_api(page_text, system_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": page_text}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=messages,
            temperature=0,
            max_tokens=2000,
            n=1,
            stop=None,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        return None

# Streamlit app
st.title("Project Sentiment Survey Data Analysis App")

# Company name input
company_name = st.text_input("Enter company name:")

# File upload
uploaded_file = st.file_uploader("Upload CSV file", type="csv")

# Submit button
if st.button("Submit"):
    if not company_name or not uploaded_file:
        st.error("Please enter company name and upload a CSV file.")
    else:
        # Read CSV file
        df = pd.read_csv(uploaded_file)
        
        # Read prompt2.txt
        with open('prompt2.txt', 'r') as file:
            system_prompt = file.read()
        
        # Prepare the prompt by appending CSV data
        csv_data = df.to_csv(index=False)
        user_prompt = f"Analyze the following survey data and provide insights in the json format provided:\n\n{csv_data}"
        
        # Call OpenAI API
        with st.spinner("Analyzing data..."):
            json_response = openai_api(user_prompt, system_prompt)
        
        # Parse JSON response
        if json_response:
            try:
                parsed_json = json.loads(json_response)
                st.success("Analysis complete!")
                
                # Connect to Google Sheets
                credentials = authenticate_and_connect()
                gc = gspread.authorize(credentials)
                sheet_id = "1vmXKxxE4ROfrKK2X7LWo55YTf9KWCchYekynVn0yo0Y"
                sh = gc.open_by_key(sheet_id)
                worksheet = sh.sheet1
                
                # Prepare data for Google Sheets
                current_date = datetime.now().strftime("%Y-%m-%d")
                data_to_insert = [
                    current_date,
                    company_name,
                    parsed_json.get("Overview", ""),
                    parsed_json.get("Sentiment Summary Planning Team 1 Header", ""),
                    parsed_json.get("Sentiment Summary Team 1 Text", ""),
                    parsed_json.get("Sentiment Recommendation Team 1 Text", ""),
                    parsed_json.get("Sentiment Summary Planning Team 2 Header", ""),
                    parsed_json.get("Sentiment Summary Team 2 Text", ""),
                    parsed_json.get("Sentiment Recommendation Team 2 Text", ""),
                    parsed_json.get("Sentiment Summary Planning Team 3 Header", ""),
                    parsed_json.get("Sentiment Summary Team 3 Text", ""),
                    parsed_json.get("Sentiment Recommendation Team 3 Text", ""),
                    parsed_json.get("Sentiment Summary Planning Team 4 Header", ""),
                    parsed_json.get("Sentiment Summary Team 4 Text", ""),
                    parsed_json.get("Sentiment Recommendation Team 4 Text", ""),
                    parsed_json.get("Sentiment Summary Planning Team 5 Header", ""),
                    parsed_json.get("Sentiment Summary Team 5 Text", ""),
                    parsed_json.get("Sentiment Recommendation Team 5 Text", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Header", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Header 1", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Text 1", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Header 2", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Text 2", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Header 3", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Text 3", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Header 4", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Text 4", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Header 5", ""),
                    parsed_json.get("Sentiment Summary Planning Macro Trends Text 5", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Header", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Header 1", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Text 1", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Header 2", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Text 2", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Header 3", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Text 3", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Header 4", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Text 4", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Header 5", ""),
                    parsed_json.get("Sentiment Summary Planning Recommendations Based on Trends Text 5", ""),

                    ]
                
                # Append data to Google Sheets
                worksheet.append_row(data_to_insert)
                st.success("Data has been posted to Google Sheets!")
                
            except json.JSONDecodeError:
                st.error("Error parsing JSON response from OpenAI API.")
        else:
            st.error("Failed to get a response from the OpenAI API.")

# Display the JSON response (optional)
if 'parsed_json' in locals():
    st.subheader("JSON Response:")
    st.json(parsed_json)
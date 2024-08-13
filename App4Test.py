import streamlit as st
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
from datetime import datetime

# Display logo
st.image('tndm_logo.png', width=100)

# App title
st.title("Project Sentiment Survey")

# Get client ID from URL parameter
client_id = st.query_params.get("client_id", "")

# Authentication function
@st.cache_resource
def authenticate_and_connect():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["google"], 
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return creds

# Function to extract sheet ID from Google Sheets URL
def extract_sheet_id(url):
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

# Function to get organization sheet
@st.cache_data
def get_org_sheet(client_id):
    try:
        creds = authenticate_and_connect()
        client = gspread.authorize(creds)
        
        # Open the main spreadsheet
        sheet = client.open_by_key("1yyv2GFcJpxx9ghg9uoYN8ENVp17C2VX7WNVtDC-RbAw").worksheet("OrgDatabase")
        
        # Find the row with the matching client ID
        client_cell = sheet.find(client_id, in_column=2)  # Search in column B
        if client_cell:
            row = sheet.row_values(client_cell.row)
            sheet_url = row[2]  # Google Sheet link is in column C
            sheet_id = extract_sheet_id(sheet_url)
            return sheet_id
        return None
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {str(e)}")
        return None


@st.cache_data
def get_unique_teams(sheet_id):
    try:
        creds = authenticate_and_connect()
        client = gspread.authorize(creds)
        
        # Open the client-specific spreadsheet and select the TeamQuestions sheet
        sheet = client.open_by_key(sheet_id).worksheet("TeamQuestions")
        
        # Get all values from column A (Team)
        all_teams = sheet.col_values(1)[1:]  # Skip header row
        
        # Get unique teams and sort them
        unique_teams = sorted(list(set(all_teams)))
        
        return unique_teams
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {str(e)}")
        return []


@st.cache_data
def get_unique_phases(sheet_id):
    try:
        creds = authenticate_and_connect()
        client = gspread.authorize(creds)
        
        # Open the client-specific spreadsheet and select the TeamQuestions sheet
        sheet = client.open_by_key(sheet_id).worksheet("TeamQuestions")
        
        # Get all values from column B (Phase)
        all_phases = sheet.col_values(2)[1:]  # Skip header row
        
        # Get unique phases and sort them
        unique_phases = sorted(list(set(all_phases)))
        
        return unique_phases
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {str(e)}")
        return []
    


    










@st.cache_data
def get_questions(sheet_id, team, phase):
    try:
        creds = authenticate_and_connect()
        client = gspread.authorize(creds)
        
        # Open the client-specific spreadsheet and select the TeamQuestions sheet
        sheet = client.open_by_key(sheet_id).worksheet("TeamQuestions")
        
        # Get all values from the sheet
        all_data = sheet.get_all_values()
        
        # Find the header row and get indices for relevant columns
        header_row = all_data[0]
        team_index = header_row.index("Team")
        phase_index = header_row.index("Phase")
        
        # Find question columns more flexibly
        question_indices = []
        for col in header_row:
            if col.lower().startswith("question"):
                question_indices.append(header_row.index(col))
        
        if len(question_indices) < 4:
            st.error(f"Not enough question columns found. Expected 4, found {len(question_indices)}")
            return None
        
        # Find the row with the matching team and phase
        for row in all_data[1:]:  # Skip header row
            if row[team_index] == team and row[phase_index] == phase:
                return [row[i] for i in question_indices[:4]]  # Return only the first 4 questions
        
        st.warning(f"No questions found for team '{team}' and phase '{phase}'")
        return None
    except Exception as e:
        st.error(f"Error accessing Google Sheets: {str(e)}")
        return None



# Get organization sheet ID
org_sheet_id = get_org_sheet(client_id)


if org_sheet_id:
    # Initialize reset flag if it doesn't exist
    if 'reset_form' not in st.session_state:
        st.session_state.reset_form = False

    # Function to reset form
    def reset_form():
        st.session_state.reset_form = True

    # Input fields
    st.header("Please answer the following questions:")

    # Team selection
    teams = get_unique_teams(org_sheet_id)
    if teams:
        selected_team = st.selectbox("1. What team do you work in?", [""] + teams, index=0 if st.session_state.reset_form else None, key="q0")
    else:
        st.error("Unable to fetch team list. Please try again later.")
        st.stop()

    # Phase selection
    phases = get_unique_phases(org_sheet_id)
    if phases:
        selected_phase = st.selectbox("2. What phase of the project are you in now?", [""] + phases, index=0 if st.session_state.reset_form else None, key="q1")
    else:
        st.error("Unable to fetch phase list. Please try again later.")
        st.stop()

    # Get questions based on selected team and phase
    if selected_team and selected_phase:
        questions = get_questions(org_sheet_id, selected_team, selected_phase)

        if questions:
            # Display the team-specific questions
            for i, question in enumerate(questions):
                key = f"q{i+2}"
                st.text_input(f"{i+3}. {question}", value="" if st.session_state.reset_form else None, key=key)

            # Submit button
            if st.button("Submit"):
                # Function to post answers to the sheet

                
                def post_answers(sheet_id, answers):
                    try:
                        creds = authenticate_and_connect()
                        service = build('sheets', 'v4', credentials=creds)
        
                         # Add date stamp to the beginning of the answers
                        date_stamp = datetime.now().strftime("%Y/%m/%d")
                        answers_with_date = [date_stamp] + answers
        
                        # Prepare the data to be inserted
                        values = [answers_with_date]
                        body = {'values': values}
        
                         # Append the data to the sheet
                        result = service.spreadsheets().values().append(
                        spreadsheetId=sheet_id, range='A1',
                        valueInputOption='USER_ENTERED', body=body).execute()
        
                        return result
                    except Exception as e:
                        st.error(f"Error posting answers: {str(e)}")
                        return None

                # Collect responses
                responses = [selected_team, selected_phase] + [st.session_state.get(f"q{i}", "") for i in range(2, 6)]

                # Post answers to the sheet
                result = post_answers(org_sheet_id, responses)
                
                if result:
                    st.success("Thank you for your feedback!")
                    # Reset the form
                    reset_form()
                else:
                    st.error("There was an error submitting your response. Please try again.")

            # Reset the reset_form flag at the end of the script
            if st.session_state.reset_form:
                st.session_state.reset_form = False
        else:
            st.warning("No questions found for the selected team and phase. Please try a different combination.")
    else:
        st.info("Please select both a team and a phase to view the questions.")

else:
    st.error("Invalid client ID or error accessing the database. Please check the URL and try again.")
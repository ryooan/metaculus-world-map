import requests
import csv

# Your auth token (replace with the actual token string)
auth_token = '4d39dd5fb8fcca0107fff5f492c488c0a19c456a'

# The header that includes the auth token
headers = { 'Authorization' : "Token %s" % auth_token }

# Initialize API URL
urls = {
    "api_data": "https://www.metaculus.com/api2/questions/18274/",
    "r_nominee": "https://www.metaculus.com/api2/questions/11370/",
    "d_nominee": "https://www.metaculus.com/api2/questions/11379/"
}

# Fetch API data

for url_name, url in urls.items():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Failed to get data. HTTP status code: {response.status_code}")
        exit(1)

    # Extract information
    page_url = data.get("page_url", "N/A")
    title = data.get("title", "N/A")

    sub_questions = data.get("sub_questions", [])

    # Prepare data for CSV
    csv_data = []

    # Write header
    csv_data.append(["page_url", "title", "sub_question_id", "sub_question_label", "active", "median"])

    # Add data
    for sub_question in sub_questions:
        sub_question_id = sub_question.get("id", "N/A")
        sub_question_label = sub_question.get("sub_question_label", "N/A")
        active_state = sub_question.get("active_state", "N/A")
        community_prediction = sub_question.get("community_prediction", {}).get("full", {}) if sub_question.get("community_prediction", {}) else {}
        q2 = community_prediction.get("q2", "N/A")

        csv_data.append([page_url, title, sub_question_id, sub_question_label, active_state, q2])

    # Write to CSV
    csv_filename = f"{url_name}.csv"
    with open(csv_filename, "w", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(csv_data)

    print(f"CSV file has been written for {url_name}.")
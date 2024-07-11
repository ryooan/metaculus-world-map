import requests
import csv
import os
from dotenv import load_dotenv
load_dotenv()

# The header that includes the auth token
headers = { 'Authorization' : "Token %s" % os.environ.get('AUTH_TOKEN') }
    
# Initialize API URL
base_url = 'https://www.metaculus.com/api2/questions/?include_description=true'

# Prepare data for CSV
csv_data = []
# Write header
csv_data.append(["page_url", "title", "type", "question_id", "activity", "sub_question_label", "active", "median", "resolution_criteria", "fine_print", "fan_graph", "parent_question", "category_ids"])

loopcounter = 0
offset = 0  # Initialize offset
limit = 100  # Number of records per request
seen_ids = set()

while True:

    if loopcounter == 0:
        url = f"{base_url}&limit={limit}"
        print("Fetching data with no offset")
    else:
        url = f"{base_url}&limit={limit}&offset={offset}"
        print(f"Fetching data with offset {offset}")
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Failed to get data. HTTP status code: {response.status_code}")
        break
    
    results = data.get("results", [])
    if not results:
        print("No more results.")
        break  # Exit the loop if no more results are returned
    
    for row in results:
        # Extract information
        custom_group = row.get("group", "N/A")

        #check if it's a subquestion. If custom_group is a value it is.
        # In that case it will be picked up in the subquestion portion later.
        if custom_group is None:
            page_url = row.get("page_url", "N/A")
            title = row.get("title", "N/A")
            q_type = row.get("type", "N/A")
            question_id = row.get("id", "N/A")
            activity = row.get("activity", "N/A")
            active_state = row.get("active_state", "N/A")
            community_prediction = row.get("community_prediction", {}).get("full", {}) if row.get("community_prediction", {}) else {}
            q2 = community_prediction.get("q2", "N/A") if community_prediction else "N/A"
            resolution_text = row.get("resolution_criteria", "N/A")
            fine_print_text = row.get("fine_print", "N/A")
            fan_graph = row.get("has_fan_graph", "N/A")
            category_ids = [category['id'] for category in row.get('categories', [])]

            category_ids_str = ';'.join(category_ids)

            csv_data.append([page_url, title, q_type, question_id, activity, "", active_state, q2, resolution_text, fine_print_text, fan_graph, "", category_ids_str])

            sub_questions = row.get("sub_questions", [])
            
            # Add data
            for sub_question in sub_questions:
                if sub_question is None:
                    continue
                else:
                    sub_question_id = sub_question.get("id", "N/A")
                    sub_question_label = sub_question.get("sub_question_label", "N/A")
                    active_state = sub_question.get("active_state", "N/A")
                    community_prediction = sub_question.get("community_prediction", {}) if sub_question is not None else {}
                    full_prediction = community_prediction.get("full", {}) if community_prediction is not None else {}
                    q2 = full_prediction.get("q2", "N/A") if full_prediction else {}
                    
                    if sub_question_id not in seen_ids:
                        seen_ids.add(sub_question_id)
                        csv_data.append([page_url, title, "", sub_question_id, "", sub_question_label, active_state, q2, "", "", "", question_id, ""])

    offset += limit  # Increment the offset for the next batch
    loopcounter += 1

#get question ids for comparisons
#make sure to include ? and & as appropriate (limit or limit and offset will be appended without any symbol before the first one)
match_urls = {
    "public_questions": "https://www.metaculus.com/api2/questions/?",
    "electionsExact": "https://www.metaculus.com/api2/questions/?search=\" election\"&",
    "electionsSearch": "https://www.metaculus.com/api2/questions/?search=elect&",
}

category_search = {
    "ai": "artificial-intelligence",
    "cryptocurrencies": "cryptocurrencies",
    "economy": "economy-business",
    "environment": "environment-climate",
    #elections is handled separately, via a search, since category was not always used in the past.
    "geopolitics": "geopolitics",
    "health": "health-pandemics",
    "law": "law",
    "nuclear": "nuclear",
    "politics": "politics",
    "space": "space",
    "sports": "sports-entertainment",
    "technology": "technology",
}

comparison_data = {url_name: [] for url_name in match_urls}  # Dictionary to hold lists of data

# Fetch API data

for url_name, url in match_urls.items():

    loopcounter = 0
    offset = 0  # Initialize offset
    limit = 100  # Number of records per request

    while True:

        if loopcounter == 0:
            request_url = f"{url}limit={limit}"
            print(f"{url_name}: Fetching data with no offset")
        else:
            request_url = f"{url}limit={limit}&offset={offset}"
            print(f"{url_name}: Fetching data with offset {offset}")
        
        print(request_url)
        response = requests.get(request_url)
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"{url_name}: Failed to get data. HTTP status code: {response.status_code}")
            break
        
        results = data.get("results", [])
        if not results:
            print("No more results.")
            break  # Exit the loop if no more results are returned
        
        for row in results:

            custom_group = row.get("group", "N/A")

            #check if it's a subquestion. If custom_group is a value it is.
            # In that case it will be picked up in the subquestion portion later.
            if custom_group is None:
                question_id = str(row.get("id", "N/A"))
            
                comparison_data[url_name].append(question_id)

        offset += limit  # Increment the offset for the next batch
        loopcounter += 1

    # Write to CSV
    csv_filename = f"{url_name}.csv"
    with open(csv_filename, "w", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(comparison_data[url_name])

    print(f"CSV file has been written for {url_name}.")

#make custom comparison_data as needed
exact_values = set(comparison_data["electionsExact"])
search_values = set(comparison_data["electionsSearch"])

combined_unique_values = exact_values.union(search_values)

comparison_data["elections"] = list(combined_unique_values)

print("Keys before deletion:", comparison_data.keys())

#delete the below after combining
del comparison_data['electionsExact']
del comparison_data['electionsSearch']

print("Keys after deletion:", comparison_data.keys())

csv_data[0].extend(list(comparison_data.keys()))
csv_data[0].extend(list(category_search.keys()))

question_id_idx = csv_data[0].index('question_id')
parent_idx = csv_data[0].index('parent_question')

# Loop over csv_data and append the new columns for matches
for row in csv_data[1:]:  # Skip the header row
    question_id = str(row[question_id_idx])
    parent_question = str(row[parent_idx])

    # Check for matches in public_questions and elections
    for key in comparison_data.keys():
        match = "True" if question_id in comparison_data[key] or parent_question in comparison_data[key] else ""
        row.append(match)

category_idx = csv_data[0].index('category_ids')

# Loop over csv_data and append the new columns for matches
for row in csv_data[1:]:  # Skip the header row
    categories = row[category_idx].split(';')

    for search_category, search_ids in category_search.items():
        category_ids_list = [id.strip() for id in search_ids.split(',')]
        row.append('True' if any(category_id == category for category_id in category_ids_list for category in categories) else '')

#remove all rows where "public_questions" is not true
public_questions_idx = csv_data[0].index('public_questions')
csv_data = [csv_data[0]] + [row for row in csv_data[1:] if row[public_questions_idx].lower() == 'true']

# Write to CSV
csv_filename = "questions_list.csv"
with open(csv_filename, "w", newline='', encoding='utf-8') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(csv_data)

print(f"CSV file has been written.")
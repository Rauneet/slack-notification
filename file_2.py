import requests
import datetime
from pytz import timezone
import pprint
import calendar
import time 

# Constants 
CLICKUP_API_TOKEN = 'pk_73223342_17LY9UC6TE84D6P5MF2ALXU5W8UT6LHA'  #clickup api token
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'  #slack webhook url
CLICKUP_API_ENDPOINT = 'https://api.clickup.com/api/v2'       #clickup api endpoint
HEADERS = {
    'Authorization': CLICKUP_API_TOKEN
    }
SECONDS_IN_AN_HOUR = 3600


# Function to check whether it is night time or not 
# Working hour is defined from 9 AM to 9 PM
def is_night_time():
    tz = timezone('Asia/Kolkata')
    current_time = datetime.datetime.now(tz)
    return not 9 <= current_time.hour <= 21

def send_message_slack(message):
    payload = {
        'text' : message
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    return response.status_code == 200

def get_tasks_and_notify(list_id, list_name):
    if is_night_time():
        return            # Skip execution during night time

    response = requests.get(f'{CLICKUP_API_ENDPOINT}/list/{list_id}/task', headers=HEADERS)
    if response.status_code != 200:
        return             # Exit if tasks cannot be fetched

    tickets = response.json().get('tasks', [])
    for ticket in tickets:
        # is_bug = False
        # for field in ticket.get('custom_field', []):                                                      #this logic for checking the bug is working 
        #     if field.get('name').strip() == 'Request Type' and field.get('value','').strip() == 'Bug':
        #         is_bug = True
        #         print(f"Found a Bug for Ticket ID: {ticket['id']}")
        #         break
        # if not is_bug:
        #     print(f"Skipping Ticket ID: {ticket['id']} as it's not marked as a Bug.")
        #     continue

        status_type = ticket.get('status', {}).get('status', '').lower().replace(" ", "")
        #print(f"Debug - Ticket ID: {ticket['id']} Status: {status_type}") 
        priority = ticket.get('priority')    #get to the priority object  and then access the attribute value
        # retrieves the ticket priority in lowercase for better consistency default to none if priority is not set 
        priority_type = priority.get('priority', '').lower() if priority and isinstance(priority, dict) else 'none'
        
        # Check for desired status and priority
        if status_type in ['open','inprogress','pending(ack)'] and priority_type in ['high', 'urgent']:
            task_id = ticket['id']
         # Fetches comments for a given task from ClickUp   
            comment_response = requests.get(f'{CLICKUP_API_ENDPOINT}/task/{task_id}/comment', headers=HEADERS)
            if comment_response.status_code == 200:
                # Extracts the list of comments
                comments = comment_response.json().get('comments' ,[])
                pprint.pprint(comments)
                # Checks if there are more than two comments on the task.
                if len(comments) >2:
                    print(f"Task ID: {task_id} has more than two comments, no action needed.")
                    continue
                #checks if there are comments and check the time of the last comment 
                if comments:
                     # Converts the timestamp of the last comment from milliseconds to seconds for comparison.
                    last_comment_timestamp = int(comments[0]['date']) // 1000
                    #check for the current time 
                    current_time = time.time()
                    # Checks if the last comment was made more than 2 hours ago.
                    if(current_time - last_comment_timestamp) > 7200:
                        message = f'Ticket ID: {task_id} from list "{list_name}" with status "{status_type}" and priority "{priority_type}"  https://app.clickup.com/t/{task_id} requires attention.'
                        if send_message_slack(message):
                            print(f'Success !!')
                        else:
                            print(f'Failed to send notification!!')
                    else:
                        print(f'No need to notify as last comment was made within 2 hours')   # Last comment was within 2 hours, no notification needed.
                else:
                    print(f'No comments in the ticket is made')   # No comments have been made on the task.
            else:
                print(f'failed to fetch ticket comments')    #Failed to fetch the task comments
            
                    
# retrieves the lists from the specific folder in the clickup
def get_list(folder_id):
    response = requests.get(f'{CLICKUP_API_ENDPOINT}/folder/{folder_id}/list', headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('lists', [])
    return []

# retrieves all the ticket/task from the specific list and also get the list name and list id and call the get_task_and_notify() for processing each ticket in the list
def get_tickets_from_customer_lists(folder_id):
    lists = get_list(folder_id)
    for list_item in lists:
        list_name, list_id = list_item.get('name'), list_item.get('id')
        print(f'Fetching tickets for list: {list_name}')
        get_tasks_and_notify(list_id,list_name)

if not is_night_time():
    # it will check for new tickets every 60 min
    while True:                          #1
        print('checking for new tickets to notify')  #2
        get_tickets_from_customer_lists("109448264")
        print(f"Waiting for {SECONDS_IN_AN_HOUR // 60} minutes until the next check.")  #3  
        time.sleep(SECONDS_IN_AN_HOUR)  #4
else:
    print("It's night time. No operations will be performed.")

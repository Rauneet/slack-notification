<<<<<<< HEAD
# import requests
# import datetime
# from pytz import timezone
# import pprint
# import calendar
# import time 

# # Constants 
# CLICKUP_API_TOKEN = 'pk_73223342_17LY9UC6TE84D6P5MF2ALXU5W8UT6LHA'  #clickup api token
# SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'  #slack webhook url 
# CLICKUP_API_ENDPOINT = 'https://api.clickup.com/api/v2'       #clickup api endpoint
# HEADERS = {'Authorization': CLICKUP_API_TOKEN}

=======
import requests
import json
import datetime
from pytz import timezone
import pprint
import calendar
import time
from dotenv import load_dotenv
import os

load_dotenv()       #this will load the environment variables from .env file
#dictionary to keep track of notified tickets 
notified_tickets = set()


# Constants 
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')                                                                                            #'pk_73223342_17LY9UC6TE84D6P5MF2ALXU5W8UT6LHA'  #clickup api token
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')                                                                                            #'https://hooks.slack.com/triggers/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'  #slack webhook url-'https://hooks.slack.com/services/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'- previous webhook
CLICKUP_API_ENDPOINT = 'https://api.clickup.com/api/v2'    #clickup api endpoint    
HEADERS = {
    'Authorization': CLICKUP_API_TOKEN
    }
SECONDS_IN_AN_HOUR = 3600
>>>>>>> 867e33fc7523a31ed6fc482f34367b6d81e80756

# # Function to check whether it is night time or not 
# # Working hour is defined from 9 AM to 9 PM
# def is_night_time():
#     tz = timezone('Asia/Kolkata')
#     current_time = datetime.datetime.now(tz)
#     return not 9 <= current_time.hour <= 21

<<<<<<< HEAD
# def send_message_slack(message):
#     payload = {
#         'text' : message
#     }
#     response = requests.post(SLACK_WEBHOOK_URL, json=payload)
#     return response.status_code == 200

# def get_tasks_and_notify(list_id , list_name):                     #list name is included
#     if is_night_time():
#         return            # Skip execution during night time
=======

def send_message_slack(message, task_url):
    full_message = f'{message} Ticket URL:'
    payload = {
        'full_message' : full_message,
        'task_url': task_url
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=payload, headers=headers)
    return response.status_code == 200

def is_bug_based_on_comment(comments):
    bot_comment_count = 0                    #initialize the bot comment count to 0
    for comment in comments:                 #iterate through each commets
        if comment['user']['id'] == -1:      #checks if the id of the comment is -1
            bot_comment_count +=1            #if it is -1 increase the bot_comment_count
    if bot_comment_count>=1:                 #checks if the comment is greater than equal to 2
    #if true consider it as a bug based on comment  
        return True
    else:
        return False     #it is not a bug based on comment

# def is_request_type_bug(custom_fields):
#     for field in custom_fields:
#         if field.get('name') == 'Request Type ':
#             bug_option_id = None
#             for option in field.get('type_config', {}).get('option', []):
#                 if option.get('name').lower() == 'bug':
#                     bug_option_id = option.get('id')
#                     break
#             if bug_option_id and str(field.get('value')) == str(bug_option_id):
#                 return True
#     return False
# def is_recent_tickets(ticket, days=30):
#     ticket_updated = datetime.datetime.fromtimestamp(int(ticket['date_updated'])/1000)
#     return datetime.datetime.now() - ticket_updated < datetime.timedelta(days=days)

def get_tasks_and_notify(list_id, list_name):
    global notified_tickets                                   #global notified_tickets dictionary for storing the ticket id which have been notified 
    if is_night_time():
        return            # Skip execution during night time
>>>>>>> 867e33fc7523a31ed6fc482f34367b6d81e80756

#     response = requests.get(f'{CLICKUP_API_ENDPOINT}/list/{list_id}/task', headers=HEADERS)
#     if response.status_code != 200:
#         return             # Exit if tasks cannot be fetched

<<<<<<< HEAD
#     tickets = response.json().get('tasks', [])
#     for ticket in tickets:
#         # is_bug = False
#         # for field in ticket.get('custom_field', []):                                                      #this logic for checking the bug is working 
#         #     if field.get('name').strip() == 'Request Type' and field.get('value','').strip() == 'Bug':
#         #         is_bug = True
#         #         print(f"Found a Bug for Ticket ID: {ticket['id']}")
#         #         break
#         # if not is_bug:
#         #     print(f"Skipping Ticket ID: {ticket['id']} as it's not marked as a Bug.")
#         #     continue

#         status_type = ticket.get('status', {}).get('status', '').lower().replace(" ", "")
#         #print(f"Debug - Ticket ID: {ticket['id']} Status: {status_type}") 
#         priority = ticket.get('priority')    #get to the priority object  and then access the attribute value
#         # retrieves the ticket priority in lowercase for better consistency default to none if priority is not set 
#         priority_type = priority.get('priority', '').lower() if priority and isinstance(priority, dict) else 'none'
        
#         # Check for desired status and priority
#         if status_type in ['open','inprogress','pending(ack)'] and priority_type in ['high', 'urgent']:
#             task_id = ticket['id']
#          # Fetches comments for a given task from ClickUp   
#             comment_response = requests.get(f'{CLICKUP_API_ENDPOINT}/task/{task_id}/comment', headers=HEADERS)
#             if comment_response.status_code == 200:
#                 # Extracts the list of comments
#                 comments = comment_response.json().get('comments' ,[])
#                 pprint.pprint(comments)
#                 # Checks if there are more than two comments on the task.
#                 if len(comments) > 2:
#                     print(f"Task ID: {task_id} has more than two comments, no action needed.")
#                     continue
#                 #checks if there are comments and check the time of the last comment 
#                 if comments:
#                      # Converts the timestamp of the last comment from milliseconds to seconds for comparison.
#                     last_comment_timestamp = int(comments[0]['date']) // 1000
#                     #check for the current time 
#                     current_time = time.time()
#                     # Checks if the last comment was made more than 2 hours ago.
#                     if(current_time - last_comment_timestamp) > 7200:                               #in actual it is 2 hrs ie 7200 seconds
#                         message = f'Ticket ID: {task_id} in list "{list_name}" with status "{status_type}" and priority "{priority_type}"  https://app.clickup.com/t/{task_id} requires attention.'   #in actual message it is {list_name}
#                         if send_message_slack(message):
#                             print(f'Success !!')
#                         else:
#                             print(f'Failed to send notification!!')
#                     else:
#                         print(f'No need to notify as last comment was made within 2 hours')   # Last comment was within 2 hours, no notification needed.
#                 else:
#                     print(f'No comments in the ticket is made')   # No comments have been made on the task.
#             else:
#                 print(f'failed to fetch ticket comments')    #Failed to fetch the task comments
=======
    tickets = response.json().get('tasks', [])
    for ticket in tickets:
        task_id = ticket['id']                                                                         #till here 
        task_url = ticket.get('url')     #this line will remain
        if task_id in notified_tickets:      #checks if the ticket is in notified_tickets dictionary if not present it will again continue 
            continue
        # print(task_url)                            #for debugging
        # is_bug = False
        # for field in ticket.get('custom_fields', []):
        #     if field.get('name') == 'Request Type ':
        #         if 'value' in field and field.get('value') is not None:
        #             for option in field.get('type_config', {}).get('options', []):
        #                 if option.get('name').lower() == 'bug' and str(field.get('value')) == str(option.get('id')):
        #                     is_bug = True
        #                     break
        #         break
        # if is_bug:
        #     task_url = ticket.get('url')
        #     print(f"Bug Ticket URL: {task_url}")
            
                   

        status_type = ticket.get('status', {}).get('status', '').lower().replace(" ", "")
        #print(f"Debug - Ticket ID: {ticket['id']} Status: {status_type}") 
        priority = ticket.get('priority')    #get to the priority object  and then access the attribute value
        # retrieves the ticket priority in lowercase for better consistency default to none if priority is not set 
        priority_type = priority.get('priority', '').lower() if priority and isinstance(priority, dict) else 'none'
        
        # Check for desired status and priority
        if status_type in ['open','inprogress','pending(ack)'] and priority_type in ['high', 'urgent']:
            # task_id = ticket['id']
            # task_url = f"https://app.clickup.com/t/{task_id}"
         # Fetches comments for a given task from ClickUp   
            comment_response = requests.get(f'{CLICKUP_API_ENDPOINT}/task/{task_id}/comment', headers=HEADERS)
            if comment_response.status_code == 200:
                # Extracts comments
                comments = comment_response.json().get('comments' ,[])
                if is_bug_based_on_comment(comments):
                #filter the comments made by bot
                    user_comments = [comment for comment in comments if comment['user']['id'] != -1]
                    pprint.pprint(comments)
                # Checks if there are more than two comments on the task.
                    if len(user_comments) > 2:
                        print(f"Task ID: {task_id} has more than two user comments, no action needed.")
                        continue
                #checks if there are comments and check the time of the last comment 
                    if user_comments:
                        # Converts the timestamp of the last comment from milliseconds to seconds for comparison.
                        last_comment_timestamp = int(user_comments[-1]['date']) // 1000
                        #check for the current time 
                        current_time = time.time()
                    # Checks if the last comment was made more than 2 hours ago.
                        if(current_time - last_comment_timestamp) > 7200:
                            message = f'Update with latest progress.'  # this is included https://app.clickup.com/t/{task_id}
                        # task_url =  f'https://app.clickup.com/t/{task_id}'    
                            if send_message_slack(message,task_url):                                              
                                print(f'Message being sent' , message)
                                notified_tickets.add(task_id)                                  #[task_id] = True                        #this will mark the ticket as notified true                                        
                            else:
                                print(f'Failed to send notification!!')
                        else:
                            print(f'No need to notify as last comment was made within 2 hours')   # Last comment was within 2 hours, no notification needed.
                    else:
                        print(f'No comments in the ticket is made by user')   # No comments have been made on the task.
                else:
                    print(f'its not a bug based on comment {task_url}')
            else:
                print(f'failed to fetch ticket comments')    #Failed to fetch the task comments
>>>>>>> 867e33fc7523a31ed6fc482f34367b6d81e80756
            
                    
# # retrieves the lists from the specific folder in the clickup
# def get_list(folder_id):
#     response = requests.get(f'{CLICKUP_API_ENDPOINT}/folder/{folder_id}/list', headers=HEADERS)
#     if response.status_code == 200:
#         return response.json().get('lists', [])
#     return []

# # retrieves all the ticket/task from the specific list and also get the list name and list id and call the get_task_and_notify() for processing each ticket in the list
# def get_tickets_from_customer_lists(folder_id):
#     lists = get_list(folder_id)
#     for list_item in lists:
#         list_name, list_id = list_item.get('name'), list_item.get('id')
#         print(f'Fetching tickets for list: {list_name}')
#         get_tasks_and_notify(list_id,list_name)

<<<<<<< HEAD
# if not is_night_time():
#     get_tickets_from_customer_lists('109448264')
# else:
#     print("It's night time. No operations will be performed.")
=======
if not is_night_time():
    # it will check for new tickets every 60 min
    while True:                          #1
        print('checking for new tickets to notify')  #2
        get_tickets_from_customer_lists("109448264")
        print(f"Waiting for {SECONDS_IN_AN_HOUR // 60} minutes until the next check.")  #3  
        time.sleep(SECONDS_IN_AN_HOUR)  #4
else:
    print("It's night time. No operations will be performed.")
>>>>>>> 867e33fc7523a31ed6fc482f34367b6d81e80756

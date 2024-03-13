import requests
import json
import datetime
from pytz import timezone
import pprint
import calendar
import time
from datetime import timedelta
from dotenv import load_dotenv
import os


load_dotenv()       #this will load the environment variables from .env file
#dictionary to keep track of notified tickets 
notified_tickets = set()
# Global list to keep track of tickets for end-of-day summary
end_of_day_tickets = []   #new line
summary_sent_today = False
last_run_date = datetime.datetime.now(tz=timezone('Asia/Kolkata')).date()     #new line


# Constants 
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')                                                                                            #'pk_73223342_17LY9UC6TE84D6P5MF2ALXU5W8UT6LHA'  #clickup api token
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')                                                                                            #'https://hooks.slack.com/triggers/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'  #slack webhook url-'https://hooks.slack.com/services/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'- previous webhook
CLICKUP_API_ENDPOINT = 'https://api.clickup.com/api/v2'    #clickup api endpoint    
HEADERS = {
    'Authorization': CLICKUP_API_TOKEN
    }
SECONDS_IN_AN_HOUR = 3600


#Function to check whether it is night time or not 
#Working hour is defined from 9 AM to 9 PM
def is_night_time():
    tz = timezone('Asia/Kolkata')
    current_time = datetime.datetime.now(tz)
    return not 9 <= current_time.hour <= 21


def send_message_slack(message, task_url): #task_name, list_name):
    full_message = f'{message}'                #Ticket URL:is included in full message
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
    if bot_comment_count >=1:                 #checks if the comment is greater than equal to 2
    #if true consider it as a bug based on comment  
        return True
    else:
        return False     #it is not a bug based on comment


#checks if the tcket is created or updated within last "hours"
def is_ticket_eligible_for_review(ticket,current_time):
    current_time = datetime.datetime.now(datetime.timezone.utc)   #gets the current time and date
    #date_updated = datetime.datetime.fromtimestamp(int(ticket['date_updated']) /1000 , tz=datetime.timezone.utc)
    date_created = datetime.datetime.fromtimestamp(int(ticket['date_created']) /1000 , tz=datetime.timezone.utc)
    two_hours_after_creation = date_created + datetime.timedelta(hours=2)
    return current_time >= two_hours_after_creation
    # updated_recently = (current_time - date_updated) < datetime.timedelta(hours=hours)
    # created_recently = (current_time - date_created) < datetime.timedelta(hours=hours)

def get_tasks_and_notify(list_id, list_name):
    global notified_tickets                                     #global notified_tickets dictionary for storing the ticket id which have been notified         
    current_time = datetime.datetime.now(tz=timezone('Asia/Kolkata'))
    if is_night_time():
        return            # Skip execution during night time


    response = requests.get(f'{CLICKUP_API_ENDPOINT}/list/{list_id}/task', headers=HEADERS)
    if response.status_code != 200:
        return             # Exit if tasks cannot be fetched

    tickets = response.json().get('tasks', [])
    for ticket in tickets:    #here is for ticket in tickets change it after checking 
        task_id = ticket['id']
        task_name = ticket.get('name')   #added ticket name here                                                                        
        task_url = ticket.get('url')
        assignees = ticket.get('assignee', [])
        if assignees:
            assignee_username = assignees[0].get('username', 'Unassigned')
            print(f'Assignee for {task_id} is {assignee_username}')
        if task_id not in notified_tickets and is_ticket_eligible_for_review(ticket, current_time): #checks if the ticket is in notified_tickets set if not present it will again continue 
            status_type = ticket.get('status', {}).get('status', '').lower().replace(" ", "")
            #print(f"Debug - Ticket ID: {ticket['id']} Status: {status_type}") 
            priority = ticket.get('priority')    #get to the priority object
            #retrieves the ticket priority in lowercase for better consistency default to none if priority is not set 
            priority_type = priority.get('priority', '').lower() if priority and isinstance(priority, dict) else 'none'
        
            # Check for desired status and priority
            if status_type in ['open','inprogress','pending(ack)','planned'] and priority_type in ['high', 'urgent']:
            # task_id = ticket['id']
            # task_url = f"https://app.clickup.com/t/{task_id}"
        #Fetches comments for a given task from ClickUp   
                comment_response = requests.get(f'{CLICKUP_API_ENDPOINT}/task/{task_id}/comment', headers=HEADERS)
                if comment_response.status_code == 200:
                #fetch comments
                    comments = comment_response.json().get('comments' ,[])
                    if is_bug_based_on_comment(comments):
                    #end_of_day_tickets.append(task_url)   #new line is added here      #identified as bug and added to the list 
                #filter the comments made by bot
                        user_comments = [comment for comment in comments if comment['user']['id'] != -1]
                        pprint.pprint(user_comments)
                # Checks if there are more than two comments on the task.
                        if len(user_comments) >=1:
                            print(f"Task ID: {task_id} has more than one user comments, no action needed.")
                            continue
                        if not user_comments:
                            ticket_created_timestamp = int(ticket['date_created']) // 1000 
                            ticket_created_timestamp = datetime.datetime.fromtimestamp(ticket_created_timestamp,tz=timezone('Asia/Kolkata'))
                            #ticket_created_timestamp_formatted = datetime.datetime.fromtimestamp(ticket_created_timestamp).strftime('%Y-%m-%d %H:%M')
                            if (current_time - ticket_created_timestamp).total_seconds() >7200:
                                ticket_created_timestamp_formatted = ticket_created_timestamp.strftime('%Y-%m-%d %H:%M')
                                message = f'From Customer: "{list_name}" Ticket headline: "{task_name}" has not recieved update since {ticket_created_timestamp_formatted}. Update with latest progress.'
                                if send_message_slack(message, task_url): #task_name, list_name):
                                    print(f'Message sent for ticket where no user comments are there', message)
                                    notified_tickets.add(task_id)
                                    end_of_day_tickets.append(task_url)
                                else:
                                    print(f'Failed to send notification')
                            else:
                                print(f'Time is not more than 2 hours')
                #checks if there are less than equal to 2 user comments and check the time of the last comment 
                        elif user_comments:   #changed the condition to check the user comments <=2   #used elif instead of if here len(user_coomment)<=2
                        # Converts the timestamp of the last comment from milliseconds to seconds for comparison.
                            last_comment_timestamp = int(user_comments[-1]['date']) // 1000  #if user_comments else 0
                        #added this to get the last update time on the ticket 
                            last_update_time = datetime.datetime.fromtimestamp(last_comment_timestamp, tz=timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M')
                        #check for the current time 
                            current_time = time.time()
                    # Checks if the last comment was made more than 2 hours ago.
                            if (current_time - last_comment_timestamp) > 7200:              #remove this if not user_comments or (included)
                                message = f'From Customer: "{list_name}" Ticket headline: "{task_name}" has not recieved update since {last_update_time}. Update with latest progress.'  #updated the message structure to include the last update time on ticket 
                        # task_url =  f'https://app.clickup.com/t/{task_id}'    
                                if send_message_slack(message, task_url): #task_name, list_name):                                              
                                    print(f'Message being sent' , message)
                                    end_of_day_tickets.append(task_url)
                                    notified_tickets.add(task_id)                                  #[task_id] = True                        #this will mark the ticket as notified true                                                                    
                                else:
                                    print(f'Failed to send notification!!')
                            else:
                                print(f'No need to notify as last comment was made within 2 hours')   # Last comment was within 2 hours, no notification needed.
                        else:
                            print(f'No comments in the ticket is made by user')   # No comments have been made on the task.
                            print()
                    else:
                        print(f'its not a bug based on comment {task_url}') #commented out this but we have to un comment thhis 
                else:
                    print(f'failed to fetch ticket comments')    #Failed to fetch the task comments
                                       
                    
#retrieves the lists from the specific folder in the clickup
def get_list(folder_id):
    response = requests.get(f'{CLICKUP_API_ENDPOINT}/folder/{folder_id}/list', headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('lists', [])
    return []


#retrieves all the ticket from the specific list and also get the list name and list id and call the get_task_and_notify() for processing each ticket in the list
def get_tickets_from_customer_lists(folder_id):
    lists = get_list(folder_id)
    for list_item in lists:
        list_name, list_id = list_item.get('name'), list_item.get('id')
        print(f'Fetching tickets for list: {list_name}')
        get_tasks_and_notify(list_id,list_name)

#Function to send the summary to slack 
def send_summary_slack():
    global end_of_day_tickets, summary_sent_today
    if end_of_day_tickets:
        message = "End of Day Summary: Bug Tickets\n"
        message +="\n".join([f"-{task_url}" for task_url in end_of_day_tickets])
        if send_message_slack(message, None):
            print(f"Summary sent to slack")
            # summary_sent_today = True
            end_of_day_tickets.clear()
        else:
            print('Summary not sent to slack')
    else:
        print(f'No bug tickets for the day')

#checks for new date and resets the sumamry sent today, notified_tickets set and last run date for the new day 
def check_for_new_date():                                                         #new function/new line
    global summary_sent_today, notified_tickets, last_run_date
    current_date = datetime.datetime.now(tz=timezone('Asia/Kolkata')).date()
    if current_date > last_run_date:
        notified_tickets.clear()
        end_of_day_tickets.clear()
        summary_sent_today = False
        last_run_date = current_date
        print('New date detected.. Resetting the notified_tickets and summary_sent_today')

#function to send the summary to slack at particular time and also gives a 10 min buffer time to send summary
def is_time_to_send_summary(current_time):
    current_time = datetime.datetime.now(tz=timezone('Asia/Kolkata'))
    summary_start_time = current_time.replace(hour=18,minute=0,second=0, microsecond=0)   #summary time set at 8:30pm
    summary_end_time = summary_start_time + datetime.timedelta(minutes=10)                 #given 10 minutes buffer time to send summary
    return summary_start_time <= current_time <= summary_end_time    #new line 


#calculates the sleep duration based on the next check time and next summary time whichever is sooner it will return that 
def calculate_sleep_duration():
    current_time = datetime.datetime.now(tz=timezone('Asia/Kolkata'))
    next_check_time = (current_time + datetime.timedelta(minutes=15)).replace(second=0, microsecond=0)
    next_summary_time = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
    if current_time >= next_summary_time:
        next_summary_time = next_summary_time + datetime.timedelta(days=1)
    sleep_duration = min((next_check_time - current_time).total_seconds(), (next_summary_time - current_time).total_seconds())
    return sleep_duration


if not is_night_time():
    # it will check for new tickets every 60 min
    while True:
        check_for_new_date()     #new line
        print('checking for new tickets to notify')  
        get_tickets_from_customer_lists("109448264")                      #folder id here 
        sleep_duration = calculate_sleep_duration()
        print(f'sleeping for {sleep_duration // 60} minutes')
        time.sleep(sleep_duration)
        current_time = datetime.datetime.now(tz=timezone('Asia/Kolkata'))
        if is_time_to_send_summary(current_time) and not summary_sent_today:
            send_summary_slack()
            summary_sent_today = True
            end_of_day_tickets.clear()
        else:
            print('Failed to send summary')
        if current_time.hour == 0 and summary_sent_today:
            summary_sent_today = False
else:
    print('Night time no action needed')

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    




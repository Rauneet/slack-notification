#imports Standard Library
import requests
import time
import datetime
import os
import json
from datetime import timedelta
from dotenv import load_dotenv
from pytz import timezone


load_dotenv()

#Constants 
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
CLICKUP_API_ENDPOINT = 'https://api.clickup.com/api/v2'
HEADERS = {
    'Authorization': CLICKUP_API_TOKEN
}

#timezone setup
TIMEZONE = timezone('Asia/Kolkata')

#state
notified_tickets = set()
end_of_day_tickets = []
last_run_date = datetime.datetime.now(tz=timezone('Asia/Kolkata')).date() 
summary_sent_today = False


def is_night_time():
    """
    Check if the current time is between 9AM to 9PM
    """
    current_time = datetime.datetime.now(TIMEZONE)
    return not 9 <= current_time.hour <= 21

def is_ticket_eligible_for_review(ticket,current_time):
    """
    # Determines if a ticket is eligible for review based on its creation time.
    # This function calculates whether a ticket has been created at least two hours ago from the specified current time.
    # It uses the 'date_created' field from the ticket data, which is a Unix timestamp, converts it to a datetime object,
    # and then checks if the current time is at least two hours after the ticket's creation time.
    # A ticket created at 10:00 AM will be eligible for review after 12:00 PM on the same day.
    """
    date_created = datetime.datetime.fromtimestamp(int(ticket['date_created'])/1000, tz=datetime.timezone.utc)
    two_hours_after_creation = date_created+datetime.timedelta(hours=2)
    return current_time >= two_hours_after_creation


def get_tasks_and_notify(list_id, list_name):
    """
    Retrieves tasks from a specified ClickUp list based on custom field filters and processes each task.

    This function aims to fetch tasks that meet specific criteria from a given ClickUp list. The criteria are defined by custom fields,
    specifically filtering for tasks that represent 'bugs' as defined by the custom field settings. The function performs an API call
    to ClickUp, retrieves the tasks, and then processes each task individually if the API call is successful.

    If the function is called during night time (as determined by is_night_time()), it returns immediately without fetching tasks,
    assuming that no task processing should occur during off-hours.
    """
    if is_night_time():
        return
    custom_fields_filters = json.dumps([
        {"field_id": "af553c42-561b-4260-93b0-ca2afa6b520f", "operator":"=", "value": "2c234b21-fb9a-49ad-bceb-0a342556e213"}  #field id is request type id and value is bug id 
    ])
    params = {
        #"include_closed": "true",    #this will include the tickets whose status is in complete this is not required since we are checking only the tasks which are in open , planned, pending(ack), inprogress 
        "custom_fields": custom_fields_filters
    }
    try:
        response = requests.get(f'{CLICKUP_API_ENDPOINT}/list/{list_id}/task' ,headers=HEADERS, params=params)
        if response.status_code !=200:
            print(f'Failed to fetch tasks')
            return []
    except Exception as e:
        print(f'Error fetching task: {e}')
        return []
    tickets = response.json().get('tasks', [])
    for ticket in tickets:
        process_ticket(ticket, list_name)


def process_ticket(ticket, list_name):
    """
    This functions fetches the ticket data such as task name , task url , task id , status, priority 
    Then checks the status and priority of each ticket and if the ticket is not present in the notified_ticket set and if the ticket is eligible for review then calls the notify_ticket function.
    """
    current_time = datetime.datetime.now(TIMEZONE)
    task_id = ticket.get('id')
    task_name = ticket.get('name')
    task_url = ticket.get('url')
    status = ticket.get('status',{}).get('status','').lower().replace(" ", "")
    priority = ticket.get('priority',{}).get('priority','').lower() if ticket.get('priority') else 'none'
    if task_id not in notified_tickets and is_ticket_eligible_for_review(ticket,current_time) and \
    status in ['open', 'pending(ack)', 'inprogress','planned'] and priority in ['urgent', 'high']:
        notify_ticket(ticket, task_name, task_url, list_name, task_id)
        

def notify_ticket(ticket, task_name, task_url, list_name, task_id):
    """
    Evaluates whether a notification should be sent for a specific ticket based on user comments 
    This functions checks the comments on a ticket to determine if there has been a sufficient user interaction.
    if there is atleast one user commets it assumes that there is active user interactions and no notification has been sent for those tickets 
    if there is no user comments on a ticket and other criteria also fulfills (eg ticket creation time is more than 2 hours) then notification is sent for those tickets
    
    The function fetches comments using the ClickUp API. If the fetch is successful and there are no user comments,
    it calls `check_and_send_notification` to evaluate if the notification criteria are met based on ticket creation time.
    If the comments fetch fails or if an exception occurs, it logs the error.
    """
    current_time = datetime.datetime.now(TIMEZONE)
    try:
        comments_response = requests.get(f'{CLICKUP_API_ENDPOINT}/task/{task_id}/comment', headers=HEADERS)
        if comments_response.status_code == 200:
            comments = comments_response.json().get('comments', [])
            #print(json.dumps(comments, indent=2))
            user_comments = [comment for comment in comments if comment['user']['id'] != -1]
            if len(user_comments) >= 1:
                print(f'More than one user comments no action needed!: {task_url}')
                return
            if not user_comments:
                check_and_send_notification(ticket, task_name, task_url, list_name, task_id, current_time)
        else:
            print(f'Failed to fetch comments for Task ID: {task_id}, HTTP Status: {comments_response.status_code}')
    except requests.RequestException as e:
        print(f'Error fetching comments for Task ID: {task_id}: {e}')
                
 
def check_and_send_notification(ticket, task_name, task_url, list_name, task_id, current_time):
    """
    checks if the ticket should receive notification based on the ticket created timestamp
    this function calculates the age of the ticket created timestamp by comparing the current time with the ticket's creation time 
    if the ticket is created more than 2 hours ago and have not received the update since then , it sends notification to slack with details of the ticket 
    this ensuress that the ticket needs attention 

    The function first converts the ticket creation time from a Unix timestamp to a datetime object.
    If the ticket's age exceeds two hours, a message is formulated and sent via Slack. If the message
    is successfully sent, the ticket ID is added to a set of notified tickets and the URL to a list for
    end-of-day summaries. If the message fails to send, it logs an error. Any exceptions in processing
    are caught and logged, providing robustness against errors in date conversion or message sending.
    """
    try:
        ticket_created_timestamp = int(ticket['date_created']) // 1000 
        ticket_created_timestamp = datetime.datetime.fromtimestamp(ticket_created_timestamp,tz=TIMEZONE)
        if (current_time - ticket_created_timestamp).total_seconds() > 7200:
            ticket_created_timestamp_formatted = ticket_created_timestamp.strftime('%Y-%m-%d %H:%M')
            message = (f'From Customer: "{list_name}" Ticket headline: "{task_name}" has not recieved update since {ticket_created_timestamp_formatted}. Update with latest progress.')
            if send_message_slack(message, task_url):
                print(f'Message sent to slack : {message}')
                notified_tickets.add(task_id)
                end_of_day_tickets.append(task_url)
            else: 
                print(f'Failed to send notification')
        else:
            print(f'Ticket created time is not more than 2 hours')
    except Exception as e:
        print(f'Error while processing notification for Task ID: {task_id}: {e}')


def send_message_slack(message, task_url): 
    """
    Sends a formatted message to a Slack channel
    This function constructs a payload containing a message and a task URL, then sends this payload to Slack
    """
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


def check_for_new_date():
    """
    #Checks for the new date and clears the notified_tickets set and end_of_day_tickets list for new day
    #It also updates the last run date to the current date 
    """ 
    global last_run_date, notified_tickets, summary_sent_today
    try:
        current_date = datetime.datetime.now(TIMEZONE).date()
        if current_date > last_run_date:
            notified_tickets.clear()
            end_of_day_tickets.clear()
            summary_sent_today = False
            last_run_date = current_date
            print('New date detected.. Resetting the notified_tickets and summary_sent_today')
    except Exception as e:
        print(f'Error during date check: {e}')


def is_time_to_send_summary(current_time):
    """
    determins whether the current time falls within the time to send the daily summary 
    This function checks if the current time is within a 10-minute window starting at 18:00 each day. 
    """
    current_time = datetime.datetime.now(TIMEZONE)
    summary_start_time = current_time.replace(hour=18,minute=0,second=0, microsecond=0)   #summary time set at 8:30pm
    summary_end_time = summary_start_time + datetime.timedelta(minutes=10)                 #given 10 minutes buffer time to send summary
    return summary_start_time <= current_time <= summary_end_time 

def send_summary_slack():
    """
    Sends summary to slack at 18:00 each day only for those tickets which are added to end_of_day_tickets list 
    Only those tickets are added to end_of_day_tickets list which does not receive the user comments within 2 hours of ticket created 
    """
    global end_of_day_tickets, summary_sent_today
    if end_of_day_tickets:
        message = "End of Day Summary: Bug Tickets\n"
        message +="\n".join([f"-{task_url}" for task_url in end_of_day_tickets])
        if send_message_slack(message, None):
            print(f"Summary sent to slack")
            summary_sent_today = True
            end_of_day_tickets.clear()
        else:
            print('Summary not sent to slack')
    elif not end_of_day_tickets:
        print(f'No bug tickets for the day')

def get_list(folder_id):
    """
    #Retrieves a list of ClickUp lists associated with a specific folder ID.
    # This function makes an HTTP GET request to the ClickUp API endpoint to fetch lists within a given folder.
    # It uses the folder_id to request the specific folder's lists and checks the HTTP response status code
    # to determine whether the fetch was successful. If the response status is 200, it extracts and returns
    # the lists from the JSON response. If the request fails or another status code is returned, it handles
    # the failure by returning an empty list
    """
    response = requests.get(f'{CLICKUP_API_ENDPOINT}/folder/{folder_id}/list', headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('lists', [])
    return []

def get_tickets_from_customer_lists(folder_id):
    """
    Retrieves all tickets from lists within a specified ClickUp folder and initiates notifications based on task conditions.

    This function first calls get_list to fetch all lists within the given folder identified by folder_id.
    It then iterates through each list, retrieving the list's name and ID. For each list, it prints a message indicating
    that it is fetching tickets for that list and then calls get_tasks_and_notify to process each ticket in the list
    based on predefined conditions (such as ticket status and priority).
    """
    lists = get_list(folder_id)
    for list_item in lists:
        list_name, list_id = list_item.get('name'), list_item.get('id')
        print(f'Fetching tickets for list: {list_name}')
        get_tasks_and_notify(list_id,list_name)

def run():
    """
    # The main control loop of the application that continuously checks and processes tasks based on time and state.
    # - Checks if it is night time to pause operations.
    # - Regularly checks for new tickets that need notifications.
    # - Sends a daily summary of tasks at a specified time if it hasn't already been sent that day fir those ticket which have not received user comments within 2 hours of ticket creation.
    # - Manages and clears states at appropriate times (e.g., at midnight or when a new day is detected).

    # The loop first checks if it's night time using the is_night_time function. If it is, the loop breaks until
    # it's no longer night time.
    # It checks if the date has changed and resets relevant states if necessary.
    # Retrieves and processes tasks from specified ClickUp lists.
    # Calculates and sleeps for the duration required until the next necessary action (either the next task check or the daily summary).
    # At a specified summary time, if the summary hasn't been sent yet for the day, it sends the summary and clears the tickets list.
    # It resets the daily summary sent flag at midnight to prepare for the next day.
    """
    global summary_sent_today
    current_time = datetime.datetime.now(TIMEZONE)
    if is_night_time():
        print('Night time , No action needed')
        return
    
    check_for_new_date()
    print('checking for new tickets to notify') 
    get_tickets_from_customer_lists("109448264")   # folder id
    
    if is_time_to_send_summary(current_time) and not summary_sent_today:
        send_summary_slack()
        summary_sent_today = True
        end_of_day_tickets.clear()
    else:
        print('Failed to send summary')
    
if __name__ == '__main__':
    run()



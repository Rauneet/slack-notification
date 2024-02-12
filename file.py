import requests
import datetime
from pytz import timezone
import pprint
import calendar


CLICKUP_API_TOKEN = 'pk_67495744_YZUBMLUMJ4QQHOZK9XCOA8W9D8VEOD9S'
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'
CLICKUP_SPACE_ID = '90160582515'
CUSTOMER_TICKET_LIST_ID = '901601275948'
CLICKUP_API_ENDPOINT = 'https://api.clickup.com/api/v2'
HEADERS = {'Authorization': CLICKUP_API_TOKEN}


def is_night_time():
    tz = timezone('Asia/Kolkata')
    current_time = datetime.datetime.now(tz)
    # print(current_time.time())
    morning = datetime.time(hour = 9, minute = 0)
    # print(morning)
    night = datetime.time(hour = 21, minute = 0)
    if(current_time.time() >= morning and current_time.time() <= night):
        return False
    else:
        return True



def get_tasks_and_notify(list_id):
    if not is_night_time():
        print('Sending... Notification to slack')
        
        response = requests.get(f'{CLICKUP_API_ENDPOINT}/list/{list_id}/task', headers=HEADERS)
        if response.status_code == 200:
            tickets = response.json().get('tasks', [])
            for ticket in tickets:
                # priority = ticket['priority']['priority_type'] if ticket.get('priority_type') else ""
                # if priority.lower() not in ['high' , 'urgent']:
                #     print(f'Ticket is not urgent or high priority')
                #     continue
                # is_bug = False
                # for field in ticket.get('custom_fields' , []):
                #     if field['name'].strip().lower() == 'request type' and any(option['name'].strip().lower() == 'bug' for option in field['type_config']['option']):
                #         is_bug = True
                #         break
                #     if not is_bug:
                #         print(f'Ticket {task_id} is not marked as bug!!')
                #         continue
                

                # is_bug , high_urgent_priority = False, False
                # for field in ticket.get('custom_fields', []):
                #     if field['name'] == "Request_type" and field.get('value') == 'Bug':
                #         is_bug = True
                # if not (is_bug and high_urgent_priority):
                #     continue
                priority = ticket['priority']
                priority_type = priority['priority']
                if priority_type in ['High' , 'Urgent']:
                    print('Ticket is urgent or high priority' + priority_type)
                else:
                    print('Ticket is not ugent or high priority!!')
                task_id = ticket['id']
                # print(task_id)
               
            
                custom_fields = ticket['custom_fields']
                for field in custom_fields:
                    name = field['name']
                    if (name == "request type "):
                       options =  field['type_config']
                       for option in options['options']:
                           option_name =option['name']
                        #    print("got the option name " + option_name)
                           if (option_name == "bug "):
                               print("got the ticket where request type is bug")
    
                           
                comment = requests.get(f'{CLICKUP_API_ENDPOINT}/task/{task_id}/comment',headers=HEADERS)
                
                if comment.status_code == 200:
                    comment_res = comment.json().get('comments' ,[])
                    pprint.pprint(comment_res)
                    if len(comment_res)>0 :
                        date_time = comment_res[0]['date']
                        date_time = int(date_time[0:10])
                        
                        current_time = datetime.datetime.now()
                        epoch_time = int(calendar.timegm(current_time.timetuple()))
                        print(f"{date_time} {epoch_time}")
                        if (epoch_time - date_time) > 7200:
                            message = f'This ticket has not recieved any comment since 2 hour - https://app.clickup.com/t/{task_id} please update with the current progress.'
                            if send_message_slack(message) == 200:
                                print(f'Success!!!')
                                
                            else:
                                print(f"Failed to send notification for task ID {task_id}.")     
                    else:
                        print(f"no comments for task {task_id}")
            
def send_message_slack(message):
    payload = {
        'text' : message
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    if response.status_code == 200:
        return response.status_code

# def check_task_and_notify():
#     if not is_night_time():
#         tasks = get_tasks(CUSTOMER_TICKET_LIST_ID)
#         if tasks:
#             for task in tasks:
#                 message = f'Ticket Id {task[id]} has not been commented over 2 hours. Please add a comment.'
#                 send_message_slack(message)
#         else:
#             print('No task require notification')
#     else:
#         print('Its night time no notificatin sent.')


# pprint.pprint(get_tasks('901601275948'))
print(get_tasks_and_notify('901601275948'))
# Slack Notification System for ClickUp Tasks

## Introduction

This Python script integrates ClickUp with Slack notifications, designed to automate the monitoring of tasks within specified ClickUp lists. It targets tasks based on their priority, and type (request type - bugs), and notifies a configured Slack channel if certain conditions are met, such as lack of recent activity.

## Table of Contents

- [Installation](#installation)
- [Features](#features)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)
- [License](#license)

## Installation

Before running this script, ensure you have Python installed on your system. This script requires Python 3.x.

1. Clone the repository or download the script to your local machine.

## Features

1. Time based Filtering - Checks the time that it is within the working hour and not the off hour to reduce the unneccessary notification in the channel.
2. Task priority and type checking - Check the priority of the task whether it is urgent or high and also checks for the request type whether it bug or not.
3. Activity Monitoring: Checks the last activity on a task and notifies if there hasn't been any update within a specified time frame.
4. Slack Integration: Automatically sends messages to a specified Slack channel based on the task's status and the conditions.

## Dependencies 

requests: For making HTTP requests to the ClickUp and Slack APIs.
datetime, pytz: For handling time-based operations and timezone conversions.
pprint: For debugging purposes, to print data structures in a formatted way.
calendar: To convert dates into a UNIX timestamp.

## Configuration 

To configure the script for your environment, you will need to set several variables at the top of the script:

1. CLICKUP_API_TOKEN: Your ClickUp API token.
2. SLACK_WEBHOOK_URL: The Webhook URL for your Slack workspace.
3. CLICKUP_SPACE_ID: The ID of your ClickUp space.
4. CUSTOMER_TICKET_LIST_ID: The ID of the list in ClickUp containing customer tickets.

## Documentation 
For more information on the APIs used:

[Clickup API](https://clickup.com/api/)
[Slack API](https://api.slack.com/messaging/webhooks)




from flask import Flask
import threading 
from file_2 import get_tickets_from_customer_lists, is_night_time
app = Flask(__name__)
@app.route('/test-tasks')
def test_tasks():
    if not is_night_time():
        get_tickets_from_customer_lists('109448264')
        return "Tickets checked and send notification"
    else:
        return "Its night time no action needed"

thread = threading.Thread(target=get_tickets_from_customer_lists, args=("109448264",))
thread.start()
if __name__ == '__main__':
    app.run(debug=True , port=5000)
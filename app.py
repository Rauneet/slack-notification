from flask import Flask
import threading 
from file_2 import get_tickets_from_customer_lists, is_night_time
app = Flask(__name__)
@app.route('/test-tasks')
def test_tasks():
     if is_night_time():
        return "It's night time. No operations will be performed."
thread = threading.Thread(target=get_tickets_from_customer_lists, args=("109448264",))
thread.start()
if __name__ == '__main__':
    app.run(debug=True , port=5000)
from flask import *
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY']='secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def main():
	return render_template('template.html') 

def messageRecieved(methods=['GET', 'POST']):
	print('received!')

@socketio.on('my event')
def handle_event(json, methods=['GET', 'POST']):
	print('recieve event: '+str(json))
	if (str(json) != '{}'):
		socketio.emit('response', json, callback=messageRecieved)
	else:
		print('no messages')

if __name__ == '__main__':
	socketio.run(app, debug=True)

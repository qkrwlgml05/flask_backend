from flask import *
from flask_jwt_extended import *
import psycopg2 as pg2
import pandas as pd 
import torch
from LSTM import *
from datetime import timedelta

app = Flask(__name__)
app.config.update(DEBUG=True, JWT_SECRET_KEY="screte key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"]=timedelta(minutes=5)
app.config["JWT_REFRESH_TOKEN_EXPIRES"]=timedelta(hours=5)
jwt = JWTManager(app)

# conn = pg2.connect()
# cur = conn.cursor()

def return_result (subject_id):
	data = pd.read_csv('../data/data.csv')
	
	data = data[data['subject_id']==subject_id]
	
	if len(data) == 0:
		return '\n\t"sepsis": "no patients"\n}'
	drop_cols = ['urine', 'subject_id', 'hadm_id', 'stay_id', 'hr', 'endtime', 'icd_event', 'dobutamine', 'dopamine', 'epinephrine', 'norepinephrine', 'vasopressin', 'fio2', 'pao2fio2ratio_vent', 'is_infection']
	data = data.sort_values(by='starttime')[-24:-5].set_index('starttime').drop(drop_cols, axis=1).loc[:].values
	data = data.reshape((1,)+data.shape)
	device = 'cuda:2' if torch.cuda.is_available() else 'cpu'
	
	model = torch.load('../data/model.pt', map_location=device)
	model.device = device
	y_pred = model(torch.tensor(data).transpose(0, 1).float())
	y_pred = 1/(1 + np.exp(-y_pred.cpu().detach().numpy()[0][0]))
	return '\n\t"sepsis":'+str(y_pred)+'\n'

app.route('/')
def start():
	return 'Hello'

@app.route('/login', methods=['POST', 'PUT'])
def login():
	input = request.get_json()
	conn = pg2.connect()
	cur = conn.cursor()
	
	user_id = input['id']
	user_pwd = input['pwd']
	
	exestr = "SELECT * FROM public.login WHERE id='{0}' and pwd='{1}'".format(user_id, user_pwd)
	cur.execute(exestr)
	rows = cur.fetchall()
	conn.commit()
	conn.close()
	
	if len(rows) != 1:
		return jsonify(result="invalid")
	else:
		access_token = create_access_token(identity=user_id, fresh=True)
		print(decode_token(access_token))
		refresh_token = create_refresh_token(identity=user_id)
		print(decode_token(refresh_token))
		return jsonify(result="success", access_token=access_token, refresh_token=refresh_token)

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
	user_id = get_jwt_identity()
	access_token = create_access_token(identity=user_id, fresh=False)
	return jsonify(access_token=access_token)

@app.route('/user', methods=['GET'])
@jwt_required(fresh=True)
def user():
	return "Hello World!"

@app.route('/model', methods=['POST', 'PUT'])
@jwt_required()
def model():
	input = request.get_json()
	pat_id = input['pat_id']
	conn = pg2.connect()
	cur = conn.cursor()
	exestr = "SELECT * FROM core.patients WHERE subject_id='{0}'".format(pat_id)
	cur.execute(exestr)
	row = cur.fetchall()
	conn.commit()
	conn.close()
	
	if len(row) == 0:
		return jsonify(result="not match to patients id")
	dict_row = {"result":"success", "subject_id":row[0][0], "gender":row[0][1], "anchor_age":row[0][2], "anchor_year_group":row[0][3], "dod":row[0][4]}
	sepsis = return_result(pat_id)
	def generate():
		yield '{'
		for i in dict_row.keys():
			yield '\n\t"'+i+'":"'+str(dict_row[i])+'", '
		yield return_result(pat_id)
		yield '}'
	return Response(stream_with_context(generate()), mimetype='text/json')

if __name__ == '__main__':
	app.run(debug=True)

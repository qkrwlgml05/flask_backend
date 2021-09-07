from flask import *
from flask_jwt_extended import *
import psycopg2 as pg2
import pandas as pd 
import torch
from LSTM import *
import sys

sys.path.append('~/.local/lib/python3.6/site-packages')
app = Flask(__name__)
app.config.update(DEBUG=True, JWT_SECRET_KEY="screte key")
jwt = JWTManager(app)

# conn = pg2.connect(host="mdhidaea.iptime.org", port=21212, dbname="aiadmin", user="internship", password="internship")
# cur = conn.cursor()

def return_result (subject_id):
	data = pd.read_csv('../data/data.csv')
	
	data = data[data['subject_id']==subject_id]
	if len(data) == 0:
		return -1
	drop_cols = ['subject_id', 'hadm_id', 'stay_id', 'hr', 'endtime', 'icd_event', 'dobutamine', 'dopamine', 'epinephrine', 'norepinephrine', 'vasopressin', 'fio2', 'pao2fio2ratio_vent', 'is_infection']
	data = data.sort_values(by='starttime')[-24:-5].set_index('starttime').drop(drop_cols, axis=1).loc[:].values
	data = data.reshape((1,)+data.shape)
	device = 'cuda:2' if torch.cuda.is_available() else 'cpu'
	
	model = torch.load('../data/model.pt')
	y_pred = model(torch.tensor(data).transpose(0, 1).float().to(device))
	y_pred = 1/(1 + np.exp(-y_pred.cpu().detach().numpy()[0][0]))
	return y_pred

app.route('/')
def start():
	return 'Hello'

@app.route('/login', methods=['POST', 'PUT'])
def login():
	input = request.get_json()
	conn = pg2.connect(host="mdhidaea.iptime.org", port=21212, dbname="aiadmin", user="internship", password="internship")
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
		return jsonify(result="success", access_token=create_access_token(identity=user_id, expires_delta = False))

@app.route('/user', methods=['GET'])
@jwt_required()
def user():
	cur_user = get_jwt_identity()
	if cur_user is None:
		return "not user"
	else: return "Hello World!"

@app.route('/model', methods=['POST', 'PUT'])
@jwt_required()
def model():
	cur_user = get_jwt_identity()
	if cur_user is None:
		return "not user"
	
	input = request.get_json()
	pat_id = input['pat_id']
	conn = pg2.connect(host="mdhidaea.iptime.org", port=21212, dbname="aiadmin", user="internship", password="internship")
	cur = conn.cursor()
	exestr = "SELECT * FROM core.patients WHERE subject_id='{0}'".format(pat_id)
	cur.execute(exestr)
	row = cur.fetchall()
	conn.commit()
	conn.close()
	
	if len(row) == 0:
		return jsonify(result="not match to patients id")
	sepsis = return_result(pat_id)
	return jsonify({"result":"success", "subject_id":row[0][0], "gender":row[0][1], "anchor_age":row[0][2], "anchor_year_group":row[0][3], "dod":row[0][4], 'sepsis':sepsis})

if __name__ == '__main__':
	app.run(debug=True)

from flask import Flask, render_template, redirect, request, json, jsonify, url_for
from werkzeug import secure_filename
import csv
import pypyodbc
import redis
import time
import _pickle as cPickle
import hashlib
import datetime

app = Flask(__name__)


server = 'nishant22.database.windows.net'
database = 'sqldatabase'
username = 'admin_nishant'
password = 'N!shant22'
driver='{ODBC Driver 13 for SQL Server};Server=tcp:nishant22.database.windows.net,1433;Database=sqldatabase;Uid=admin_nishant@nishant22;Pwd=N!shant22;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
cnxn = pypyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()

# Redis Object
R_SERVER  = redis.StrictRedis(host='nishant.redis.cache.windows.net', port=6380, db=0, password='TPtibow4e1+IlO7H/Blcc5pDUaoFeyo+ymttTKMQ+Sk=', ssl=True)
TTL = 36

@app.route('/')
def home():
	return render_template('index.html', script_root = request.script_root)


@app.route('/searchMagnitude', methods=['POST','GET'])
def searchMagnitude():
	if request.method == 'POST':
		data = request.form
		cursor.execute("SELECT * FROM earthquake WHERE mag > " + data['searchWord']+ ";") 
		row = cursor.fetchone()
		result = []
		while row:
			row1 = [str(i) for i in row]
			result.append(row1)
			row = cursor.fetchone()
		return jsonify(result)


@app.route('/searchMagnitudeRange', methods=['POST','GET'])
def searchMagnitudeRange():
	if request.method == 'POST':
		data = request.form
		sql = "SELECT * FROM earthquake WHERE mag between " + data['range1'] + " and " + data['range2'] + " and CONVERT(datetime,LEFT(time,10),126) BETWEEN '"+ data['startDate'] +"' AND '"+ data['endDate'] +"'";

		cursor.execute(sql)
		row = cursor.fetchone()
		result = []
		while row:
			row1 = [str(i) for i in row]
			result.append(row1)
			row = cursor.fetchone()
		return jsonify(result)

@app.route('/searchMagnitudeIntervals', methods=['POST','GET'])
def searchMagnitudeIntervals():
	if request.method == 'POST':
		data = request.form
		pointer1 = int(data['range1'])
		endPoint = int(data['range2'])
		rows = []
		start_time = time.time()
		now = datetime.datetime.now()
		while pointer1 < endPoint :
			pointer2 = pointer1 + 0.1
			sql = "SELECT TOP "+data['count']+" * FROM earthquake WHERE mag between " + str(pointer1+0.001)  + " and " + str(pointer2) +";"
			# Create a hash key
			hash = hashlib.sha224(sql.encode('utf-8')).hexdigest()
			key = "sql_cache:" + hash
			if (R_SERVER.get(key)):
				print("This was return from redis")
				result =  cPickle.loads(R_SERVER.get(key))
			else:
				print(sql)
				cursor.execute(sql)
				row = cursor.fetchone()
				result = []
				while row:
					row1 = [str(i) for i in row]
					result.append(row1)
					row = cursor.fetchone()
				# Put data into cache for 1 hour
				if result:
					save = list(result)
				else:
					save = 0
				R_SERVER.set(key, cPickle.dumps(save))
				# R_SERVER.expire(key, TTL);

			rows.append([[pointer1, pointer2],result])

			pointer1 = pointer2
		total_time = time.time() - start_time
		# print(rows)
		return jsonify(["first select time: " + str(now)]+["total_time: " + str(total_time)] + rows)


@app.route('/searchLocation', methods=['POST','GET'])
def searchLocation():
	if request.method == 'POST':
		data = request.form
		sql = "SELECT * FROM(SELECT *,(((acos(sin((" + data['latitude'] + "*(22/7)/180)) * sin((latitude*(22/7)/180))+cos((" + data['latitude'] + "*(22/7)/180)) * cos((latitude*(22/7)/180)) * cos(((" + data['longitude'] + " - longitude)*(22/7)/180))))*180/(22/7))*60*1.1515*1.609344) as distance FROM earthquake) t WHERE distance <= "+  data['distance']
		print(sql)
		cursor.execute(sql)
		row = cursor.fetchone()
		result = []
		while row:
			row1 = [str(i) for i in row]
			result.append(row1)
			row = cursor.fetchone()
		return jsonify(result)

@app.route('/searchLocationDistance', methods=['POST','GET'])
def searchLocationDistance():
	if request.method == 'POST':
		data = request.form
		res = []
		start_time = time.time()
		for i in range(1,101,5):
			sql = "SELECT * FROM(SELECT *,(((acos(sin((" + data['latitude'] + "*(22/7)/180)) * sin((latitude*(22/7)/180))+cos((" + data['latitude'] + "*(22/7)/180)) * cos((latitude*(22/7)/180)) * cos(((" + data['longitude'] + " - longitude)*(22/7)/180))))*180/(22/7))*60*1.1515*1.609344) as distance FROM earthquake) t WHERE distance <= "+  str(i)
			print(sql)
			hash = hashlib.sha224(sql.encode('utf-8')).hexdigest()
			key = "sql_cache:" + hash
			if (R_SERVER.get(key)):
				print("This was return from redis")
				result =  cPickle.loads(R_SERVER.get(key))
			else:
				cursor.execute(sql)
				row = cursor.fetchone()
				result = []
				while row:
					row1 = [str(i) for i in row]
					result.append(row1)
					row = cursor.fetchone()
				# Put data into cache for 1 hour
				R_SERVER.set(key, cPickle.dumps(list(result)))
				# R_SERVER.expire(key, TTL);
			res.append({'range': str(i) + " km", 'results': result})
		total_time = time.time() - start_time
	return jsonify(["total_time: " + str(total_time)] + res)
		

@app.route('/searchLocationName', methods=['POST','GET'])
def searchLocationName():
	if request.method == 'POST':
		data = request.form
		sql = "SELECT * FROM earthquake WHERE locationSource = '" + data['name'] + "' and mag between " + data['range1'] + " and " + data['range2'] + ";"
		print(sql)
		cursor.execute(sql)
		row = cursor.fetchone()
		result = []
		while row:
			row1 = [str(i) for i in row]
			result.append(row1)
			row = cursor.fetchone()
		return jsonify(result)
		

@app.route('/searchLocationRange', methods=['POST','GET'])
def searchLocationRange():
	if request.method == 'POST':
		data = request.form
		sql = "SELECT * FROM earthquake WHERE latitude between " + data['latitude1'] + " and " + data['latitude2'] + " and longitude between " + data['longitude1'] + " and " + data['longitude2'] + ";"
		cursor.execute(sql)
		row = cursor.fetchone()
		result = []
		while row:
			row1 = [str(i) for i in row]
			result.append(row1)
			row = cursor.fetchone()
		return jsonify(result)


if __name__ == '__main__':
	app.run()

from flask import Flask, render_template, redirect, request, json, jsonify, url_for
import pypyodbc
from sklearn.cluster import KMeans
import numpy as np

app = Flask(__name__)

server = 'nishant22.database.windows.net'
database = 'sqldatabase'
username = 'admin_nishant'
password = 'N!shant22'
driver='{ODBC Driver 13 for SQL Server};Server=tcp:nishant22.database.windows.net,1433;Database=sqldatabase;Uid=admin_nishant@nishant22;Pwd=N!shant22;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
cnxn = pypyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()

@app.route('/')
def home():
	return render_template('index.html', script_root = request.script_root)

@app.route('/visualizeData', methods=['POST','GET'])
def visualizeData():
	if request.method == 'POST':
		data = request.form
		k = int(data['kclusters'])
		cursor.execute("SELECT " + data['xaxis']+ "," + data['yaxis']+ " FROM titanic3 WHERE " + data['xaxis']+ " IS NOT NULL and " + data['yaxis']+ " IS NOT NULL;") 
		row = cursor.fetchone()
		result = []
		X = []
		while row:
			row = list(row)
			X.append(row)
			row = cursor.fetchone()

		kmeans = KMeans(n_clusters=k).fit(X)
		centroids = kmeans.cluster_centers_

		print(centroids)
		kmeans_transform = kmeans._transform(X).tolist()
		point_distance = []
		clusters = [[] for i in range(k)]
		for i in range(len(X)):
			c_index = kmeans_transform[i].index(min(kmeans_transform[i]))
			clusters[c_index].append(X[i])
			temp = {"point":X[i], "distance_from_centroid":kmeans_transform[i]}
			point_distance.append(temp)

		return jsonify({"centroids":centroids.tolist(),"pointDistances":point_distance, "clusters": clusters})

if __name__ == '__main__':
	app.run()

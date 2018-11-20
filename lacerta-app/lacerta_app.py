#!/usr/bin/python3.6

from flask import Flask, jsonify, render_template, request, redirect, make_response, url_for
from flask_s3 import FlaskS3
import logging
import sys, os, json, traceback
sys.path.insert(0, "{}/crawler".format(os.getcwd()))
import search
from parse import validate_url_format


app = Flask(__name__)
app.config['FLASKS3_BUCKET_NAME'] = 'lacerta-app'
s3 = FlaskS3(app)


@app.route("/", methods=['GET'])
def render():
	history = request.cookies.get('history')
	if not history:
		history = ""
	container1_data = history.split(", ")

	if container1_data[0] == "":
		container1_data = None

	return render_template('layout.html', container1_data=container1_data)


@app.route("/query", methods=['GET', 'POST'])
def query():
	if request.method == 'GET':
		return redirect(url_for('render'))
	else:
		logging.info(request.form)
		start = request.form["start_url"]
		depth = request.form["depth"]
		keyword = request.form["keyword"]
		search_type = request.form["search_type"]

		if not validate_url_format(start):
			return bad_request('Error: Invalid Start URL: {}'.format(start))
		if not start or not depth:
			return bad_request('Error: Start URL and seach depth required!')
		if search_type not in ['BFS', 'DFS']:
			return bad_request('Error: search type {} is an invalid search type'.format(search_type))
		if not int(depth) or int(depth) < 0:
			return bad_request('Error: Invalid depth. Please specify a positive integer')
		try:
			result = search.search(start, depth, keyword, search_type)
			result_json = search.loadGraph(result)
			result_json_d3 = search.transformGraph(result_json)

			history = request.cookies.get('history')
			if history:
				history = history + ", " + result_json['start_url']
			else:
				history = result_json['start_url']

			response = make_response(jsonify(result_json_d3), 200)
			response.set_cookie('history', history)
			return response
		except ValueError as error:
			tb = traceback.format_exc()
			logging.error(tb)
			return bad_request(str(error))
		except Exception as e:
			tb = traceback.format_exc()
			logging.error(tb)
			return server_error(str(e))


#TODO: add additional errorhandlers
@app.errorhandler(400)
def bad_request(error_message):
	message = {
		'status' : 400,
		'message' : str(error_message)
	}
	response = jsonify(message)
	response.status_code = 400
	return response

@app.errorhandler(500)
def server_error(error_message):
	message = {
		'status' : 500,
		'message' : str(error_message)
	}
	response = jsonify(message)
	response.status_code = 500
	return response

if __name__ == '__main__':
	app.run()

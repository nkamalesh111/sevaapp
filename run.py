from flaskblog import app,socketio

if __name__ == '__main__':
    socketio.run(app,host='10.110.30.104',debug=True)

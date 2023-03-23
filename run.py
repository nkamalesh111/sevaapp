from sevaapp import app, socketio

if __name__ == "__main__":
    socketio.run(app, host="10.110.30.109", port=5001, debug=True)

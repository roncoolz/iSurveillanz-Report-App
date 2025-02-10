from flask import Flask, request
import socket

app = Flask(__name__)

@app.route('/')
def get_hostname():
    # Get the client's IP address from request
    client_ip = request.remote_addr  # This is equivalent to Request.ServerVariables["REMOTE_ADDR"]
    
    try:
        # Resolve the IP address to a hostname
        hostname = socket.gethostbyaddr(client_ip)[0]  # This corresponds to GetHostEntry and HostName in C#
    except socket.herror:
        hostname = None  # In case the hostname cannot be resolved
    
    return f"Client IP: {client_ip}, Hostname: {hostname}"

if __name__ == '__main__':
    app.run(debug=True)
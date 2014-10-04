import os
import json
from flask import Flask, request, redirect, make_response, render_template
from flask_bootstrap import Bootstrap
from auth import SalesforceOAuth2

def create_app():
  app = Flask(__name__)
  Bootstrap(app)

  return app

app = create_app()

def get_callback_url(request):
    """ Ensure that if running on Heroku, https is used """
    if request.base_url.find('herokuapp.com') == -1:
        base_url = request.base_url
    else:
        base_url = request.base_url.replace('http:', 'https:')
    return base_url + 'callback'

@app.route('/')
def home():
    return render_template('index.html', callback_url = get_callback_url(request))

@app.route('/refresh_token')
def refresh_token():
    # Get arguments from HTTP GET request
    client_id = request.args.get('client_id')
    if not client_id:
        return 'ERROR: You must pass a client_id'
    client_secret = request.args.get('client_secret')
    if not client_secret:
        return 'ERROR: You must pass a client_secret'
    callback_url = get_callback_url(request)
    sandbox = request.args.get('sandbox', False) == 'true'
    scope = 'web full refresh_token'
    
    sf = SalesforceOAuth2(client_id, client_secret, callback_url, sandbox=sandbox)
    redirect_url = sf.authorize_url(scope=scope)

    response = make_response(redirect(redirect_url))
    response.set_cookie('client_id', client_id)
    response.set_cookie('client_secret', client_secret)
    if sandbox:
        response.set_cookie('sandbox', 'true')
    return response

@app.route('/callback')
def callback():
    client_id = request.cookies.get('client_id')
    client_secret = request.cookies.get('client_secret')
    callback_url = get_callback_url(request)
    sandbox = request.cookies.get('sandbox') == 'true'
    scope = 'web full refresh_token'

    code = request.args.get('code')

    sf = SalesforceOAuth2(client_id, client_secret, callback_url, sandbox=sandbox)
    token = sf.get_token(code)

    template_context = {
        'client_id': client_id,
        'client_secret': client_secret,
        'access_token': token['access_token'],
        'refresh_token': token['refresh_token'],
        'instance_url': token['instance_url'],
    }

    response = make_response(render_template('callback.html', **template_context))
    response.set_cookie('client_id', '', expires=0)
    response.set_cookie('client_secret', '', expires=0)
    response.set_cookie('sandbox', '', expires=0)
    return response

if __name__ == '__main__':
    app.run()

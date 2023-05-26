import pyrebase
from flask import Flask, render_template, request, redirect, session, url_for
import os
import pandas as pd
import numpy as np
import random
import openai
from datetime import datetime

app = Flask(__name__)

APIKEY = os.environ['APIKEY']
APIKEY2 = os.environ['APIKEY2']

config = {
  'apiKey': APIKEY,
  'authDomain': "hetspel-63066.firebaseapp.com",
  'projectId': "hetspel-63066",
  'databaseURL':"https://hetspel-63066-default-rtdb.europe-west1.firebasedatabase.app/",
  'storageBucket': "hetspel-63066.appspot.com",
  'messagingSenderId': "478411402160",
  'appId': "1:478411402160:web:0e46daddb7728c74034475",
  'measurementId': "G-H1266G5CBF"
}



app.secret_key="hello"



firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

db=firebase.database()
storage=firebase.storage()

df=pd.read_excel("opdrachten.xlsx")
df_teams=pd.read_excel("df_teams.xlsx")



with open('matroos.txt', 'r') as file:
    # Read the contents of the file into a string
    matroos_basis = file.read()

with open('muiter.txt', 'r') as file:
    # Read the contents of the file into a string
    muiter_basis = file.read()

with open('kapitein.txt', 'r') as file:
    # Read the contents of the file into a string
    kapitein_basis = file.read()
with open('speech1.txt', 'r') as file:
    # Read the contents of the file into a string
    speech_basis = file.read()
with open('speech2.txt', 'r') as file:
    # Read the contents of the file into a string
    speech_basis2 = file.read()

# Get the current date
now = datetime.now()

# Format the date as yyyymmdd
date_str = now.strftime("%Y%m%d")

def gpt3(history):
    openai.api_key=APIKEY2
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=history
    )
    #content = response.content.value()
    return response#["content"]

def MakeHistory(df):
    result = []
    for index, row in df.iterrows():
        result.append({'content': row['content'], 'role': row['role']})
    return result

def MakePandasDF(data, user_input):
    df=pd.DataFrame(data, columns=['content', 'role'])
    data2=[{'content': user_input, 'role': 'user'}]
    df2=pd.DataFrame(data2, columns=['content', 'role'])
    df=pd.concat([df,df2])
    return df

def HistToString(lst):
    result = ""
    for item in lst:
        result += f'<br> <p> {item["role"]}: {item["content"]} </p> <br>\n'
    return result

def HistToString2(lst, muiter):
    if lst is None:
        return ""
    result = ""
    for item in lst:
        if item["role"] == 'user':
            result += f'{muiter}: {item["content"]}.'
        else:
            result += f'assistant: {item["content"]}.'
    return result

    return result

history=[{"content": "" ,"role": "system"}]        

#db.child("visitors").set(likes_data)  

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    if (request.method == 'POST'):
            email = request.form['name']
            password = request.form['password']
            try:
                user=auth.sign_in_with_email_and_password(email, password)
                name=db.child(user['localId']).child("Handle").get().val()
                session["user"]= user
                session["name"]= name
                if db.child(date_str).get().val() is None:
                    df_teams['roles'] = df_teams['roles'].sample(frac=1).reset_index(drop=True)
                    df_teams['assignment'] = df_teams['roles'].apply(lambda x: df['content'][random.randint(0, df.shape[0]-1)] if x == 'Matroos' else 'Je hebt geen taak!')
                    df_dict=df_teams.to_dict()
                    db.child(date_str).child('roles').set(df_dict)
                else:
                    pass
                list_names=db.child(date_str).child('roles').child('names').get().val()
                list_roles=db.child(date_str).child('roles').child('roles').get().val()
                list_assignment=db.child(date_str).child('roles').child('assignment').get().val()
                name_index=list_names.index(session["name"])
                role=list_roles[name_index]
                #muiters = [list_names[key] for key in list_roles if list_roles[key] == "Muiter"]
                muiters = [list_names[i] for i in range(len(list_roles)) if list_roles[i] == "Muiter"]
                session["muiter1"]=muiters[0]
                session["muiter2"]=muiters[1]
                session["muiter3"]=muiters[2]
                session["muiter4"]=muiters[3]
                session["muiter5"]=muiters[4]
                session["role"]=role
                task=list_assignment[name_index]
                session["task"]=task
                if db.child(date_str).child(session["name"]).child("History").get().val() is None:
                    if session["role"]== 'Matroos':
                        session["history"]= [{"content": matroos_basis+"This is the task of the person you are helping: "+session["task"]+". This is the person you are helping: "+session["name"] ,"role": "system"}]
                        db.child(date_str).child(session["name"]).child("History").set(session["history"])  
                    elif session["role"]== 'Muiter':
                        session["history"]= [{"content": muiter_basis ,"role": "system"}]
                        db.child(date_str).child(session["name"]).child("History").set(session["history"])
                    elif session["role"]== 'Kapitein':
                        session["history"]= [{"content": kapitein_basis ,"role": "system"}]
                        db.child(date_str).child(session["name"]).child("History").set(session["history"])
                    else:
                        pass
                else:
                    pass
                return redirect(url_for("home"))
            except:
                unsuccessful = 'Please check your credentials'
                return render_template('index.html', umessage=unsuccessful)
    return render_template('index.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if (request.method == 'POST'):
            email = request.form['name']
            password = request.form['password']
            handle = request.form['username']
            auth.create_user_with_email_and_password(email, password)
            user=auth.sign_in_with_email_and_password(email, password)
            db.child(user['localId']).child("Handle").set(handle)
            db.child(user['localId']).child("ID").set(user['localId'])          
            return render_template('index.html', smessage=1)
    return render_template('create_account.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if (request.method == 'POST'):
            email = request.form['name']
            auth.send_password_reset_email(email)
            return render_template('index.html')
    return render_template('forgot_password.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if (request.method == 'POST'):
        return redirect(url_for("chat"))
    else:
        return render_template('home.html')

@app.route('/speech', methods=['GET', 'POST'])
def speech():
    if (request.method == 'POST'):
        return redirect(url_for("chat"))
    else:
        history_kapitein=db.child(date_str).child(session["name"]).child("History").get().val()
        try:
            history_muiter1=db.child(date_str).child(session["muiter1"]).child("History").get().val()
            history_muiter1=history_muiter1[1:]
        except:
            pass
            
        try:
            history_muiter2=db.child(date_str).child(session["muiter2"]).child("History").get().val()
            history_muiter2=history_muiter2[1:]
        except:
            pass
            

        try:
            history_muiter3=db.child(date_str).child(session["muiter3"]).child("History").get().val()
            history_muiter3=history_muiter3[1:]
        except:
            pass
            

        try:
            history_muiter4=db.child(date_str).child(session["muiter4"]).child("History").get().val()
            history_muiter4=history_muiter4[1:]
        except:
            pass
            

        try:
            history_muiter5=db.child(date_str).child(session["muiter5"]).child("History").get().val()
            history_muiter5=history_muiter5[1:]
        except:
            pass
            

        
        history_speech=[{"content": speech_basis+HistToString2(lst=history_muiter1,muiter=session["muiter1"])+HistToString2(lst=history_muiter2,muiter=session["muiter2"])+HistToString2(lst=history_muiter3,muiter=session["muiter3"])+HistToString2(lst=history_muiter4,muiter=session["muiter4"])+HistToString2(lst=history_muiter5,muiter=session["muiter5"])+speech_basis2+HistToString2(lst=history_kapitein,muiter=session["name"]),"role": "system"},{'content':'Kan je de speech voor het diner schrijven? antwoord alleen met de tekst van de speech','role':'user'}]
        speech_gpt=gpt3(history_speech)
        speech_gpt= list([dict(speech_gpt["choices"][0]["message"])])
        speech=HistToString(speech_gpt)
        return render_template('speech.html', speech=speech, name=session["name"])

@app.route('/chat', methods=['GET', 'POST'])
def chat(): 
    if session["role"]=='Matroos':
        if (request.method == 'POST' and "action9" in request.form):
            return redirect(url_for("home"))
        elif (request.method == 'POST' and "action10" in request.form):
            question = request.form['action10'] 
            session.pop("prompt", None)  
            session["prompt"]=question
            session["history"]=db.child(date_str).child(session["name"]).child("History").get().val()
            df=MakePandasDF(data=session["history"], user_input=session["prompt"])
            session.pop("history", None)
            session["history"]=MakeHistory(df)
            session["test"]=gpt3(session["history"])
            session["test"]= list([dict(session["test"]["choices"][0]["message"])])
            session["history"]=session["history"]+session["test"]
            session["chat"]=session["history"][1:]
            session["chat"]=HistToString(session["chat"][-5:])
            db.child(date_str).child(session["name"]).child("History").set(session["history"])
            return render_template('conversation.html', answer=session["test"], chat=session["chat"], role=session["role"], task=session["task"])
        else:    
            return render_template('conversation.html', chat="", role=session["role"], task=session["task"])
    elif session["role"]=='Kapitein':
        if (request.method == 'POST' and "action9" in request.form):
            return redirect(url_for("home"))
        elif (request.method == 'POST' and "action10" in request.form):
            list_names=db.child(date_str).child('roles').child('names').get().val()
            list_roles=db.child(date_str).child('roles').child('roles').get().val()
            list_assignment=db.child(date_str).child('roles').child('assignment').get().val()
            html = '<table>\n'
            # headers
            html += '<tr><th>Naam</th><th>Rol</th><th>Taak</th></tr>\n'

            # rows
            for name, age, assignment in zip(list_names, list_roles, list_assignment):
                html += '<tr><td>{}</td><td>{}</td><td>{}</td></tr>\n'.format(name, age, assignment)

            html += '</table>' 
            question = request.form['action10'] 
            session.pop("prompt", None)  
            session["prompt"]=question
            session["history"]=db.child(date_str).child(session["name"]).child("History").get().val()
            df=MakePandasDF(data=session["history"], user_input=session["prompt"])
            session.pop("history", None)
            session["history"]=MakeHistory(df)
            session["test"]=gpt3(session["history"])
            session["test"]= list([dict(session["test"]["choices"][0]["message"])])
            session["history"]=session["history"]+session["test"]
            session["chat"]=session["history"][1:]
            session["chat"]=HistToString(session["chat"][-5:])
            db.child(date_str).child(session["name"]).child("History").set(session["history"])
            return render_template('conversation_kapitein.html', answer=session["test"], chat=session["chat"], role=session["role"], task=session["task"],group=html)
        elif (request.method == 'POST' and "action11" in request.form):
            return redirect(url_for("speech"))
        else:
            list_names=db.child(date_str).child('roles').child('names').get().val()
            list_roles=db.child(date_str).child('roles').child('roles').get().val()
            list_assignment=db.child(date_str).child('roles').child('assignment').get().val() 
            html = '<table>\n'
            # headers
            html += '<tr><th>Naam</th><th>Rol</th><th>Taak</th></tr>\n'

            # rows
            for name, age, assignment in zip(list_names, list_roles, list_assignment):
                html += '<tr><td>{}</td><td>{}</td><td>{}</td></tr>\n'.format(name, age, assignment)

            html += '</table>'    
            return render_template('conversation_kapitein.html', chat="", role=session["role"], task=session["task"],group=html)
    elif session["role"]=='Muiter':
        if (request.method == 'POST' and "action9" in request.form):
            return redirect(url_for("home"))
        elif (request.method == 'POST' and "action10" in request.form):
            question = request.form['action10'] 
            session.pop("prompt", None)  
            session["prompt"]=question
            session["history"]=db.child(date_str).child(session["name"]).child("History").get().val()
            df=MakePandasDF(data=session["history"], user_input=session["prompt"])
            session.pop("history", None)
            session["history"]=MakeHistory(df)
            session["test"]=gpt3(session["history"])
            session["test"]= list([dict(session["test"]["choices"][0]["message"])])
            session["history"]=session["history"]+session["test"]
            session["chat"]=session["history"][1:]
            session["chat"]=HistToString(session["chat"][-5:])
            db.child(date_str).child(session["name"]).child("History").set(session["history"])
            return render_template('conversation_kapitein.html', answer=session["test"], chat=session["chat"], role=session["role"], task=session["task"],group=html)
        else:    
            return render_template('conversation_kapitein.html', chat="", role=session["role"], task=session["task"],group=html)
    
    else:
        return render_template('conversation.html', chat="", role=session["role"], task=session["task"])
        




if __name__ == '__main__':
    app.run(debug=True)

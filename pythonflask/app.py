from datetime import datetime
import bcrypt
from flask import json
from flask import Flask, request,session, abort,render_template
from flask.json import jsonify
from flask_session import Session
from flask_bcrypt import Bcrypt
from config import ApplicationConfig
from models import db,User,Datos
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from elasticsearch import Elasticsearch
import csv
import random
import string
import smtplib,ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config.from_object(ApplicationConfig)
UPLOAD_FOLDER = 'static/imgs'
UPLOAD_FOLDER2 = 'static/data'

ALLOWED_EXTENSIONS = {'csv'}
#es= Elasticsearch()

smtp_address = 'smtp.gmail.com'
smtp_port = 465

email_address = 'enerhomeTFG@gmail.com'
email_password = '#enerhomeTFG1'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2

bcrypt=Bcrypt(app)
cors = CORS(app, supports_credentials=True)
server_session = Session(app)
db.init_app(app)

with app.app_context():
    db.create_all()

class Usuario:
  def __init__(self, name, email,datos):
    self.name = name
    self.email = email
    self.datos = datos
  def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class energyData:
 def __init__(self, energia, acPower,voltage,powerFactor,apPower,current,fechas,name ):
    self.energia=energia
    self.acPower=acPower
    self.voltage=voltage
    self.powerFactor=powerFactor
    self.apPower=apPower
    self.current=current
    self.fechas=fechas
    self.name=name
   # self.reactivePower=reactivePower
 def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

@app.route("/@me", methods=['GET'])
def get_curret_user():
    global allDates

    user_id = session.get("user_id")
    if user_id != None:
        user = User.query.filter_by(id=user_id).first()
    # new_csv()
        if user==None:
            return jsonify({"error" : "Unauthorized"}) ,401
        
        user = User.query.filter_by(id=user_id).first()
        datas=[]
        datos = Datos.query.filter_by(owner_id=user.id).all()
        for data in datos:
            datas.append(data.name)
        es= Elasticsearch(['localhost:9200'])
        body={"size":100}

        resp=es.indices.get('*').keys()
        sorted_list=sorted(resp)
        test_str='.'
        indices = []
        fechas=[]
        energia=[]
        activePower=[]
        voltage=[]
        powerFactor=[]
        apparentPower=[]
        current=[]
        for sub in sorted_list:
            flag = 0
            for ele in sub:
                if ele in test_str:
                    flag = 1
            if not flag:
                indices.append(sub)  

        for index in indices:
    
            resp=es.search(index=index,body=body)   
            data2 = [doc2 for doc2 in resp['hits']['hits']]
        # print(data2)
            cont=0
        # print(index)
            for doc2 in data2:
                #print(doc2)
                if doc2['_source'] != {}:
                    horaaux=doc2['_source']["Hora"]
                    fechaaux2=doc2['_source']["Fecha"]
                    fechaaux=fechaaux2+":"+ str(horaaux)
                #print(energia)

                if fechaaux not in fechas:
                    if len(fechas)>0:
                        date1 = datetime.strptime(fechaaux, "%d/%m/%Y:%H")
                        date2 = datetime.strptime(fechas[cont], "%d/%m/%Y:%H")
                    # print(date1<date2)
                        if date1 < date2:
                            fechas.insert(cont,fechaaux)
                            energia.insert(cont,doc2['_source']["Energia"])
                            activePower.insert(cont,doc2['_source']["P_Activa"])
                            voltage.insert(cont,doc2['_source']["Tension"])
                            powerFactor.insert(cont,doc2['_source']["F_Potencia"])
                            apparentPower.insert(cont,doc2['_source']["P_Aparente"])
                            current.insert(cont,doc2['_source']["Intensidad"])
                            cont=cont+1
                        else:
                            fechas.append(fechaaux)
                            energia.append(doc2['_source']["Energia"])
                            activePower.append(doc2['_source']["P_Activa"])
                            voltage.append(doc2['_source']["Tension"])
                            powerFactor.append(doc2['_source']["F_Potencia"])
                            apparentPower.append(doc2['_source']["P_Aparente"])
                            current.append(doc2['_source']["Intensidad"])
                    else:
                        fechas.append(fechaaux)
                        energia.append(doc2['_source']["Energia"])
                        activePower.append(doc2['_source']["P_Activa"])
                        voltage.append(doc2['_source']["Tension"])
                        powerFactor.append(doc2['_source']["F_Potencia"])
                        apparentPower.append(doc2['_source']["P_Aparente"])
                        current.append(doc2['_source']["Intensidad"])
                else:
                    i=0
                #  print(len(fechas))
                    while i< len(fechas):
                        #print(i)
                        if fechas[i] == fechaaux:
                            #print(fechaaux)
                            if doc2['_source'] != {}:
                                energia[i]=(energia[i]+(doc2['_source']["Energia"]))/2
                                activePower[i]=(activePower[i]+doc2['_source']["P_Activa"])/2
                                voltage[i]=(voltage[i]+doc2['_source']["Tension"])/2
                                powerFactor[i]=(powerFactor[i]+doc2['_source']["F_Potencia"])/2
                                apparentPower[i]=(apparentPower[i]+doc2['_source']["P_Aparente"])/2
                                current[i]=(current[i]+doc2['_source']["Intensidad"])/2
                                
                                break
                        i+=1    
            #  reactivePower.append(doc['_source']["P_Aparente(VA)"])

        fechas.sort(key=lambda date: datetime.strptime(date, "%d/%m/%Y:%H"))
        allDates=fechas
        indices2=[]
        for fichero in datas :
            aux=fichero.split(".", 1)
            indices2.append(aux[0].lower())

        return jsonify({
            "id": user.id,
            "email": user.email,
            "nombre" : user.nombre,
            "avatar": user.avatar,
            "data": datas,
            "rol" : user.rol , 
            "indices": indices2,
            "mediaCurrent":current,
            "mediaEnergia":energia,
            "mediaActivePower":activePower,
            "mediaVoltage":voltage,
            "mediaPowerFactor":powerFactor,
            "mediaApparentPower":apparentPower,
            "mediaCurrent":current,
            "labels": fechas
        })
    return jsonify({}), 200
@app.route("/getData", methods=['GET'])
def get_data():
    startDate = request.args['startDate']
    finishDate =request.args['finishDate']
    files=request.args.getlist('deviceList[]')
    user_id = session.get("user_id")
    user = User.query.filter_by(id=user_id).first()
    es= Elasticsearch(['localhost:9200'])
    lista = []
    fechas=[]
    #print(allDates)

    for index in files:
        #
        body={"size":100,"query": {"bool":{"must":[{"range": {"Fecha": {"gte": startDate,"lte": finishDate}}}]}}}
        resp=es.search(index=index,body=body,scroll='5s')  
        newSize=len(allDates)
        energia=[0] * newSize
        activePower=[0] * newSize
        voltage=[0] * newSize
        powerFactor=[0] * newSize
        apparentPower=[0]* newSize
        current=[0] * newSize
        fechas=[0]*newSize
        cont=0
        parsedDates=False
        isDateGreater=False
       # print(resp['hits']['hits'])
        data = [doc for doc in resp['hits']['hits']]    
        for doc in data:
            #print(doc)
            #fechaaux2=fechaaux.split(".", 1)
            #if fechaaux2[0] in fechas:
            if doc['_source'] != {}:
                horaaux=doc['_source']["Hora"]
                fechaaux2=doc['_source']["Fecha"]
                fecha=fechaaux2+":"+ str(horaaux)
            i=0
            if parsedDates==False:
                date1 = datetime.strptime(fecha, "%d/%m/%Y:%H")
                date2 = datetime.strptime(allDates[i], "%d/%m/%Y:%H")
                isDateGreater=date1 > date2
            while isDateGreater==True:
              #  print(i)
                energia[i]=0
                activePower[i]=0
                voltage[i]=0
                powerFactor[i]=0
                apparentPower[i]=0
                current[i]=0
                i=i+1
                date1 = datetime.strptime(fecha, "%d/%m/%Y:%H")
                date2 = datetime.strptime(allDates[i], "%d/%m/%Y:%H")
                isDateGreater=date1 > date2
                cont=i
            parsedDates=True
            if doc['_source'] != {}:
                energia[cont]=((float(doc['_source']["Energia"])))
                activePower[cont]=((float(doc['_source']["P_Activa"])))
                voltage[cont]=((float(doc['_source']["Tension"])))
                powerFactor[cont]=((float(doc['_source']["F_Potencia"])))
                apparentPower[cont]=((float(doc['_source']["P_Aparente"])))
                current[cont]=((float(doc['_source']["Intensidad"])))
                fechas[cont]=doc['_source']["Fecha"]
            cont+=1
      #  print(energia)
        datosEnergia= energyData(energia,activePower,voltage,powerFactor,apparentPower,current,fechas,index)
        datosEnergia = datosEnergia.toJSON()
        jsonEnergia = json.loads(datosEnergia)
        lista.append(jsonEnergia)
    if(user!= None):
        return jsonify({
           "data": lista,
         })
    else:
        return jsonify({
           "data": "No hay datos"
        })

def new_csv():
    es= Elasticsearch(['localhost:9200'])
    resp=es.indices.get('*').keys()
    sorted_list=sorted(resp)
    test_str='.'
    indices = []

    for sub in sorted_list:
        flag = 0
        for ele in sub:
            if ele in test_str:
                flag = 1
        if not flag:
            indices.append(sub) 
    lista = []
    size=10
    body={"size":size}

    for index in indices:
        newRows=[]
        newRows.append(['Fecha','Tension','Intensidad','F.Potencia','P.Activa','P.Aparente','Energia'])
        auxenergia=0
        auxactivePower=0
        auxvoltage=0
        auxCurrent=0
        auxPowerFactor=0
        auxapparentPower=0
        resp=es.search(index=index,body=body,scroll='20s')   
        old_scroll_id = resp['_scroll_id']     
        fechahora=""
        contmedia=0

        while len(resp['hits']['hits']):
            resp = es.scroll(
                scroll_id = old_scroll_id,
                scroll = '20s', # length of time to keep search context
            )
            old_scroll_id = resp['_scroll_id']
            data = [doc for doc in resp['hits']['hits']]    
            cont=0
            fechaaux=""
            for doc in data:
                
                if cont==0:
                    fechaaux=doc['_source']["Fecha"]
                    hora=doc['_source']["Hora"]
                    fechaaux2=hora.split(":", 1)
                    fechaaux =fechaaux+":"+fechaaux2[0]
                    #print(fechaaux)
                    
                auxenergia+=((float(doc['_source']["Energ�a(kWh)"].replace(',','.'))))
                auxactivePower+=((float(doc['_source']["P_Activa(W)"].replace(',','.'))))
                auxvoltage+=((float(doc['_source']["Tensi�n(V)"].replace(',','.'))))
                auxPowerFactor+=((float(doc['_source']["F_Potencia"].replace(',','.'))))
                auxapparentPower+=((float(doc['_source']["P_Aparente(VA)"].replace(',','.'))))
                auxCurrent+=((float(doc['_source']["Intensidad(A)"].replace(',','.'))))
                contmedia+=1
                cont+=1
            if fechahora!= fechaaux:    	 
                fechahora=fechaaux 
                if contmedia==0:
                    contmedia=1        
                row=[fechaaux,str(round(auxCurrent/contmedia, 2)),str(round(auxvoltage/contmedia, 2)),str(round(auxPowerFactor/contmedia, 2)),str(round(auxactivePower/contmedia, 2)),str(round(auxapparentPower/contmedia, 2)),str(round(auxenergia/contmedia,5))]
                newRows.append(row)
                auxenergia=0
                auxactivePower=0
                auxvoltage=0
                auxCurrent=0
                auxPowerFactor=0
                auxapparentPower=0
                contmedia=0
           # print(row)
        myFile = open('static/data/'+index+'1h.csv', 'w', encoding='UTF8',newline='')
        with myFile as csvfile:
            writer = csv.writer(myFile)
            writer.writerows(newRows)
        #print("Writing complete on :" + index)

   
@app.route("/DataList", methods=['POST'])
def get_User_data():
    email = request.json["useremail"]
    user_exists = User.query.filter_by(email=email).first()
    datas=[]
    if(user_exists!= None):
       
        datos = Datos.query.filter_by(owner_id=user_exists.id).all()
        for data in datos:
            datas.append(data.name)
        return ({
        "data": datas
         })
    else:
        return({
        "data": datas
        })
    
@app.route("/listUsers", methods=['GET'])
def get_user_list():
    user_id = session.get("user_id")
    user = User.query.filter_by(id=user_id).first()
    if user==None:
        return jsonify({"error" : "Unauthorized"}) ,401
    if user.rol!="ADMIN":
        return jsonify({"error" : "Unauthorized"}) ,401

    list =[]
    users = User.query.filter_by().all()
    for user in users:
        datas=[]
        datos = Datos.query.filter_by(owner_id=user.id).all()
        for data in datos:
            datas.append(data.name)
        list.append(Usuario(user.nombre,user.email,datas))
    usuarios = []
    for user in list:
        user = user.toJSON()
        userData = json.loads(user)
        usuarios.append(userData)
    return ({
        "usuarios": usuarios
    })

@app.route("/register", methods=['GET','POST'])
def register_user():

    email = request.json["email"]
    nombre=""           
    user_exists = User.query.filter_by(email=email).first() is not None
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(8))
    if user_exists:
        abort(409)
    hashed_password= bcrypt.generate_password_hash(password)

    if email== "admin@gmail.com":
        new_user= User(email=email,password=hashed_password,nombre=email,rol="ADMIN")  
    else:
        new_user= User(email=email,password=hashed_password,nombre=email)  
    new_datos = Datos()
    new_datos.owner = new_user.id  
    db.session.add(new_datos) 
    db.session.add(new_user)

    db.session.commit() 
    send_email(email,password)

    if(new_user.nombre=="nombre por defecto" or new_user.nombre==None):
        nombre= "user1"
    else:
        nombre=new_user.nombre
    return jsonify({
        "id": new_user.id,
        "email": new_user.email,
        "nombre": nombre,
        "avatar": new_user.avatar,
        "rol": new_user.rol
    })

def send_email(email,password):
    #Crear Mensaje
    message = MIMEMultipart("alternative")
    message["Subject"] = "Registro EnerHome"
    message["From"] = email_address
    message["To"] = email

    text = '''
    Bienvenido a EnerHome 
    Se ha registrado con el email: ''' + email +'''
    Con la siguiente contraseña: ''' + password+'''
    Acceda a la plataforma para cambiar la contraseña
    '''

    html = '''
    <html>
    <body>
    <h1>Bienvenido a EnerHome </h1>
    <p>Se ha registrado con el email: ''' + email+'''</p>
    <p>Con la siguiente contraseña: ''' + password+'''</p>
    <p>Acceda a la plataforma para cambiar la contraseña</p>

    <br>
    <a href="http://localhost:3000">EnerHome</a>
    </body>
    </html>
    '''
    texte_mime = MIMEText(text, 'plain')
    html_mime = MIMEText(html, 'html')
    message.attach(texte_mime)
    message.attach(html_mime)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_address, smtp_port, context=context) as server:
  # conectarse
        server.login(email_address, email_password)

        server.sendmail(email_address, email, message.as_string())

@app.route("/delete", methods=['GET','POST'])
def delete_user():
    user_id= session["user_id"]
    User.query.filter_by(id=user_id).delete()
    db.session.commit()  
    session.clear()
    return "Se ha eliminado el usuario correctamente"

@app.route("/deleteUser", methods=['GET','POST'])
def delete_user2(): 
    email= request.json["email"]   
    user_exists = User.query.filter_by(email=email).first() is not None
    if user_exists== True:
        User.query.filter_by(email=email).delete()
        db.session.commit()  
        return "Se ha eliminado el usuario correctamente"
    return "El usuario no existe"

@app.route("/deleteData", methods=['GET','POST'])
def delete_data():
    filename = request.json["filename"]
    user_id= session["user_id"]
    Datos.query.filter_by(owner_id=user_id,name=filename).delete()
    db.session.commit()  
    return "Se ha eliminado el fichero correctamente"

@app.route("/deleteDataUser", methods=['GET','POST'])
def delete_data2():
    filename = request.json["filename"]
    email= request.json["email"]
    user = User.query.filter_by(email=email).first()
    Datos.query.filter_by(owner_id=user.id,name=filename).delete()
    db.session.commit()  
    return "Se ha eliminado el fichero correctamente"

@app.route("/perfil", methods=['GET','POST'])
def update_user():
    email = request.json["email"]
    nombre = request.json["nombre"]
    cambio=0
    aux =session["user_email"]
    user = User.query.filter_by(email=aux).first()
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if (user.nombre == "nombre por defecto" or user.nombre!= nombre and nombre!=""):
        user.nombre=nombre
        cambio=cambio+1
    
    if (user.email!= nombre and email!=""):
        user_exists = User.query.filter_by(email=email).first() is not None
        if user_exists:
            abort(409)
        user.email=email
        session["user_email"]=email
        cambio=cambio+1
    if cambio==0:
        return "No ha habido ningún cambio"
    else:
        db.session.commit()
        return jsonify({
            "nombre": user.nombre,
            "email": user.email,
            "avatar": user.avatar,
        })

@app.route("/password", methods=['GET','POST'])
def update_password():
    user = User.query.filter_by(email=session["user_email"]).first()
    password = request.json["password"]

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "La contraseña a la que se intenta cambiar es la misma"}), 400

    if (password!=""):
        hashed_password= bcrypt.generate_password_hash(password)
        user.password=hashed_password
        db.session.commit()
        return jsonify({
            "nombre": user.nombre,
            "email": user.email,
            "avatar": user.avatar
        })


@app.route("/login", methods=['GET','POST'])
def login_user():
    email = request.json["email"]
    password = request.json["password"]
    nombre=""
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401
    
    else:
        nombre=user.nombre
    
    session["user_id"] = user.id
    session["user_email"] = user.email
    return jsonify({
        "id": user.id,
        "email": user.email,
        "nombre": nombre,
        "avatar": user.avatar
    })
@app.route("/@logout", methods=['GET','POST'])
def logut():
    session.clear()
    return jsonify({}), 200

@app.route("/uploadfile", methods=['GET','POST'])    
def upload_file():

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error" : "Unauthorized"}) ,401
    
    user = User.query.filter_by(id=user_id).first()
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No se ha seleccionado un fichero"}), 404
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.avatar=filename
            db.session.commit()
            return jsonify({
                "file": filename
            })

@app.route("/uploadData", methods=['GET','POST'])    
def upload_data():

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error" : "Unauthorized"}) ,401
    
    user = User.query.filter_by(id=user_id).first()
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No se ha seleccionado un fichero"}), 404
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
           
            datos = Datos.query.filter_by(owner_id=user.id,name=filename).all()
            for data in datos:
                if(data.name==filename):
                    return jsonify({
                     "error" : "Fallo, el archivo está repetido"
                    }),409
            data = Datos(name=filename,owner_id=user.id)
            db.session.add(data)
            db.session.commit()

            datos = Datos.query.filter_by(owner_id=user.id).all()
            datas=[]
            for data in datos:
                datas.append(data.name)
            file.save(os.path.join(app.config['UPLOAD_FOLDER2'], filename))
            return jsonify({
            "id": user.id,
            "email": user.email,
            "nombre": user.nombre,
             "data" : datas
            })
    return jsonify({
        "error" : "Fallo al subir el archivo"
    }),500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
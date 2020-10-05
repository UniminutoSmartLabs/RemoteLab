import socketio
import threading
import time
import RPi.GPIO as GPIO

import subprocess
import os

i=0
t=None
h=None
video=None
block=0
pidc=None
pidd=None
block=0 #esta variable_ permite habilitar o deshabilitar reconexion

sio = socketio.Client(reconnection=True,reconnection_delay=5)
GPIO.setmode(GPIO.BCM)



@sio.event
def connect():
    print('connection established')
    sio.emit('S2code', {'ncode': '0'})

@sio.event
def S2code(data):
    global i,h
    global pidc
    global pidd
    global block
    if block==1: #si hay bloque por reconexion...
        block=0
    print('message received with ', data)
    code=data['response']
    print(code)
    if code!='1':
        file=open('/home/pi/Desktop/script.py','w+')
        file.write(code)
        file.close()
        os.chmod("/home/pi/Desktop/script.py",0o777)
        i=i+1
        if i==1:
            h=subprocess.Popen(['python','/home/pi/Desktop/script.py'])
            pidc=h.pid
            print ('pidc',pidc)
            file=open('/home/pi/Desktop/pid.txt','w+')
            file.write(str(pidc))
            file.close()
        else:
            h.kill()
            h=subprocess.Popen(['python','/home/pi/Desktop/script.py'])
            pidd=h.pid
            file=open('/home/pi/Desktop/pid.txt','w+')
            file.write(str(pidd))
            file.close()
            print('pidd',pidd)
    sio.sleep(5)        
    sio.emit('S2ncode', {'ncode': '0'})

@sio.event
def S2sesion(data):
    global video,block
    comando='raspivid -t 0 -w 780 -h 580 -fps 25 -g 75 -t 0 -b 800000 -awb greyworld -rot -90 -o - | ffmpeg -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -i pipe:0 -c:v copy -c:a aac -strict experimental -loglevel quiet -f flv -f flv rtmp://204.93.196.64:1935/s2/stream'
    print('message received with ', data)
    sesion=data['Sesion']
    print(type(sesion))
    if sesion==1 and block==0:
        block=1
        #video=subprocess.Popen("raspivid",comando
        video=os.system(comando) #Ejecutar comando
    else:
        if sesion==0:
            block=0
            print("Sesion0")
            file=open('/home/pi/Desktop/pid.txt','r')
            pid=file.read()
            file.close()
            os.system("killall -9 ffmpeg")#Detener servicio ffmpeg
            os.system("kill -9 "+pid)
            for i in range (2,26):
                GPIO.setup(i,GPIO.OUT)
                GPIO.output(i,0)
            GPIO.cleanup()

            
@sio.event
def disconnect():
    print('disconnected from server')
    sio.emit('S2ncode', {'ncode': '0'})
    #reconect()
    
def EnvioDatos():
    sio.emit('S2ncode', {'ncode': '0'})
    #threading.Timer(1.0, EnvioDatos).start()
    
try:
    sio.connect('http://204.93.196.64:8083')#conectar con servidor
except:
    while True: #Este bucle se ejecuta de manera indefinida hasta que la conexion es reestablecida
        try:
            sio.sleep(10)
            sio.connect('http://204.93.196.64:8083')#conectar con servidor
            break
        except:
            print("await")
            continue 

file=open('/home/pi/Desktop/pidcomser.txt','w+')
file.write(str(os.getpid()))
file.close()
t=threading.Timer(2.0, EnvioDatos)#Es mejor usar un timer para trabajar por hilos o procesos
t.start()

#sio.wait()


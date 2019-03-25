import machine, ssd1306, time, esp32, os
from machine import TouchPad, Pin
from microMLP import MicroMLP
from umqtt.simple import MQTTClient

i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5))
oled = ssd1306.SSD1306_I2C(128, 64, i2c, 0x3c)

tstop = TouchPad(Pin(0))
treset = TouchPad(Pin(14))
tstop.config(500)               # configure the threshold at which the pin is considered touched
treset.config(500)             

servo1 = machine.PWM(machine.Pin(13), freq=50)
servo2 = machine.PWM(machine.Pin(15), freq=50)
servos_running = False

c = MQTTClient("umqtt_client", "192.168.178.37", 1883)


def initServos():
  servo1.duty(83)  # right servo from OLED board
  servo2.duty(71)  # left servo

def stopServos():
  printLine("stop",27)
  initServos()

def startServos():
  printLine("start",27)
  global servos_running 
  servos_running = True
  motorLoop()

def printLine(msg,y):
  oled.fill_rect(0,y,128,8,0)
  oled.text(msg, 0, y)
  oled.show()

def clearScreen():
  oled.fill(0)
  oled.show()

def suspend():
  esp32.wake_on_touch(True)
  machine.deepsleep()

def startWifi():
  import network
  import config
  sta_if = network.WLAN(network.STA_IF)
  if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect(config.WIFI_SSID, config.WIFI_PASS)
    while not sta_if.isconnected():
      pass
    clearScreen()
    oled.text("ssid:"+str(config.WIFI_SSID), 0, 0)
    oled.text("link:"+str(sta_if.isconnected()), 0, 9)
    oled.text(str(sta_if.ifconfig()[0]), 0, 18)
    oled.show()
  print('network config:', sta_if.ifconfig())

def reboot():
  printLine("rebooting..",27)
  time.sleep(.5)
  machine.reset()

def needsReboot():
  files=os.listdir()
  if 'reboot' in files:
    os.remove('reboot')
    reboot()

def motorLoop():

  max = 115  # not change
  min = 40   # not change
  cut = 5
  step = 5
  phase_right = 2
  ms = 0.001
  x1 = 0

  for x in range (min+cut,max-cut,step):
    if x1 < (max-cut):
      x1 = x1 + (x * phase_right)
    else:
      x1 = max - cut
    servo1.duty(x1)
    servo2.duty(max-(x-min))
    time.sleep(ms)
    printLine("s1:"+str(x)+" s2:"+str(max-(x-min)),36)
  
  for x in range (min+cut,max-cut,step):
    servo2.duty(x)
    servo1.duty(max-(x-min))
    time.sleep(ms)
    printLine("s1:"+str(x)+" s2:"+str(max-(x-min)),36)

def mqttSubscriptionCallback(topic, msg):
    print("mqtt: "+str((msg)))
    global servos_running
    if msg == (b"start"):
      servos_running = True
    if msg == (b"stop"):
      servos_running = False
    if msg == (b"reboot"):
      reboot()

def startMQTTChannel():
    c.set_callback(mqttSubscriptionCallback)
    c.connect()
    c.subscribe(b"robot_msgs")

def watchDog():
  global servos_running
  while True:
    c.check_msg()
    if tstop.read()<300:
      servos_running=not servos_running
      time.sleep(.1)

    if treset.read()<460:
      printLine("suspend..",27)
      time.sleep(.5)
      clearScreen() 
      suspend()

    if servos_running:
      startServos() 
    else:
      stopServos() 
      time.sleep(1)

    needsReboot()  # if send empty file for reboot

def xorProblem():
  mlp = MicroMLP.Create( neuronsByLayers           = [2, 2, 1],
                       activationFuncName        = MicroMLP.ACTFUNC_SIGMOID,
                       layersAutoConnectFunction = MicroMLP.LayersFullConnect )

  nnFalse  = MicroMLP.NNValue.FromBool(False)
  nnTrue   = MicroMLP.NNValue.FromBool(True)

  mlp.AddExample( [nnFalse, nnFalse], [nnFalse] )
  mlp.AddExample( [nnFalse, nnTrue ], [nnTrue ] )
  mlp.AddExample( [nnTrue , nnTrue ], [nnFalse] )
  mlp.AddExample( [nnTrue , nnFalse], [nnTrue ] )

  learnCount = mlp.LearnExamples()

  print( "LEARNED :" )
  print( "  - False xor False = %s" % mlp.Predict([nnFalse, nnFalse])[0].AsBool )
  print( "  - False xor True  = %s" % mlp.Predict([nnFalse, nnTrue] )[0].AsBool )
  print( "  - True  xor True  = %s" % mlp.Predict([nnTrue , nnTrue] )[0].AsBool )
  print( "  - True  xor False = %s" % mlp.Predict([nnTrue , nnFalse])[0].AsBool )

  if mlp.SaveToFile("mlp.json") :
    print( "MicroMLP structure saved!" )
  
def main():
  clearScreen()
  printLine("Starting..",0)
  initServos()
  startWifi()
  startMQTTChannel()
  watchDog()

main()
      
 

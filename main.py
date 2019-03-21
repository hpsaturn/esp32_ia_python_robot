import machine, ssd1306, time, esp32
from machine import TouchPad, Pin

i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5))
servo1 = machine.PWM(machine.Pin(13), freq=50)
servo2 = machine.PWM(machine.Pin(15), freq=50)
servo1.duty(77)
servo2.duty(77)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, 0x3c)

tstop = TouchPad(Pin(0))
tstop.config(500)               # configure the threshold at which the pin is considered touched
treset = TouchPad(Pin(14))
treset.config(500)               # configure the threshold at which the pin is considered touched
pressKey = False

def do_connect():
  import network
  import config
  sta_if = network.WLAN(network.STA_IF)
  if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect(config.WIFI_SSID, config.WIFI_PASS)
    while not sta_if.isconnected():
      pass
    oled.fill(0)
    oled.text("ssid:"+str(config.WIFI_SSID), 0, 0)
    oled.text("link:"+str(sta_if.isconnected()), 0, 9)
    oled.text(str(sta_if.ifconfig()[0]), 0, 18)
    oled.show()
  print('network config:', sta_if.ifconfig())


def printLine(msg,y):
  oled.fill_rect(0,y,128,8,0)
  oled.text(msg, 0, y)
  oled.show()

def motorLoop():

  max = 115  # not change
  min = 40   # not change
  cut = 0
  step = 5
  ms = 0.001

  for x in range (min+cut,max-cut,step):
    servo1.duty(x)
    servo2.duty(max-(x-min))
    time.sleep(ms)
    printLine("s1:"+str(x)+" s2:"+str(max-(x-min)),36)
  
  for x in range (min,max,step):
    servo2.duty(x)
    servo1.duty(max-(x-min))
    time.sleep(ms)
    printLine("s1:"+str(x)+" s2:"+str(max-(x-min)),36)
 

do_connect()

while True:
  if tstop.read()<300:
    pressKey=not pressKey
    time.sleep(.5)

  if treset.read()<500:
    printLine("suspend..",27)
    time.sleep(1)
    oled.fill(0)
    oled.show()
    esp32.wake_on_touch(True)
    machine.lightsleep()

  if pressKey:
    printLine("start",27)
    motorLoop()
  else:
    printLine("stop",27)
    time.sleep(.1)
    
    
  

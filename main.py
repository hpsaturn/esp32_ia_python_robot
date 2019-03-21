import machine, ssd1306

i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5))
oled = ssd1306.SSD1306_I2C(128, 64, i2c, 0x3c)

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
    oled.text("wifi: "+str(sta_if.isconnected()), 0, 0)
    oled.show()
  print('network config:', sta_if.ifconfig())

do_connect()




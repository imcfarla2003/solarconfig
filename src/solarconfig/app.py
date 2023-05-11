"""
SolarConfig
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, RIGHT, LEFT, MONOSPACE, RTL
from toga import validators
from typing import List, Optional, Union
from socket import socket, AF_INET, SOCK_DGRAM, IPPROTO_UDP, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, timeout
from pysolarmanv5 import PySolarmanV5,V5FrameError
from datetime import datetime
from time import sleep
import asyncio
import sys
import ipaddress

class HelloWorld(toga.App):

    datetimeplaceholder='0000-00-00 00:00'

    def startup(self):
        """
        Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        self.ip_address = None
        
        main_box = toga.Box(style=Pack(direction=COLUMN))
        
        ip_label_label = toga.Label(
            'IP Address',
            style = Pack(padding=5)
        )
        self.ip = toga.TextInput(
            placeholder='000.000.000.000',
            style = Pack(padding=5,flex=1),
            validators = [self.ipaddress()]
        )
        ip_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        ip_box.add(ip_label_label)
        ip_box.add(self.ip)
        
        serial_label_label = toga.Label(
            'Serial Number',
            style = Pack(padding=5)
        )
        self.serial_label = toga.TextInput(
            placeholder='0000000000',
            style = Pack(padding=5,flex=1),
            validators = [validators.Integer()]
        )
        serial_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        serial_box.add(serial_label_label)
        serial_box.add(self.serial_label)

        getInverterbutton = toga.Button(
            "Find Inverter",
            on_press=self.get_device,
            style=Pack(padding=5)
        )
        self.setInverterbutton = toga.Button(
            "Set Inverter",
            on_press=self.set_device,
            style=Pack(padding=5)
        )
        deviceinfo_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        deviceinfo_box.add(getInverterbutton)
        deviceinfo_box.add(self.setInverterbutton)

        device_box = toga.Box(style=Pack(direction=COLUMN, alignment=LEFT))
        device_box.add(ip_box)
        device_box.add(serial_box)
        device_box.add(deviceinfo_box)

        time_label_label = toga.Label(
            'Time on Device',
            style = Pack(padding=5)
        )
        self.time_label = toga.Label(
            self.datetimeplaceholder,
            style = Pack(padding_left=5, flex=1)
        )
        time_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        time_box.add(time_label_label)
        time_box.add(self.time_label)
        
        syncbutton = toga.Button(
            "Date/Time Synchronise",
            on_press=self.set_datetime,
            style=Pack(padding=5)
        )        
        sync_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER))
        sync_box.add(syncbutton)

        devicetime_box = toga.Box(style=Pack(direction=COLUMN, alignment=LEFT))
        devicetime_box.add(time_box)
        devicetime_box.add(sync_box)
        
        self.chktimed = toga.Switch(
            text = 'Timed (dis)charging',
            style = Pack(padding=5),
            value = False
        )
        timed_box = toga.Box(style=Pack(direction=COLUMN, text_direction=RTL))
        timed_box.add(self.chktimed)
        
        charging_label = toga.Label(
            'Charging From/To',
            style = Pack(padding=5, flex=1)
        )
        self.chargestart = toga.TimePicker(
            style = Pack(padding=5)
        )
        self.chargestop = toga.TimePicker(
            style = Pack(padding=5)
        )
        charging_box  = toga.Box(style=Pack(direction=COLUMN))
        charging_box.add(charging_label)
        charging_box.add(self.chargestart)
        charging_box.add(self.chargestop)
        
        discharging_label = toga.Label(
            'Discharging From/To',
            style = Pack(padding=5, flex=1)
        )
        self.dischargestart = toga.TimePicker(
            style = Pack(padding=5)
        )
        self.dischargestop = toga.TimePicker(
            style = Pack(padding=5)
        )
        discharging_box  = toga.Box(style=Pack(direction=COLUMN))
        discharging_box.add(discharging_label)
        discharging_box.add(self.dischargestart)
        discharging_box.add(self.dischargestop)

        current_label_label = toga.Label(
            'Charging Current (max 70A default 50A)',
            style = Pack(padding=5)
        )
        self.current_label = toga.TextInput(
            placeholder='0',
            style = Pack(padding=5,flex=1),
            validators = [validators.Integer()]
        )
        current_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        current_box.add(current_label_label)
        current_box.add(self.current_label)
        
        dcurrent_label_label = toga.Label(
            'Discharging Current (max 70A default 50A)',
            style = Pack(padding=5)
        )
        self.dcurrent_label = toga.TextInput(
            placeholder='0',
            style = Pack(padding=5,flex=1),
            validators = [validators.Integer()]
        )
        dcurrent_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        dcurrent_box.add(dcurrent_label_label)
        dcurrent_box.add(self.dcurrent_label)
        
        updatebutton = toga.Button(
            "Update Inverter",
            on_press=self.set_timing,
            style=Pack(padding=5)
        )
        updatefrombutton = toga.Button(
            "Load From Inverter",
            on_press=self.get_details,
            style=Pack(padding=5)
        )
        psync_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER))
        psync_box.add(updatebutton)
        psync_box.add(updatefrombutton)
        
        parameters_box = toga.Box(style=Pack(direction=COLUMN))
        parameters_box.add(timed_box)
        parameters_box.add(charging_box)
        parameters_box.add(current_box)
        parameters_box.add(discharging_box)
        parameters_box.add(dcurrent_box)
        parameters_box.add(psync_box)
        
        main_box.add(device_box)
        main_box.add(devicetime_box)
        main_box.add(parameters_box)

        self.add_background_task(self.get_device)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    async def get_device(self, widget, **kwargs):
        self.ip_address = None
        self.ip.value = ''
        self.serial = None
        self.serial_label.value = ''
        self.time_label.text = self.datetimeplaceholder
        
        # Scan for the device
        sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        sock.settimeout(1.0)

        request = "WIFIKIT-214028-READ"
        address = ("<broadcast>", 48899)

        sock.sendto(request.encode(), address)
        while True:
            try:
                data = sock.recv(1024)
            except timeout:
                break
            keys = dict.fromkeys(['ipaddress', 'mac', 'serial'])
            values = data.decode().split(",")
            result = dict(zip(keys, values))
            self.ip_address = result['ipaddress']
            self.ip.value = self.ip_address
            self.ip.readonly = True
            self.serial = int(result['serial'])
            self.serial_label.value = result['serial']
            self.serial_label.readonly = True
            self.setInverterbutton.enabled = False
            self.ip.readonly = True
            print(f'Got Device {self.ip_address} {self.serial}')
            break
        sock.close()
        self.add_background_task(self.get_datetime)
        self.get_details(None)

    async def get_datetime(self, widget, **kwargs):
        "A background task"
        # This task runs in the background, without blocking the main event loop
        # get the current time on the invertor every 5 minutes but update the screen every minute
        count = 0
        # the number of minutes before the time is sync'd again
        maxcount = 5
        year = 0
        month = 0
        day = 0
        hour = 0
        minute = 0
        sleepseconds = 10
        while True:
            datetimestring = self.datetimeplaceholder
            if self.ip_address != None and self.serial != None:
                sleepseconds = 60
                if count <= 0:
                    print("Getting time")
                    datelist = None
                    try:
                        modbus = PySolarmanV5(self.ip_address, self.serial, socket_timeout=10)
                    except:
                        print("IP Address wrong")
                        self.ip_address = None
                        self.ip.value = ''
                        return
                    try:
                        datelist = modbus.read_input_registers(register_addr=33022, quantity=6)
                        count = maxcount
                    except V5FrameError:
                        print("Getting time - Retry")
                        # Try again after a short pause
                        modbus.sock.close()
                        del modbus
                        await asyncio.sleep(30)
                        modbus = PySolarmanV5(self.ip_address, self.serial)
                        try:
                            # Reconnect
                            datelist = modbus.read_input_registers(register_addr=33022, quantity=6)
                            count = maxcount
                        except V5FrameError:
                            print("Getting time - Failed")
                    modbus.sock.close()
                    del modbus
                    if datelist != None:
                        print(datelist)
                        year = int(int(datetime.now().strftime("%Y"))/100)*100 + datelist[0]
                        month = datelist[1]
                        day = datelist[2]
                        hour = datelist[3]
                        minute = datelist[4]
                        datetimestring = f'{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}'
                        print(datetimestring)
                        sleepseconds -= datelist[5]
                else:
                    count -= 1
                    if minute == 59:
                        hour += 1
                        minute = 0
                    else:
                        minute += 1
                        datetimestring = f'{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}'                    
            self.time_label.text = datetimestring
            await asyncio.sleep(sleepseconds)

    async def get_timing(self, widget, **kwargs):
        if self.ip_address != None and self.serial != None:
            modbus = PySolarmanV5(self.ip_address, self.serial)
            self.timed = None
            try:
                self.timed = (modbus.read_input_register_formatted(register_addr=33132, quantity=1, bitmask=0x2, bitshift=1)==1)
                self.chktimed.value = self.timed
                timing = modbus.read_holding_registers(register_addr=43141, quantity=10)
                self.current_label.value = timing[0]/10
                self.dcurrent_label.value = timing[1]/10
                self.chargestart.value = f'{timing[2]:02d}:{timing[3]:02d}:00'
                self.chargestop.value = f'{timing[4]:02d}:{timing[5]:02d}:00'
                self.dischargestart.value = f'{timing[6]:02d}:{timing[7]:02d}:00'
                self.dischargestop.value = f'{timing[8]:02d}:{timing[9]:02d}:00'
            except V5FrameError:
                print("Getting charge timings - Failed")
            modbus.sock.close()
            del modbus
    
    def set_device(self, widget):
        # is_valid not implemented for android 
        if hasattr(sys, 'getandroidapilevel'):
            self.ip_address = self.ip.value
            try:
                self.serial = int(self.serial_label.value)
                print(f'Set Device {self.ip_address} {self.serial}')
                self.add_background_task(self.get_datetime)
                self.get_details(None)
            except ValueError:
                print("Serial not a number")
        else:
            if self.ip.is_valid and self.serial_label.is_valid:
                self.ip_address = self.ip.value
                self.serial = int(self.serial_label.value)
                print(f'Set Device {self.ip_address} {self.serial}')
                self.add_background_task(self.get_datetime)
                self.get_details(None)

    def get_details(self, widget):
        self.add_background_task(self.get_timing)
        
    def set_datetime(self, widget):
        now = datetime.now()
        print("Setting time")
        values = [int(now.strftime("%y")), now.month, now.day, now.hour, now.minute, now.second]
        datetimestring = f'{int(int(datetime.now().strftime("%Y"))/100)*100+int(now.strftime("%y"))}-{now.month:02d}-{now.day:02d} {now.hour:02d}:{now.minute:02d}'
        if self.ip_address != None and self.serial != None:
            modbus = PySolarmanV5(self.ip_address,self.serial)
            try:
                modbus.write_multiple_holding_registers(register_addr=43000, values=values)
            except:
                datetimestring = self.datetimeplaceholder
        if 'modbus' in locals():
            modbus.sock.close()
            del modbus
        self.time_label.text = datetimestring
        
    def set_timing(self, widget):
        if sys.platform == 'win32':
            chargestart = self.chargestart._impl.native.Text.split(":")
            chargestop = self.chargestop._impl.native.Text.split(":")
            dischargestart = self.dischargestart._impl.native.Text.split(":")
            dischargestop = self.dischargestop._impl.native.Text.split(":")
        else:
            chargestart = self.chargestart.value.strftime('%H:%M').split(":")
            chargestop = self.chargestop.value.strftime('%H:%M').split(":")
            dischargestart = self.dischargestart.value.strftime('%H:%M').split(":")
            dischargestop = self.dischargestop.value.strftime('%H:%M').split(":")
        if float(self.current_label.value)*10 > 700:
            self.current_label.value = "70.0"
        if float(self.dcurrent_label.value)*10 > 700:
            self.dcurrent_label.value = "70.0"
        if self.ip_address != None and self.serial != None:
            modbus = PySolarmanV5(self.ip_address,self.serial)
            try:
                modbus.write_multiple_holding_registers(register_addr=43141, 
                    values=[
                        int(float(self.current_label.value)*10),
                        int(float(self.dcurrent_label.value)*10),
                        int(chargestart[0]),
                        int(chargestart[1]),
                        int(chargestop[0]),
                        int(chargestop[1]),
                        int(dischargestart[0]),
                        int(dischargestart[1]),
                        int(dischargestop[0]),
                        int(dischargestop[1])
                        ]
                    )
                if self.chktimed.value:
                    modbus.write_holding_register(register_addr=43110, value=35) # enable timed (dis)charge 
                else:
                    modbus.write_holding_register(register_addr=43110, value=1) # disable timed (dis)charge
            except:
                pass
        if 'modbus' in locals():
            modbus.sock.close()
            del modbus

    class ipaddress(validators.MatchRegex):
        IP_REGEX = (
            r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$"
        )

        def __init__(self, error_message: Optional[str] = None, allow_empty: bool = True):
            if error_message is None:
                error_message = "Input should be a valid ip address"
            super().__init__(
                self.IP_REGEX, error_message=error_message, allow_empty=allow_empty
            )

def main():
    return HelloWorld()

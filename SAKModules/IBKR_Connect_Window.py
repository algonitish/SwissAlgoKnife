import PySimpleGUI as sg
from secret import cred
import logging

logging.basicConfig(
    filename='SAK.log',
    level=logging.INFO, 
    format='{"time": %(asctime)s, "module": %(module)s, "function_name": %(funcName)s, "line_number": %(lineno)d, "message": %(message)s}', 
    datefmt='%m/%d/%Y %I:%M:%S %p'
    )

layout = [
            [sg.Text('Enter connection paramters below:')],
            [sg.Text('IP Address: ', size=(15,1)),sg.Input(cred.str_ib_ip, key='_IP_', size=(15,1))], 
            [sg.Text('Port: ', size=(15,1)),sg.Input(cred.int_ib_port, key='_PORT_', size=(15,1))], 
            [sg.Text('Client ID', size=(15,1)),sg.Input(cred.int_ib_uid, key='_UID_', size=(15,1))],
            [sg.Text('<Status Appears Here>', key='_OUTPUT_')],
            [sg.Button('Connect'), sg.Button('Disconnect'), sg.Button('Exit')]
        ]

def main(ib):
    win_ibkr_connect = sg.Window('IBKR: Connect', layout)
    logging.info("IBKR:Connect launched")

    while True:  # Event Loop
        event, values = win_ibkr_connect.Read()
        if event == 'Exit':
            logging.info("exit hit")
            win_ibkr_connect.Close()
            break
        if event == 'Connect':
            logging.info("Asked to connect.")
            try:
                logging.info("Trying to connect.")
                logging.info("%s %s %s", str(win_ibkr_connect.Element('_IP_').Get()),  str(win_ibkr_connect.Element('_PORT_').Get()), str(win_ibkr_connect.Element('_UID_').Get()))
                ib.connect(
                    str(win_ibkr_connect.Element('_IP_').Get()),
                    int(win_ibkr_connect.Element('_PORT_').Get()),
                    int(win_ibkr_connect.Element('_UID_').Get()),
                )
            except ConnectionRefusedError:
                win_ibkr_connect.Element('_OUTPUT_').Update("Connection Refused!")
                logging.info("Connection Refused!")
            except:
                win_ibkr_connect.Element('_OUTPUT_').Update("Error!")
                logging.info("Error!")
            if ib.isConnected() == True:
                win_ibkr_connect.Element('_OUTPUT_').Update("Connected!")
                logging.info("Connected!")

if __name__ == "__main__":
    from ib_insync import *
    ib = IB()
    main(ib)
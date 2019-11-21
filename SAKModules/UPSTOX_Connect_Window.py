from upstox_api.api import *
import PySimpleGUI as sg
import logging
from secret import cred
logging.basicConfig(
    filename='connection_window.log',
    level=logging.INFO, 
    format='{"time": %(asctime)s, "module": %(module)s, "function_name": %(funcName)s, "line_number": %(lineno)d, "message": %(message)s}', 
    datefmt='%m/%d/%Y %I:%M:%S %p'
    )

layout = [
            [sg.Text('Window area.')],
            [sg.Input(cred.upstox_api_key, key='_API_Key_'), sg.Input(cred.upstox_api_secret, key='_API_Secret_'), sg.Input('', key='_Redirect_URI_')],
            [sg.Text('xxxx URL Appears Here xxxx', key='_OUTPUT_')],
            [sg.Button('Connect'), sg.Button('Disconnect'), sg.Button('Exit')]
        ]

def main(up_session):
    win_upstox_connect = sg.Window('UPSTOX: Connect', layout)
    logging.info("UPSTOX:Connect launched")

    while True:  # Event Loop
        event, values = win_upstox_connect.Read()
        if event == 'Exit':
            logging.info("exit hit")
            win_upstox_connect.Close()
            break
        
        if event == 'Connect':
            logging.info("Asked to connect.")
            try:
                logging.info("Trying to connect.")
                logging.info("%s %s %s", 
                            str(win_upstox_connect.Element('_API_Key_').Get()),  
                            str(win_upstox_connect.Element('_API_Secret_').Get()), 
                            str(win_upstox_connect.Element('_Redirect_URI_').Get())
                            )
                up_session = Session(win_upstox_connect.Element('_API_Key_').Get())
                up_session.set_redirect_uri (win_upstox_connect.Element('_Redirect_URI_').Get())
                up_session.set_api_secret (win_upstox_connect.Element('_API_Secret_').Get())
                str_url = str(up_session.get_login_url())
                win_upstox_connect.Element('_OUTPUT_').Update(str_url)
                up_code =  sg.PopupGetText(
                                            message='Open this link and do the needful to get the "code" from the browser.', 
                                            default_text=str_url, 
                                            title='UPSTOX: Code'
                                            )
                up_session.set_code(up_code)
                cred.upstox_api_token = up_session.retrieve_access_token()
                win_upstox_connect.Element('_OUTPUT_').Update("Close window to continue.")
            except:
                win_upstox_connect.Element('_OUTPUT_').Update("Error!")
                logging.info("Error!")


if __name__ == "__main__":
    from upstox_api.api import Session
    up_session = Session('dummy_key')
    main(up_session)
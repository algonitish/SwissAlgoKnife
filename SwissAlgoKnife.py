import PySimpleGUI as sg
from ib_insync import *
from upstox_api.api import Session, Upstox
import logging, os
from secret import cred
from pathlib import Path

logging.basicConfig(
    filename='SAK.log',
    level=logging.INFO, 
    format='{"time": %(asctime)s, "module": %(module)s, "function_name": %(funcName)s, "line_number": %(lineno)d, "message": %(message)s}', 
    datefmt='%m/%d/%Y %I:%M:%S %p'
    )

logging.info("===SWISS ALGO KNIFE RUN BEGINS HERE===")

SAKIcon = Path(str(os.path.dirname( __file__ )) + '/SAK_Transparent.ico')

ib = IB()

str1 = 'https://api.upstox.com/index/dialog/authorize?apiKey='
str2 = '&redirect_uri='
str3 = '&response_type=code'

layout = [
            [
                sg.Text('IBKR', key='_IBKR_Connection_Status_', text_color='#FF0000'), 
                sg.Text('UPSTOX', key='_UPSTOX_Connection_Status_', text_color='#FF0000'),
                sg.Text('MySQL', key='_UPSTOX_Connection_Status_', text_color='#FF0000')
            ],
            [sg.Text('-----------------------------', key='_OUTPUT_')],
            [
                sg.Button('IBKR: Connect', border_width=0, size=(25,1)), 
                sg.Button('UPSTOX: Connect', border_width=0, size=(25,1), disabled=True),
                sg.Button('MySQL Utilities', border_width=0, size=(25,1))
            ],
            [
                sg.Button('IBKR: Historical OHLC', border_width=0, size=(25,1)),
                sg.Button('UPSTOX: Historical OHLC', border_width=0, size=(25,1), disabled=True),
                sg.Button('HDF5 Utilities', border_width=0, size=(25,1), disabled=True)
                
            ],
            [
                sg.Button('IBKR: Historical Tick Data', border_width=0, size=(25,1)),
                sg.Button('UPSTOX: Historical Tick Data', border_width=0, size=(25,1), disabled=True),
                sg.Button('NSE Option Chain Extractor', border_width=0, size=(25,1))
            
            ],
            [sg.Button('IBKR: All In One', border_width=0, size=(25,1))],
            [sg.Text('     ')],
            [
                sg.Button('Exit', size=(25,1), border_width=0), 
                sg.Button('Secrets', size=(25,1), border_width=0), 
                sg.Button('Help!', size=(25,1), border_width=0)
            ]
        ]

win_control = sg.Window('Control Home').Layout(layout)
win_control.set_icon(SAKIcon)


while True:
    ev1, vals1 = win_control.Read(timeout=100)

    if ev1 == 'IBKR: Connect':
        sg.Popup("Needs IBKR TWS/Gateway in Live Trading (not Read Only) Mode. Execution paused, please check.")
        from SAKModules import IBKR_Connect_Window
        logging.info("Calling IBKR_Connect_Window now.")
        IBKR_Connect_Window.main(ib)

    if ev1 == 'UPSTOX: Connect':
        up_session = Session(cred.upstox_api_token)
        up_session.set_redirect_uri (cred.upstox_api_redirect_uri)
        up_session.set_api_secret(cred.upstox_api_secret)
        up_code =  sg.PopupGetText(
                                    message='Open this link and do the needful to get the "code" from the browser.', 
                                    default_text=str1  
                                            + cred.upstox_api_key
                                            + str2
                                            + cred.upstox_api_redirect_uri                        
                                            + str3, 
                                    title='UPSTOX: Code'
                                )
        if (up_code != None) and (up_code != ''):
            up_session.set_code(up_code)
            up_token = up_session.retrieve_access_token()
            #up_object = Upstox(cred.upstox_api_key, up_token)
            #sg.Popup(up_object.get_profile())
        else:
            sg.Popup("Process failed. Try again.")
    if ev1 == 'MySQL Utilities':
        from SAKModules import MySQL_Allinone
        MySQL_Allinone.main()

    if ev1 == 'IBKR: Historical OHLC':
        from SAKModules import IBKR_Historical_Window
        logging.info("Calling IBKR_Historical_Window now.")
        IBKR_Historical_Window.main(ib)

    if ev1 == 'IBKR: Historical Tick Data':
        from SAKModules import IBKR_Tick_Data_Window
        logging.info("Calling IBKR_Historical_Window now.")
        IBKR_Tick_Data_Window.main(ib)
    
    if ev1 == 'IBKR: All In One':
        from SAKModules import IBKR_Allinone
        IBKR_Allinone.main(ib)

    if ev1 == 'NSE Option Chain Extractor':
        from SAKModules import SAK_NSEOptionChainExtractor
        SAK_NSEOptionChainExtractor.main()

    if ev1 == 'Help!':
        with open(os.getcwd() + '/SAKModules/help.txt', 'r') as fopen:
            str_help = fopen.read()
        sg.popup_scrolled('Help',str_help)
    
    if ev1 is None or ev1 == 'Exit':
        if ib.isConnected() == True:
            ib.disconnect()
            win_control.Close()
        break
        

    if ib.isConnected(): #[psg.Button('Exit')]
        win_control.Element('_IBKR_Connection_Status_').Update('IBKR', text_color='#00FF00')
    else:
        win_control.Element('_IBKR_Connection_Status_').Update('IBKR', text_color='#FF0000')

    # if upstox_conn is not None:
    #     win_control.Element('_UPSTOX_Connection_Status_').Update('UPSTOX', text_color='#00FF00')
    # else:
    #     win_control.Element('_UPSTOX_Connection_Status_').Update('UPSTOX', text_color='#FF0000')
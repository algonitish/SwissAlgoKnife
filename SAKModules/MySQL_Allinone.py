import PySimpleGUI as psg
import sqlalchemy, glob, logging, os
import pandas as pd
from secret import cred #path is relative to SAK.py, not this file.

logging.basicConfig(
    filename='SAK.log',
    level=logging.INFO, 
    format='{"time": %(asctime)s, "module": %(module)s, "function_name": %(funcName)s, "line_number": %(lineno)d, "message": %(message)s}', 
    datefmt='%m/%d/%Y %I:%M:%S %p'
    )

frame_connect = [
            [psg.Text('Enter database connection paramters below:')], #host, user, pass, dbas
            [
                psg.Text('Host: ', size=(15,1)),psg.Input(cred.str_mysql_host, key='_HOST_', size=(15,1)), 
                psg.Text('Database: ', size=(15,1)),psg.Input(cred.str_mysql_database, key='_DBAS_', size=(15,1))
            ],
            [
                psg.Text('User: ', size=(15,1)),psg.Input(cred.str_mysql_user, key='_USER_', size=(15,1)),
                psg.Text('Password:', size=(15,1)),psg.InputText(cred.str_mysql_password, key='_PWRD_', size=(15,1), password_char='*')
            ],
            [], 
            [psg.Text('Disconnected.', key='_OUTPUT_', text_color='red')],
            [psg.Button('Connect'), psg.Button('Disconnect')]
]

str_default_path = os.getcwd() + '/Downloads' #get path relative to SAK.py
list_types_of_data = ['Trade Ticks', 'OHLC 1D', 'OHLC 60m', 'OHLC 30m', 'OHLC 15m', 'OHLC 10m',  'OHLC 5m', 'OHLC 1m'] 
frame_load = [
                [psg.Text('To upload csv into database:')],
                [psg.Text('Select Directory:'), psg.Input(str_default_path, key='_LOAD_DIR_'), psg.FolderBrowse('Browse', target='_LOAD_DIR_')],
                [psg.Text('Data Type:'), psg.Combo(list_types_of_data, key='_DATA_TYPE_', size=(12,1))],
                [psg.Text('Number of files loaded this session:'), psg.Text('0', key='_COUNT_', font='Courier')],
                [psg.Button('Load', key='_LOAD_BUTTON_', disabled=True)]
]

frame_fetch = [ 
                [psg.Text('To fetch data from database to directory:')],
                [psg.Text('Select Directory:'), psg.Input(str_default_path, key='_FETCH_DIR_'), psg.FolderBrowse('Browse', target='_FETCH_DIR_')],
                [psg.Text('Data Type:'), psg.Combo(['dummy 1', 'dummy 2'])],
                [psg.Button('Load', key='_FETCH_BUTTON_', disabled=True)]
]

layout = [
            [psg.Frame('Connection Manager', frame_connect)],
            [psg.Frame('Database Loader', frame_load)],
            [psg.Frame('Data Fetcher', frame_fetch)],
            [psg.Button('Exit')]
        ]
def main():
    win_mysql_allinone = psg.Window('MySQL: All Functions', layout)
    while True:  # Event Loop
        event, values = win_mysql_allinone.Read()
        if event is None or event == 'Exit':
            win_mysql_allinone.Close()
            break
        if event == 'Connect':
            str_host = str(values['_HOST_'])
            str_user = str(values['_USER_'])
            str_pass = str(values['_PWRD_'])
            str_dbas = str(values['_DBAS_'])
            try:
                engine = sqlalchemy.create_engine('mysql+pymysql://'+str_user+':'+str_pass+'@'+str_host+'/' + str_dbas)
                connection = engine.raw_connection()
                win_mysql_allinone.FindElement('_OUTPUT_').update(value=str(engine.url), text_color='blue')
                logging.info('DBase connected: mysql+pymysql://'+str_user+':***'+'@'+str_host+'/' + str_dbas)
                win_mysql_allinone.FindElement('_LOAD_BUTTON_').update(disabled=False)
                #win_mysql_allinone.FindElement('_FETCH_BUTTON_').update(disabled=False) uncomment when fetch() is finished.
            except sqlalchemy.exc.SQLAlchemyError as err:
                logging.error(str(err))
                psg.popup(str(err))
            
        if event == 'Disconnect':
            logging.info('DBase disconnected.')
            connection.close()
            win_mysql_allinone.FindElement('_OUTPUT_').update(value='Disconnected.', text_color='red')
            win_mysql_allinone.FindElement('_LOAD_BUTTON_').update(disabled=True)
            win_mysql_allinone.FindElement('_FETCH_BUTTON_').update(disabled=True)

        if event == 'Load':
            str_path = str(values['_LOAD_DIR_'])
            intCounter = 0
            #['Trade Ticks', 'OHLC 1D', 'OHLC 60m', 'OHLC 30m', 'OHLC 15m', 'OHLC 10m',  'OHLC 5m', 'OHLC 1m'] 
            if values['_DATA_TYPE_'] == 'Trade Ticks':
                for filepath in glob.iglob(str_path):
                    dfToInsert = pd.read_csv(filepath)
                    dfToInsert = dfToInsert.drop(columns=['exchange', 'currency', 'dataType'])
                    c1 = ['time', 'symbol', 'price', 'size']
                    c2 = dfToInsert.columns.to_list()
                    if c1 == [x for x in c1 if x in c2]: 
                        dfToInsert.to_sql('tbl_tick_data', if_exists='append', con=engine, index=False)
                        intCounter+=1
                        print('{} - Uploaded {}.'.format(intCounter, dfToInsert.iloc[0,1]))
                        win_mysql_allinone['_COUNT_'].Update(value=str(intCounter))
                    else:
                        psg.popup('File not in correct format: {}'.format(c1))
            if values['_DATA_TYPE_'] != 'Trade Ticks':
                for filepath in glob.iglob(str_path):
                    dfToInsert = pd.read_csv(filepath)
                    str_tbl_name = 'tbl_ohlcv_'+ str(values['_DATA_TYPE_'])[-2:].lower()
                    c1 = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
                    c2 = dfToInsert.columns.to_list()
                    if c1 == [x for x in c1 if x in c2]: 
                        dfToInsert.to_sql(str_tbl_name, if_exists='append', con=engine, index=False)
                        intCounter+=1
                        print('{} - Uploaded {}.'.format(intCounter, dfToInsert.iloc[0,1]))
                        win_mysql_allinone.FindElement('_COUNT_').Update(value=str(intCounter))
                    else:
                        psg.popup('File not in correct format: {}'.format(c1))
            psg.popup(str_path)

        if event == 'Fetch':
            str_path = str(values['_FETCH_DIR_'])
            psg.popup(str_path)


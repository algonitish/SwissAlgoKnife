import PySimpleGUI as psg
import logging, time, os
import pandas as pd
from ib_insync import *
from datetime import datetime, timezone, timedelta
from dateutil import tz
from secret import cred

logging.basicConfig(
    level=logging.INFO, 
    format='{"time": %(asctime)s, "module": %(module)s, "function_name": %(funcName)s, "line_number": %(lineno)d, "message": %(message)s}', 
    datefmt='%m/%d/%Y %I:%M:%S %p',
    handlers=[
        logging.FileHandler(filename='SAK.log'),
        logging.StreamHandler()
        ]
    )

def utc2local (utc):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    return utc.astimezone(to_zone)

def local2utc(local):
    epoch = time.mktime(local.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return (local - offset).replace(tzinfo=None)

def getTickFor(ib, qualContract, dtmStartDate, dtmEndDate, intTicks, strWhatToShow, boolUseRTH, boolIgnoreSize, strPath):
    logging.info('Entered getTickFor().')
    strCurrency = qualContract[0].currency
    strExchange = qualContract[0].exchange
    strContract = qualContract[0].symbol
    stkContract = qualContract[0]
    
    #get the last tick of the day so that we know where to stop
    listEndOfDayTicks = ib.reqHistoricalTicks(stkContract, '', dtmEndDate, 10, strWhatToShow, boolUseRTH, boolIgnoreSize, None)
    dtmLastTickTime = listEndOfDayTicks[-1].time

    #initiate a listTicks to keep appending to later:
    listTicks = ib.reqHistoricalTicks(stkContract, dtmStartDate, '', intTicks, strWhatToShow, boolUseRTH, boolIgnoreSize, None)
    #now start looping through the day's ticks
    #initial starting point is set above with the end of the first listTicks
    dtmStartPoint = listTicks[-1].time
    #first fetch is already over:
    intCountRequests = 1
    logging.info('Request number {} Received {} ticks from {}(UTC) to {}(UTC).'.format(intCountRequests, len(listTicks), dtmStartDate, listTicks[-1].time))
    while (dtmStartPoint < dtmLastTickTime):
        listFetch = ib.reqHistoricalTicks(stkContract, dtmStartPoint, '', intTicks, strWhatToShow, boolUseRTH, boolIgnoreSize, None)
        if (listFetch[0].time != listFetch[-1].time): #ie, if the first tick != last tick of listTicks, it means there's more data to be had in the day
            listTicks = listTicks + listFetch
            dtmStartPoint = listTicks[-1].time # and increment next loop's start point to this listTick's last time
            intCountRequests += 1
        else:
            #reset start point to the end of trading hour, so that the next fetch automatically gets the next day's opening data
            dtmStartPoint = listTicks[-1].time + timedelta(0.1)
        time.sleep(0.1)
        logging.info('Request number {} Received {} ticks from {} (UTC) to {} (UTC).'.format(intCountRequests, len(listFetch), dtmStartPoint, listTicks[-1].time))

    #convert listTicks to a CSV and save
    dfTicks = pd.DataFrame(listTicks)
    dfTicks = dfTicks.rename(columns={'tickAttribLast':'symbol', 'specialConditions':'currency'})
    dfTicks['symbol'] = stkContract.symbol
    dfTicks['exchange'] = stkContract.exchange
    dfTicks['currency'] = stkContract.currency
    #dfTicks['time'] = dfTicks['time'].apply(utc2local)
    dfTicks['dataType'] = 'Ticks_' + strWhatToShow +'_RTH' if boolUseRTH else '_RHT+AMO'
    dfTicks.to_csv(strPath + '/' + strContract +'_'+ str(dtmStartDate) +'_'+ str(dtmEndDate)+'.csv', index=False)
    logging.info('FINISHED: {}'.format(strContract))
    psg.popup('Finished getting data for {}'.format(strContract))

#for getting contract data
listSecTypes = ['STK','CASH','IND'] # add these as useful: ,'OPT','FUT','FOP','CFD','BAG','WAR','BOND','CMDTY','NEWS','FUND'
listExchanges = ['NSE', 'IDEALPRO']
listCurrencies = ['INR', 'USD', 'JPY', 'CHF', 'EUR']

#for drawing table
listHeadings = ['date', 'open', 'high', 'low', 'close', 'volume', 'barCount', 'average']

#for placing data request
listDurStr2 = ['S', 'D', 'W', 'M', 'Y'] #!use with integer prefix
listBarSizes = ['1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
                '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins', '30 mins',
                '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
                '1 day', '1W', '1M']
listWhatToShows = ['TRADES', 'MIDPOINT', 'BID', 'ASK', 'BID_ASK', 'ADJUSTED_LAST', 'HISTORICAL_VOLATILITY', 
                    'OPTION_IMPLIED_VOLATILITY', 'REBATE_RATE', 'FEE_RATE', 'YIELD_BID', 'YIELD_ASK', 
                    'YIELD_BID_ASK', 'YIELD_LAST']

str_default_path = os.getcwd() + '/Downloads'

frame_connect = [
                    [psg.Text('Enter connection paramters below:')],
                    [
                        psg.Text('IP Address: ', size=(12,1)),psg.Input(cred.str_ib_ip, key='_IB_IP_', size=(15,1)),
                        psg.Text('Port: ', size=(6,1)),psg.Input(cred.int_ib_port, key='_IB_PORT_', size=(15,1)),
                        psg.Text('Client ID', size=(10,1)),psg.Input(cred.int_ib_uid, key='_IB_UID_', size=(15,1))
                    ], 
                    [psg.Text("Disconnected.", text_color='red', key='_IB_STATUS_')],
                    [psg.Button('Connect', key='_BT_CONN_', disabled=False), psg.Button('Disconnect', key='_BT_DISCO_', disabled=True)]
                ]

frame_qualify = [
                    [
                        psg.Input(default_text="RELIANCE", key='_Symbol_', tooltip='Exact IBKR symbol', size=(15,1)),
                        psg.Combo(listSecTypes, key='_SecType_', size = (4,1), tooltip='STK = Stock, CASH = Forex, IND = Index'),
                        psg.Combo(listExchanges, key='_Exchange_', size = (4,1)),
                        psg.Combo(listCurrencies, key='_Currency_', size = (4,1)),
                        psg.Text('Qualified Security: '),
                        psg.Text('<None>', size=(15,1), key='_OUTPUT_')
                    ],
                    [
                        psg.Button('Qualify', key='_BT_QUAL_', disabled=True)
                    ]
]

frame_tick = [            
            [
                psg.Text('Pick Dates: '),
                psg.Input(key='_StartDate_', size=(9,1), disabled=True, font='Courier'), 
                psg.CalendarButton('Start Date', target='_StartDate_'), 
                psg.Input(key='_EndDate_', size=(9,1), disabled=True, font='Courier'), 
                psg.CalendarButton('End Date', target='_EndDate_')
            ],
            [
                psg.Input(default_text="1000", key='_tickCount_', tooltip='Number of ticks to fetch at a time', size=(4,1), disabled=True),
                psg.Combo(listWhatToShows, key='_whatToShow_', auto_size_text=True),
                psg.Checkbox('RTH?', key='_useRTH_'),
                psg.Checkbox('Size Only Ticks?', key='_ignoreSize_')

            ],
            [
                psg.Text('Your Folder', size=(15, 1), auto_size_text=False), 
                psg.InputText(str_default_path, key='_targetFolder_'), 
                psg.FolderBrowse(target='_targetFolder_')
            ],
            [psg.Button('Get Ticks', key='_BT_TICK_', disabled=True)],
        ]

frame_OHLC =[
                [
                    psg.Input(default_text=1, key='_DurStr1_', size=(4,1)),
                    psg.Combo(listDurStr2, key='_DurStr2_', size=(4,1)),
                    psg.Combo(listBarSizes, key='_BarSize_', size=(8,1)),
                    psg.Combo(listWhatToShows, key='_WhatToShow_', auto_size_text=True)
                ],
                [psg.Button('Fetch', key='_BT_OHLC_', disabled=True), psg.Button('Download', key='_BT_DL_', disabled=True)],
                [psg.Text('Data Preview: ')],
                [
                    psg.Table(key='sgtable', values = [['','','','','','','','']], #placeholders until we learn how to dynamically create columns in PySimpleGUI
                                        headings=listHeadings, 
                                        auto_size_columns=True,
                                        alternating_row_color='#add8e6',
                                        num_rows=3)
                ]
]

layout = [
            [psg.Frame('Connection Manager', frame_connect)],
            [psg.Frame('Qualify Contract', frame_qualify)],
            [psg.Frame('Tick Data', frame_tick)],
            [psg.Frame('OHLC Data', frame_OHLC)],
            [psg.CButton('Exit')]
]
def main(ib):
    win_ibkr_allinone = psg.Window('IBRK Utilities', layout=layout)
    while True:  # Event Loop
        event, values = win_ibkr_allinone.Read()
        if event in (None, 'Exit'):
            win_ibkr_allinone.Close()
            break
        if event == '_BT_CONN_':
            logging.info("Connect clicked.")
            try:
                logging.info("Trying to connect.")
                ib.connect(
                    str(win_ibkr_allinone['_IB_IP_'].Get()),
                    int(win_ibkr_allinone['_IB_PORT_'].Get()),
                    int(win_ibkr_allinone['_IB_UID_'].Get())
                    )
            except ConnectionRefusedError:
                win_ibkr_allinone.Element('_IB_STATUS_').Update("Connection Refused!", text_color='red')
                logging.info("Connection Refused!")
            except:
                win_ibkr_allinone.Element('_IB_STATUS_').Update("Error!")
                logging.info("Error!")
            if ib.isConnected() == True:
                win_ibkr_allinone.Element('_IB_STATUS_').Update("Connected!", text_color='green')
                win_ibkr_allinone.Element('_BT_CONN_').Update(disabled=True) #can't connect if altready connected
                win_ibkr_allinone.Element('_BT_DISCO_').Update(disabled=False) #to disconnect after connection
                win_ibkr_allinone.Element('_BT_QUAL_').Update(disabled=False) #after every conn, fresh qualification
                win_ibkr_allinone.Element('_BT_TICK_').Update(disabled=True) #not active until qual()
                win_ibkr_allinone.Element('_BT_OHLC_').Update(disabled=True) #not active until qual()
                win_ibkr_allinone.Element('_BT_DL_').Update(disabled=True) #not active until qual()
                logging.info("Connected!")
        if event == '_BT_DISCO_':
            logging.info('Disconnect clicked.')
            if ib.isConnected == True:
                ib.disconnect()
                logging.info('Disconnected successfully.')
                win_ibkr_allinone.Element('_IB_STATUS_').Update("Disconnected.", text_color='red')
                win_ibkr_allinone.Element('_BT_CONN_').Update(disabled=False)
                win_ibkr_allinone.Element('_BT_DISCO_').Update(disabled=True)
                win_ibkr_allinone.Element('_BT_QUAL_').Update(disabled=True)
                win_ibkr_allinone.Element('_BT_TICK_').Update(disabled=True)
                win_ibkr_allinone.Element('_BT_OHLC_').Update(disabled=True)
                win_ibkr_allinone.Element('_BT_DL_').Update(disabled=True)
            else:
                win_ibkr_allinone.Element('_IB_STATUS_').Update("Disconnected.", text_color='red')
                win_ibkr_allinone.Element('_BT_CONN_').Update(disabled=False)
                win_ibkr_allinone.Element('_BT_DISCO_').Update(disabled=True)
                win_ibkr_allinone.Element('_BT_QUAL_').Update(disabled=True)
                win_ibkr_allinone.Element('_BT_TICK_').Update(disabled=True)
                win_ibkr_allinone.Element('_BT_OHLC_').Update(disabled=True)
                win_ibkr_allinone.Element('_BT_DL_').Update(disabled=True)
                logging.info('Faked a disconnection.')
        if event == '_BT_QUAL_':
            if values['_SecType_'] == 'STK':
                contract = Stock(values['_Symbol_'], values['_Exchange_'],values['_Currency_'])
            if values['_SecType_'] == 'CASH':
                contract = Forex(values['_Symbol_'])
            if values['_SecType_'] == 'IND':
                contract = Index(values['_Symbol_'], values['_Exchange_'],values['_Currency_'])
            qual = ib.qualifyContracts(contract)
            logging.info(str(qual))
            win_ibkr_allinone['_OUTPUT_'].Update(str(qual[0].symbol))
            win_ibkr_allinone.Element('_BT_TICK_').Update(disabled=False) #enable getting tick data
            win_ibkr_allinone.Element('_BT_OHLC_').Update(disabled=False) #enable getting OHLC data
        if event == '_BT_TICK_':
            logging.info('Starting tick fetch.')
            fmt = '%Y-%m-%d %H:%M:%S'
            strStartTime = win_ibkr_allinone['_StartDate_'].Get() #datetime(2019, 11, 7, 3, 00, tzinfo=timezone.utc)
            dtmStartTime = datetime.strptime(strStartTime, fmt)      
            strEndTime = win_ibkr_allinone['_EndDate_'].Get() #datetime(2019, 11, 8, 11, 00, tzinfo=timezone.utc)    
            dtmEndTime = datetime.strptime(strEndTime, fmt)
            dtmEndTime = dtmEndTime.replace(hour=23, minute=23)
            intTicks = int(win_ibkr_allinone['_tickCount_'].Get())
            strWhatToShow = str(win_ibkr_allinone['_whatToShow_'].Get())
            boolUseRTH = bool(win_ibkr_allinone['_useRTH_'].Get())
            boolIgnoreSize = bool(win_ibkr_allinone['_ignoreSize_'].Get())
            strPath = str(win_ibkr_allinone['_targetFolder_'].Get())
            logging.info('{},{},{},{},{},{},{}'.format(dtmStartTime, dtmEndTime,intTicks,strWhatToShow,boolUseRTH,boolIgnoreSize,strPath))
            if dtmEndTime > dtmStartTime:
                psg.popup('Starting download for {}'.format(qual[0].symbol))
                getTickFor(ib, qual, dtmStartTime, dtmEndTime, intTicks, strWhatToShow, boolUseRTH, boolIgnoreSize, strPath)
        if event == '_BT_OHLC_':
            strDuration = str(values['_DurStr1_']) +' ' + str(values['_DurStr2_'])
            strBarSize = str(values['_BarSize_'])
            strWhatToShow = str(values['_WhatToShow_'])
            logging.info('strDuration:%s , strBarSize: %s , strWhatToShow: %s', strDuration, strBarSize, strWhatToShow)
            barData = ib.reqHistoricalData(contract, '',strDuration, strBarSize, strWhatToShow, 1, 1, False)
            listData = [[item.date.strftime("%Y%m%d, %H:%M:%S"), item.open, item.high, item.low, item.close, item.volume, item.barCount, item.average] for item in barData]
            dfStockData = pd.DataFrame(listData)
            if dfStockData.shape[1]==8 and dfStockData.shape[0]>0:
                logging.info('dfStockData sample: %s',dfStockData.head(3))
                dfStockData.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'barCount', 'average']
                relist = dfStockData.values.tolist()
                win_ibkr_allinone.Element('sgtable').Update(values=relist,
                                                            num_rows=3,
                                                            visible = True)
            win_ibkr_allinone.Element('_BT_DL_').Update(disabled=False) #enable getting OHLC data
        if event == '_BT_DL_':
            if dfStockData.shape[1]==8 and dfStockData.shape[0]>0:
                file_name = psg.PopupGetFile('Please enter filename to save (if file exists, it will be overwritten): ', save_as=True) 
                fileTarget = open(file_name, 'w+')
                dfStockData.to_csv(fileTarget)
                fileTarget.close()
                psg.Popup("File saved.")
            #if NOT populated
            else:
                psg.Popup("Please fetch some data before trying to save it.")


if __name__ == "__main__":
    ib = IB()
    main(ib) 
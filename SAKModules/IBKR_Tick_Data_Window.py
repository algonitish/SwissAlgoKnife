import PySimpleGUI as sg
from ib_insync import *
from datetime import datetime, timezone, timedelta
import time, logging, os
import pandas as pd
from secret import cred

logging.basicConfig(
    filename='SAK.log',
    level=logging.INFO, 
    format='{"time": %(asctime)s, "module": %(module)s, "function_name": %(funcName)s, "line_number": %(lineno)d, "message": %(message)s}', 
    datefmt='%m/%d/%Y %I:%M:%S %p'
    )

str_default_path = os.getcwd() + '/downloaded'

#for getting contract data
listSecTypes = ['STK','CASH','IND'] # add these as useful: ,'OPT','FUT','FOP','CFD','BAG','WAR','BOND','CMDTY','NEWS','FUND'
listExchanges = ['NSE', 'IDEALPRO']
listCurrencies = ['INR', 'USD', 'JPY', 'CHF', 'EUR']

#for placing data request
listDurStr2 = ['S', 'D', 'W', 'M', 'Y'] #!use with integer prefix
listBarSizes = ['1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
                '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins', '30 mins',
                '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
                '1 day', '1W', '1M']
listWhatToShows = ['Bid_Ask', 'Midpoint', 'Trades']

# All the stuff inside your window.
layout= [            
            [
                sg.Input(default_text="RELIANCE", key='_Symbol_', tooltip='Exact IBKR symbol', size=(10,1)),
                sg.Combo(listSecTypes, key='_SecType_', auto_size_text=True, tooltip='STK = Stock, CASH = Forex, IND = Index'),
                sg.Combo(listExchanges, key='_Exchange_', auto_size_text=True),
                sg.Combo(listCurrencies, key='_Currency_', auto_size_text=True)
            ],
            [
                sg.Button('Qualify'), sg.Text('Qualified Security: '), sg.Text('<None>', size=(15,1), key='_OUTPUT_')
            ],
            [
                sg.Input(key='_StartDate_', size=(9,1), disabled=True), 
                sg.CalendarButton('Start Date', target='_StartDate_'), 
                sg.Input(key='_EndDate_', size=(9,1), disabled=True), 
                sg.CalendarButton('End Date', target='_EndDate_'),
                sg.Text('Pick Dates')
            ],
            [
                sg.Input(default_text="1000", key='_tickCount_', tooltip='Number of ticks to fetch at a time', size=(4,1), disabled=True),
                sg.Combo(listWhatToShows, key='_whatToShow_', auto_size_text=True),
                sg.Checkbox('RTH?', key='_useRTH_'),
                sg.Checkbox('Size Only Ticks?', key='_ignoreSize_')

            ],
            [
                sg.Text('Your Folder', size=(15, 1), auto_size_text=False, justification='right'), 
                sg.InputText(str_default_path, key='_targetFolder_'), 
                sg.FolderBrowse(target='_targetFolder_')
            ],
            [sg.Button('Fetch'), sg.Button('Download'), sg.CButton('Close', key='_CloseWindow_')],
            [sg.Text('Data gathered: '), sg.Text('',key='_TickCount_')]
        ]


def utc2local (utc):
    #NOTE converts UTC time to LOCAL
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return (utc + offset).replace(tzinfo=None)

def local2utc(local):
    #NOTE converts LOCAL time to UTC
    epoch = time.mktime(local.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return (local - offset).replace(tzinfo=None)


def loop_reqHistoricalTicks(ib, stkContract, dtmStartTime, dtmEndTime, intTicks, strWhatToShow, boolUseRTH, boolIgnoreSize):
    listEndOfDayTicks = ib.reqHistoricalTicks(stkContract, '', dtmEndTime, 10, strWhatToShow, boolUseRTH, boolIgnoreSize, None)
    dtmLastTickTime = listEndOfDayTicks[-1].time

    #now start looping through the day's ticks
    listTicks = ib.reqHistoricalTicks(stkContract, dtmStartTime, '', intTicks, strWhatToShow, boolUseRTH, boolIgnoreSize, None)
    dtmStartPoint = listTicks[-1].time
    intCountRequests = 1
    print('Request number {} Received {} ticks from {} to {}'.format(intCountRequests, len(listTicks), utc2local(dtmStartTime), utc2local(listTicks[-1].time)))
    while (dtmStartPoint < dtmLastTickTime):
        listFetch = ib.reqHistoricalTicks(stkContract, dtmStartPoint, '', intTicks, strWhatToShow, boolUseRTH, boolIgnoreSize, None)
        if (listFetch[0].time != listFetch[-1].time):
            listTicks = listTicks + listFetch
            dtmStartPoint = listTicks[-1].time
            intCountRequests += 1
        else:
            dtmStartPoint = listTicks[-1].time + timedelta(0.1)
        time.sleep(0.2)
        print('Request number {} Received {} ticks from {} (UTC) to {} (UTC).'.format(intCountRequests, len(listFetch), listFetch[0].time, listFetch[-1].time))
    return listTicks


def main(ib):
    from ib_insync import Stock, Forex, Index
    win_historical_ticks = sg.Window('IBKR Historical Ticks', layout)
    #win_historical_ticks.Element('_TickCount_').Update('0')
    
    # Event Loop to process "events" and get the "values" of the inputs
    while True:  # Event Loop
        event, values = win_historical_ticks.Read()

        if event == '_CloseWindow_':
            #? commenting out "disconnect()" because any calling procedure would not want a child to disconnect it
            #ib.disconnect()
            logging.info("Close hit")
            win_historical_ticks.close()
            break

        if event == 'Qualify':
            # Update the "output" element to be the value of "input" element
            win_historical_ticks.Element('_OUTPUT_').Update(values['_Symbol_'])
            if values['_SecType_'] == 'STK':
                contract = Stock(values['_Symbol_'], values['_Exchange_'],values['_Currency_'])
            if values['_SecType_'] == 'CASH':
                contract = Forex(values['_Symbol_'])
            if values['_SecType_'] == 'IND':
                contract = Index(values['_Symbol_'], values['_Exchange_'],values['_Currency_'])
            qual = ib.qualifyContracts(contract)
            logging.info(str(qual))

        if event == 'Fetch':
            #NOTE add validations here
            if values['_targetFolder_'] != '':
                dtmStartTime = datetime.strptime(str(values['_StartDate_']), '%Y-%m-%d %H:%M:%S')
                dtmStartTime = dtmStartTime.replace(hour=0, minute=1)
                dtmEndTime  = datetime.strptime(str(values['_EndDate_']), '%Y-%m-%d %H:%M:%S')
                dtmEndTime = dtmEndTime.replace(hour=23, minute=59)
                
                intTicks = int(values['_tickCount_'])
                # whatToShow (str) – One of ‘Bid_Ask’, ‘Midpoint’ or ‘Trades’.
                strWhatToShow = str(values['_whatToShow_'])
                # useRTH – If True then only show data from within Regular Trading Hours, if False then show all data.
                boolUseRTH = bool(values['_useRTH_'])
                # ignoreSize (bool) – Ignore bid/ask ticks that only update the size.
                boolIgnoreSize = bool(values['_ignoreSize_'])
                #sg.popup(str([dtmStartTime, " - ", dtmEndTime, " - ", intTicks, " - ", strWhatToShow, " - ", boolUseRTH, " - ", boolIgnoreSize]))
                if dtmEndTime > dtmStartTime:
                    listTicks = loop_reqHistoricalTicks(ib, contract, dtmStartTime, dtmEndTime, intTicks, strWhatToShow, boolUseRTH, boolIgnoreSize)
                #convert listTicks to a CSV and save
                dfTicks = pd.DataFrame(listTicks)
                dfTicks = dfTicks.rename(columns={'tickAttribLast':'symbol', 'specialConditions':'currency'})
                dfTicks['symbol'] = contract.symbol
                dfTicks['exchange'] = contract.exchange
                dfTicks['currency'] = contract.currency
                dfTicks['time'] = dfTicks['time'].apply(utc2local)
                dfTicks['dataType'] = 'Ticks_' + str(values['_whatToShow_']) +('_RTH' if boolUseRTH else '_RHT+AMO')
                #For Linux uncomment below
                #dfTicks.to_csv(values['_targetFolder_'] +'/'+ contract.symbol +'_'+ str(dtmStartTime) +'_'+ str(dtmEndTime)+'.csv', index=False)
                #For Windows uncomment below
                dfTicks.to_csv(str_default_path +'//'+ contract.symbol +'_'+ dtmStartTime.strftime("%Y%M%d_%H%M%S") +'_'+ dtmEndTime.strftime("%Y%M%d_%H%M%S") +'.csv', index=False)

if __name__ == "__main__":
    from ib_insync import *
    ib = IB()
    conn = ib.connect(cred.str_ib_ip, cred.int_ib_port, cred.int_ib_uid)
    main(ib)

datetime.now().strftime("%Y%M%d_%H%M%S")
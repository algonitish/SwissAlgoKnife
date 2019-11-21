import PySimpleGUI as sg
import logging
import pandas as pd
from secret import cred

logging.basicConfig(
    filename='SAK.log',
    level=logging.INFO, 
    format='{"time": %(asctime)s, "module": %(module)s, "function_name": %(funcName)s, "line_number": %(lineno)d, "message": %(message)s}', 
    datefmt='%m/%d/%Y %I:%M:%S %p'
    )

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

layout= [            
            [
                sg.Input(default_text="RELIANCE", key='_Symbol_', tooltip='Exact IBKR symbol'),
                sg.Combo(listSecTypes, key='_SecType_', auto_size_text=True, tooltip='STK = Stock, CASH = Forex, IND = Index'),
                sg.Combo(listExchanges, key='_Exchange_', auto_size_text=True),
                sg.Combo(listCurrencies, key='_Currency_', auto_size_text=True)
            ],
            [sg.Button('Qualify'), sg.Text('Qualified Security: '), sg.Text('<None>', size=(15,1), key='_OUTPUT_')],
            [
                sg.Input(default_text=1, key='_DurStr1_', size=(3,1)),
                sg.Combo(listDurStr2, key='_DurStr2_', size=(3,1)),
                sg.Combo(listBarSizes, key='_BarSize_', size=(7,1)),
                sg.Combo(listWhatToShows, key='_WhatToShow_', auto_size_text=True)
            ],
            [sg.Button('Fetch'), sg.Button('Download'), sg.Button('Exit')],
            [sg.Text('Data Preview: ')],
            [sg.Table(key='sgtable', values = [['','','','','','','','']], #placeholders until we learn how to dynamically create columns in PySimpleGUI
                                    headings=listHeadings, 
                                    auto_size_columns=True,
                                    alternating_row_color='#add8e6',
                                    num_rows=1)]
        ]

def main(ib):
    from ib_insync import Stock, Forex, Index
    win_historical = sg.Window('Historical OHLC', layout)

    while True:  # Event Loop
        event, values = win_historical.Read()
        if event == 'Exit':
            #? commenting out "disconnect()" because any calling procedure would not want a child to disconnect it
            #ib.disconnect()
            logging.info("exit hit")
            win_historical.Close()
            break

        if event == 'Qualify':
            # Update the "output" element to be the value of "input" element
            win_historical.Element('_OUTPUT_').Update(values['_Symbol_'])
            if values['_SecType_'] == 'STK':
                contract = Stock(values['_Symbol_'], values['_Exchange_'],values['_Currency_'])
            if values['_SecType_'] == 'CASH':
                contract = Forex(values['_Symbol_'])
            if values['_SecType_'] == 'IND':
                contract = Index(values['_Symbol_'], values['_Exchange_'],values['_Currency_'])
            qual = ib.qualifyContracts(contract)
            logging.info(str(qual))

        if event == 'Fetch':
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
                win_historical.Element('sgtable').Update(values=relist,
                                                            num_rows=25,
                                                            visible = True)
        if event == 'Download':
            #check if the DatFrame is minimally populated or not.
            #if populated:
            if dfStockData.shape[1]==8 and dfStockData.shape[0]>0:
                file_name = sg.PopupGetFile('Please enter filename to save (if file exists, it will be overwritten): ', save_as=True) 
                fileTarget = open(file_name, 'w+')
                dfStockData.to_csv(fileTarget)
                fileTarget.close()
                sg.Popup("File saved.")
            #if NOT populated
            else:
                sg.Popup("Please fetch some data before trying to save it.")

if __name__ == "__main__":
    from ib_insync import *
    ib = IB()
    conn = ib.connect(cred.str_ib_ip, cred.int_ib_port, cred.int_ib_uid)
    main(ib)
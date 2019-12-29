# SwissAlgoKnife
Utilities to automate small daily tasks for algo traders.

~~WARNING: Based on https://github.com/PySimpleGUI/, these are one shot windows. Plan your workflow, or be prepared to open and close the application in entirety since a window once closed cannot be opened again. As soon as there's a solution for this, this warning will be removed.~~ Latest change made to SwissAlgoKnife.py (2019-12-29) allow windows to opened and close multiple times. The change was to use read-execute on the files contained in SAKModules directory, rather than importing them at the click of a button. This also allows new modules to be added to the project without any changes needed in the front end.

**Project Structure:**

    SwissAlgoKnife
        |-SwissAlgoKnife.py
        |-SAKModules
            |-IBKRAllinone.py
            |-MySQL_Allinone.py
            |-IBKR_Connect_Window.py
            |-IBKR_Historical_Window.py
            |-IBKR_Tick_Data_Window.py
            |-ALPACA_Connect.py
            |-UPSTOX_Connect_Window.py
            |-SAK_NSEOptionChainExtractor.py
            |-__pycache__
        |-Secret
            |-Cred.py
        |-Downloads
            |-<various downloaded data files>
        |-__pycache__

**Description of files**

- SwissAlgoKnife.py - just an entry point to the application.
- SAKModules - Folder containing all utilities. Each utility is designed to also be a standalone file.
- IBKRAllinone.py - All IBKR functions in one file: Connect, get OHLC Data, get Tick Data
- MySQL_Allinone.py - All MySQL functions in one file: Connect, store OHLC Data, store Tick Data. (TODO: (1) Retrieval function WIP, (2) store Option Chain Data.)
- IBKR_Connect_Window.py - older window. To connect to IBKR.
- IBKR_Historical_Window.py - older window. To get OHLC Data.
- IBKR_Tick_Data_Window.py - older window. To get tick Data.
- SAK_NSEOptionChainExtractor.py - crawls and collects data from NSE Options Chain pages. Creates a separate CSV file for each symbol. Will keep appending to CSV if file isn't removed from directory. (TODO: (1) Subdivide Downloads directory into different folders for different types of downloaded data, (2) pick up list_identifiers from a file instead of hardcoded values.)
- ALPACA_Connect.py - WIP.
- SAK_Zerodha.py - coming sooner.
- SAK_Fyers.py - coming later.
- UPSTOX_Connect_Window.py - frozen due to Upstox discontinuing API.
- __pycache__ - don't touch.
- Secret - folder for credential files
- Cred.py - file containing credentials for all APIs in one place.
- Downloads - folder for all downloaded files across utilities.
- __pycache__ - don't touch.

**Interactive Brokers Utilities**

Written with https://github.com/erdewit/ib_insync.

- Connect to TWS or Gateway on localhost:port:UID
- View and download OHLC data for one symbol, one request at a time
- Download Tick data for one symbol, between any two start and end dates

**MySQL Utilities**

Written using SQLAlchemy.

- Connect to local MySQL server
- Commit OHLC and Tick data files to respective tables

**Upstox Utilities**

_Frozen due to unavailability of Upstox Historical API_

**Zerodha Utilities**

_WIP_

**Fyers Utilities**

_WIP_

**HDF5 Utilities**

_Planning_

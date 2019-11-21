import alpaca_trade_api as tradeapi
import time
from secret import cred

api = tradeapi.REST(cred.APCA_API_KEY_ID, cred.APCA_API_SECRET_KEY, cred.APCA_API_BASE_URL) # or use ENV Vars shown below
account = api.get_account()
api.list_positions()

# Check if the market is open now.
clock = api.get_clock()
print('The market is {}'.format('open.' if clock.is_open else 'closed.'))

# Check when the market was open on Dec. 1, 2018
date = '2019-11-03'
calendar = api.get_calendar(start=date, end=date)[0]
print('The market opened at {} and closed at {} on {}.'.format(
    calendar.open,
    calendar.close,
    date
))

# Get daily price data for AAPL over the last 5 trading days.
barset = api.get_barset('AAPL', 'day', limit=5)
aapl_bars = barset['AAPL']

# See how much AAPL moved in that timeframe.
week_open = aapl_bars[0].o
week_close = aapl_bars[-1].c
percent_change = (week_close - week_open) / week_open * 100
print('AAPL moved {}% over the last 5 days'.format(percent_change))

# Submit a market order to buy 1 share of Apple at market price
ord_mkt = api.submit_order(
    symbol='AAPL',
    qty=1,
    side='buy',
    type='market',
    time_in_force='gtc'
)

# Submit a limit order to attempt to sell 1 share of AMD at a
# particular price ($20.50) when the market opens
ord_lmt = api.submit_order(
    symbol='AMD',
    qty=1,
    side='sell',
    type='limit',
    time_in_force='opg',
    limit_price=20.50
)

# The security we'll be shorting
symbol = 'TSLA'

# Submit a market order to open a short position of one share
ord_shrt = api.submit_order(symbol, 1, 'sell', 'market', 'day')
print("Market order submitted.")

# Submit a limit order to attempt to grow our short position
# First, get an up-to-date price for our symbol
symbol_bars = api.get_barset(symbol, 'minute', 1).df.iloc[0]
symbol_price = symbol_bars[symbol]['close']
# Submit an order for one share at that price
ord_shrt = api.submit_order(symbol, 1, 'sell', 'limit', 'day', symbol_price)
print("Limit order submitted.")

# Wait a second for our orders to fill...
print('Waiting...')
time.sleep(1)

# Check on our position
position = api.get_position(symbol)
if int(position.qty) < 0:
    print(f'Short position open for {symbol}')

# Submit a market order and assign it a Client Order ID.
api.submit_order(
    symbol='AAPL',
    qty=1,
    side='buy',
    type='market',
    time_in_force='gtc',
    client_order_id='my_first_order'
)

# Get our order using its Client Order ID.
my_order = api.get_order_by_client_order_id('my_first_order')
print('Got order #{}'.format(my_order.id))

# Get the last 100 of our closed orders
closed_orders = api.list_orders(
    status='closed',
    limit=100
)

# Get only the closed orders for a particular stock
closed_aapl_orders = [o for o in closed_orders if o.symbol == 'AAPL']
print(closed_aapl_orders)

#Websockets to receive real-time updates about the status of your orders as they change
conn = tradeapi.stream2.StreamConn(cred.APCA_API_KEY_ID, cred.APCA_API_SECRET_KEY)

# Handle updates on an order you've given a Client Order ID.
# The r indicates that we're listening for a regex pattern.
client_order_id = r'my_client_order_id'
@conn.on(client_order_id)
async def on_msg(conn, channel, data):
    # Print the update to the console.
    print("Update for {}. Event: {}.".format(client_order_id, data['event']))

# Start listening for updates.
conn.run(['trade_updates'])

# Get our position in AAPL.
aapl_position = api.get_position('AAPL')

# Get a list of all of our positions.
portfolio = api.list_positions()

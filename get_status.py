# -*- coding: GBK -*-
import os
from datetime import datetime
from futu import *
import pandas as pd

FUTU_OPEND_ADDRESS = '127.0.0.1'  # Futu OpenD listening address
FUTU_OPEND_PORT = 11111  # Futu OpenD listening port

DIR = os.path.dirname(os.path.abspath(__file__))
PDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PW_FILENAME = 'passwords/futu_trd_pw.txt'
PW_PATH = os.path.join(PDIR, PW_FILENAME)
TRADING_PWD = next(open(PW_PATH, 'r')).strip()  # Trading password, used to unlock trading for real trading environment
print(PW_PATH)

TRADING_ENVIRONMENT = TrdEnv.SIMULATE  # Trading environment: REAL / SIMULATE
TRADING_MARKET = TrdMarket.HK  # Transaction market authority, used to filter accounts
TRADING_PERIOD = KLType.K_1M  # Underlying trading time period

STATUS_FILENAME = 'status/' + str(datetime.now().date()) + '.csv'
STATUS_PATH = os.path.join(DIR, STATUS_FILENAME)

status_list = []
for mkt in [TrdMarket.HK, TrdMarket.US, TrdMarket.CN]:
    trd_ctx = OpenSecTradeContext(filter_trdmarket=mkt, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)
    ret, data = trd_ctx.accinfo_query(trd_env=TRADING_ENVIRONMENT)
    if ret == RET_OK:
        status_list.append(data)
        # print(data['power'][0])  # Get the first buying power
        # print(data['power'].values.tolist())  # convert to list
    else:
        print('accinfo_query error: ', data)

status_df = pd.concat(status_list, ignore_index=True)
status_df.insert(0, 'market', ['HK', 'US', 'CN'])

status_df.to_csv(STATUS_PATH)

trd_ctx.close()  # Close the current connection
if __name__ == '__main__':
    print(status_df)
    # print(status_df.columns)
    # print(status_df.total_assets[0])
    
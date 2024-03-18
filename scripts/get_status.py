# -*- coding: GBK -*-
import os
from datetime import datetime
from futu import *
import pandas as pd

FUTU_OPEND_ADDRESS = '127.0.0.1'  # Futu OpenD listening address
FUTU_OPEND_PORT = 11111  # Futu OpenD listening port
TRADING_PWD = os.getenv('FUTU_TRD_PW')  # Trading password, used to unlock trading for real trading environment

DIR = os.path.dirname(os.path.abspath(__file__))
PDIR = os.path.dirname(DIR)

stats_dir = os.path.join(PDIR, 'stats')
os.makedirs(stats_dir, exist_ok=True)
STATUS_FILENAME = str(datetime.now().date()) + '.csv'
STATUS_PATH = os.path.join(stats_dir, STATUS_FILENAME)

# Initialize the list outside the loop
status_list = []

for env in [TrdEnv.REAL, TrdEnv.SIMULATE]:
    # Initialize the list inside the outer loop
    env_status_list = []
    for mkt in [TrdMarket.HK, TrdMarket.US, TrdMarket.CN, TrdMarket.HKCC]:
        trd_ctx = OpenSecTradeContext(filter_trdmarket=mkt, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)
        ret, data = trd_ctx.accinfo_query(trd_env=env)
        if ret == RET_OK:
            data['market'] = mkt  # Directly assign market name to the dataframe
            data['trading_env'] = env  # Directly assign trading environment to the dataframe
            env_status_list.append(data)
        else:
            print('accinfo_query error: ', data)
        trd_ctx.close()  # Close the trade context to avoid resource leak

    # Concatenate data for each environment
    if env_status_list:
        env_status_df = pd.concat(env_status_list, ignore_index=True)
        status_list.append(env_status_df)

# Concatenate all dataframes into one
if status_list:
    status_df = pd.concat(status_list, ignore_index=True)
    cols = ['trading_env', 'market'] + [col for col in status_df.columns if col not in ['market', 'trading_env']]
    status_df = status_df[cols]
    print(status_df)
    status_df.to_csv(STATUS_PATH)
else:
    print("No data retrieved.")

trd_ctx.close()  # Close the current connection
if __name__ == '__main__':
    print(status_df)
    
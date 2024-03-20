from flask import Flask, request, jsonify
import os
import pandas as pd

app = Flask(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
pdir = os.path.dirname(dir)

@app.route('/daily_assets', methods=['GET'])
def daily_assets():
    date = request.args.get('date')  # Assume date format is YYYY-MM-DD
    if not date:
        return "Please specify the date parameter in the format YYYY-MM-DD", 400

    filepath = os.path.join(pdir, f'stats/{date}.csv')
    if not os.path.exists(filepath):
        return f"CSV file for the requested date {date} does not exist.", 404

    df = pd.read_csv(filepath)
    if df.empty:
        return f"No data available for {date}.", 404

    real_df = df[df['trading_env'] == 'REAL']
    sim_df = df[df['trading_env'] == 'SIMULATE']

    real_hk = real_df[real_df['market'] == 'HK']
    real_us = real_df[real_df['market'] == 'US']
    real_hkcc = real_df[real_df['market'] == 'HKCC']

    sim_hk = sim_df[sim_df['market'] == 'HK']
    sim_us = sim_df[sim_df['market'] == 'US']
    sim_cn = sim_df[sim_df['market'] == 'CN']

    response_data = {
        'date': date,
        'real_hk_assets': real_hk['total_assets'].values[0],
        'real_us_assets': real_us['total_assets'].values[0],
        'real_hkcc_assets': real_hkcc['total_assets'].values[0],
        'sim_hk_assets': sim_hk['total_assets'].values[0],
        'sim_us_assets': sim_us['total_assets'].values[0],
        'sim_cn_assets': sim_cn['total_assets'].values[0]
    }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)

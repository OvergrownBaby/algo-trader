from flask import Flask, request, jsonify
import os
import pandas as pd

dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

@app.route('/get_csv', methods=['GET'])
def get_csv():
    date = request.args.get('date')  # Assume date format is YYYY-MM-DD
    filepath = os.path.join(dir, f'status/{date}.csv')

    
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        return df.to_html()  # Or jsonify(df.to_dict()) for JSON format
    else:
        return "CSV file for the requested date does not exist.", 404

if __name__ == '__main__':
    app.run()

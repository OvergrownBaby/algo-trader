import os
import pandas as pd

dir = os.path.dirname(os.path.abspath(__file__))
status_dir = os.path.join(dir, 'status')

for file in os.listdir(status_dir):
    # Construct the full path to the entry
    print(file)
    # if os.path.isfile(entry_path):
    #     print(entry_path)


# html_table = df.to_html()

# Optionally, write the HTML table to a file
# with open('path/to/your/table.html', 'w') as f:
#     f.write(html_table)

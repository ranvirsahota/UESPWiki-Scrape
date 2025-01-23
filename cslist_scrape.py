import requests, sys, bs4, io, traceback,numpy
import pandas as pd
import re
books = pd.DataFrame()


offset = 0
while True:
    url = f"https://cslist.uesp.net/index.php?game=mw&rec=BOOK&offset={offset}&format=csv"
    print(offset)
    data = pd.read_csv(url)
    if (data.size == 0):
        break
    books = pd.concat([books, data], ignore_index=True)
    offset = offset + 100
print("URL GATHERED")

try:
    count = 0
    columns = ["TEXT", "Model", "Icon"]
    books_details = pd.DataFrame(columns=columns)
    for book in books["edID"]:
        count += 1
        values = [None] * len(columns)
        print (count/len(books) * 100, " ccomplete",end = '\r')
        url = f"https://cslist.uesp.net/index.php?game=mw&edid={book.replace(' ', '+')}&rectype=BOOK"
        data = pd.read_html(url,flavor="bs4")[1]
        for column_idx in range(len(columns)):
            for index in range(len(data)):
                if data.at[index, "Parameter"] == columns[column_idx]:
                    values[column_idx] = data.at[index,"Value"]
                    break
                

        values_reshape = numpy.reshape(values, shape=(1, -1))
        book_detail = pd.DataFrame(data=values_reshape, columns=columns)
        books_details = pd.concat([books_details, book_detail], ignore_index=True)    
    
        # last_index = data.last_valid_index()
        # data = data.at[last_index, "Value"]
        # if data == pd.DataFrame.empty:
        #     print(url, f"No Text found: {data}")
        #     break
        # books_content.append(data)


        # data = data.replace("<BR>", "\n")
        # match = re.search("<DIV ALIGN=\"CENTER\">",data)
        # match = re.search(r"by( \w*)*<BR>", data)
        
except (IndexError, KeyError) as error:
    print("Error:", url)
    print(error)
    print(traceback.format_exc())

books = pd.concat([books, books_details], axis=1)
books.to_csv("morr_fixed_cslist.csv")
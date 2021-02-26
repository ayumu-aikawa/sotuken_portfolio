import mysql.connector as mydb
import json
import os

#DBの設定
conn = mydb.connect(
  database = 'sotu_test',
  user='root',
  password = 'P@ssw0rd',
  host = 'localhost',
  port = '3306',
)

# コネクションが切れた時に再接続してくれるよう設定
#conn.ping(reconnect=True)

# 接続できているかどうか確認
print(conn.is_connected())


#書籍データのみが入ったdirectoryの中身を取得
directory = "./isbn_data/book_data2"
book_dir = os.listdir(directory)
# DB操作用にカーソルを作成
cur = conn.cursor(buffered=True)
#1つずつ取り出して実行 len(book_dir)
for i in range(1,len(book_dir) + 1):
  # DB操作用にカーソルを作成

  cur.execute("INSERT INTO `sotuken_lendmanage` (`smallcat_id`, `lendflag`, `returndate`, `accountid`) VALUES (%(smallcat)s, '0', '1970-01-01', '0');", {"smallcat":i})

cur.close()
conn.commit()
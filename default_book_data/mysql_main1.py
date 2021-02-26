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
#1つずつ取り出して実行 len(book_dir)
cur = conn.cursor(buffered=True)
for i in range(len(book_dir)):
  # DB操作用にカーソルを作成

  isbn_data = json.load(open(directory +'/'+ book_dir[i],'r',encoding='utf-8'))
  if isbn_data["ページ数"] == '':
      page = None
  else:
      page = isbn_data["ページ数"]
  print(isbn_data["小分類"])
  cur.execute("INSERT INTO `sotuken_bookinfo` (`isbn13`, `bigcat`, `midcat`, `smallcat`, `title`, `title_long`, `authors`, `publisher`, `exp`, `lang`, `page`, `publisheddate`, `label`, `price`, `piclink`,`deleteflag`) VALUES (%(isbn13)s, %(bigcat)s, %(midcat)s, %(smallcat)s, %(title)s, %(title_long)s, %(authors)s, %(publisher)s, %(exp)s,  %(lang)s, %(page)s, %(publisheddate)s, %(label)s, %(price)s, %(piclink)s,'0');", {'isbn13' : isbn_data["ISBN"],'bigcat' : isbn_data["大分類"],'midcat' : isbn_data["中分類"],'smallcat' : isbn_data["小分類"], 'title' : isbn_data["タイトル"],'title_long' :isbn_data["タイトル"] +" " + isbn_data["サブタイトル"],'authors':isbn_data["著者"],'publisher':isbn_data["出版社"],'exp':isbn_data["説明"],'lang':isbn_data["言語"],'page':page,'publisheddate':isbn_data["発売日"],'label':isbn_data["レーベル"],'price':isbn_data["値段"],'piclink':isbn_data["画像URL"]})

cur.close()
conn.commit()

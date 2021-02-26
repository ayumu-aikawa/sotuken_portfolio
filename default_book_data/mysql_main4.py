import mysql.connector as mydb
import json

#DBの設定
conn = mydb.connect(
  database = 'sotu_test',
  user='root',
  password = 'P@ssw0rd',
  host = 'localhost',
  port = '3306',
)


# 接続できているかどうか確認
print(conn.is_connected())

cur = conn.cursor(buffered=True)
#中分類
cat_data = json.load(open('./isbn_data/category_data/category_list.json','r',encoding='utf-8'))
for i in range(len(cat_data)):
  cur.execute("INSERT INTO `sotuken_midcategory` (`id`, `midcat`, `catname`, `bigcat_id`) VALUES (NULL, %(midcat)s,%(catname)s ,%(bigcat_id)s );",{'midcat':cat_data[i]["中分類番号"],'catname':cat_data[i]["中分類名"],'bigcat_id':cat_data[i]["大分類番号"]})

cur.close()
conn.commit()
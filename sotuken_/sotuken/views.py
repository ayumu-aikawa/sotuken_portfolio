import string, random, secrets, smtplib, datetime, pytz, re, json, requests
import mysql.connector as mydb
from .forms import CameraForm, ReturnsForm, LoginForm, SignUpForm, PasswordResetForm
from .models import Multi, Bookinfo, Lendmanage, BigCategory, MidCategory, User, UserManager, Lendhistory
from django.views import generic
from django.views.generic import View
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db.utils import InternalError   ###エラーハンドリング
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import make_password
from email.mime.text import MIMEText
from datetime import  date, time

#環境変数
Lending_period = 6 #貸出期間
header_name_len = 7 #ページ上部のヘッダーの１行に表示しきれる名前の長さ

#データベース情報
database = getattr(settings,"DATABASES",None)

#管理者のメールアドレス
AdminEmail = [
  ,
]

###################このアプリケーションのURL※必要に応じて変更する事！##################
URL_default = "https://www.bookon.tokyo"



#メール送信関数
def mail_send(to_email,subject,message):
  # SMTP認証情報
  account = "aaa@aaa.com"#メールアドレス
  password = "password"#パスワード

  from_email = "BOOK ON  メール送信システム<" + account + ">"
  
  # MIMEの作成
  msg = MIMEText(message, "html")
  msg["Subject"] = subject
  msg["To"] = to_email
  msg["From"] = from_email
  
  # メール送信処理
  server = smtplib.SMTP("smtp.gmail.com", 587)
  server.starttls()
  server.login(account, password)
  server.send_message(msg)
  server.quit()




@login_required(login_url="/login/")
def profile(request):
  userid = request.user.id
  userdata = User.objects.get(id = userid)

  params = {
    'title' : "プロフィール",
    'userdata': userdata,
  }

  return render(request, 'sotuken/profile.html', params)

  # book model
@login_required(login_url="/login/")
def book(request):

  if request.user.password == request.user.first_password:
    return redirect('password_change')
  elif request.user.first_password != None and request.user.password != request.user.first_password:
    userobj = User.objects.get(id = request.user.id)
    userobj.first_password = None
    userobj.save()

  params = {
      'title':'図書システム',
      'camera':'貸出',
      'returns':'返却',
      'search':'検索',
      'manage':'管理',
  }

  return render(request, 'sotuken/book.html', params)

  # camera_check model
@login_required(login_url="/login/")
def camera_check(request):
    params = {
        'title': 'カメラ確認画面',
        'msg': '※本の裏にある\nバーコードを読み取ってください',
        'form': CameraForm(),
        'goto': 'OK',
    }
    params['form'] = CameraForm(request.POST)
    return render(request, 'sotuken/camera_check.html', params)

  # camera model
@login_required(login_url="/login/")
def camera(request):
    params = {
        'title': 'カメラ画面',
        'goto': '貸出',
    }
    return render(request, 'sotuken/camera.html', params)

  #lend_check model
@login_required(login_url="/login/")
def lend_check(request):
    id_num = request.POST.get('scanned-QR')
    if Bookinfo.objects.filter(isbn13=id_num,deleteflag = 0).exists():
      book_data = Bookinfo.objects.filter(isbn13=id_num)
      dataLast = len(book_data) - 1
    else :
      messages.error(request, '一致する書籍が見つかりませんでした')
      #messages.warning(request, '入力欄にISBNコードを手入力してください')

      return redirect('/sotuken/camera') #get params

    returndate = datetime.datetime.now().date()+ datetime.timedelta(days=Lending_period)

    params = {
        'title': '貸出確認画面',
        'msg1':'背表紙の番号を入力してください',
        'msg2':'エラーが発生しました',
        'yes': 'はい',
        'no': '戻る',
        'isbn13':book_data[dataLast].isbn13,
        'b_title' :book_data[dataLast].title_long,
        'authors' :book_data[dataLast].authors,
        'publisher' :book_data[dataLast].publisher,
        'returnyear' :returndate.year,
        'returnmonth' :returndate.month,
        'returnday' :returndate.day,
        'hitnum':len(book_data),
        'lend_success' : 0,
    }

    params['msg2'] = 'この本は現在貸出中です'
    for i in range(len(book_data)):
      lend_data = Lendmanage.objects.get(smallcat_id = book_data[i].smallcat)
      if (lend_data.lendflag == 0):
        params['lend_success'] = 1
        params['msg2'] = 'この本で間違いないですか？'
        

    #params['form'] = MultiForm(request.POST)
    return render(request, 'sotuken/isbn_load.html', params)

  #lend_comp model
@login_required(login_url="/login/")
def lend_comp(request):
    userid = request.user.id

    num_s = request.POST.get('input_num')
    isbn = request.POST.get('isbn')

    if Bookinfo.objects.filter(isbn13=isbn,deleteflag = 0).exists():
      book_data = Bookinfo.objects.filter(isbn13=isbn)
      if None != num_s:
        for i in range(len(book_data)):
          if int(book_data[i].smallcat) == int(num_s):
            break
          if i >= (len(book_data) - 1):
            messages.error(request, '背表紙の番号が一致していません')
            return redirect('/sotuken/camera')
    else:
      messages.error(request, '想定外のエラーです')

      return redirect('/sotuken/camera')

    returndate = datetime.datetime.now().date()+ datetime.timedelta(days=Lending_period)


    params = {
        'title': '貸出完了画面',
        'msg1': '貸出を完了しました',
        'msg2': '貸出に失敗しました',
        'error': '予期していないエラーが発生しました',
        'msg3': '本の貸出を続けますか？',
        'goto': 'camera_check',
        'end': 'book',
        'returnyear' :returndate.year,
        'returnmonth' :returndate.month,
        'returnday' :returndate.day,
        'lend_success' : 0,
    }

    if None == num_s:
      book_data2 = Bookinfo.objects.get(isbn13 = isbn,deleteflag = 0)
      num_s = book_data2.smallcat
      
    lend_data = Lendmanage.objects.get(smallcat_id = num_s)
    if lend_data.lendflag == 1:
      params['error'] = 'この本は現在貸出中です'
    elif lend_data.lendflag == 0:
      lend_data.lendflag = 1
      lend_data.returndate = returndate
      lend_data.accountid = request.user.id
      lend_data.save()
      Lendhistory.objects.create(accountid = userid,opeaccountid = userid,smallcat = num_s,lenddate = datetime.datetime.now(),lendtype = 0)
      params['lend_success'] = 1

    return render(request, 'sotuken/lend_comp.html', params)

  #返却画面 貸出中のリストをfilterで取得する
@login_required(login_url="/login/")
def returns(request):
    info_data = []
    book_data = []
    userid = request.user.id
    lend_data = Lendmanage.objects.filter(lendflag = 1,accountid = userid)
    for i in range (len(lend_data)):
      info_data.append(Bookinfo.objects.get(smallcat = lend_data[i].smallcat_id))

    for d in info_data:
      dic = {'smallcat':d.smallcat,'title':(d.title_long),'authors':d.authors}
      l = Lendmanage.objects.get(smallcat_id = d.smallcat)
      dic.update({'returndate':l.returndate})
      book_data.append(dic)


    params = {
        'title': '返却画面',
        'msg': '返却したい書籍を選択してください',
        'form': ReturnsForm(),
        'book_data': book_data,
        'goto': '返却',
        'back': '戻る',
        'data_num': len(book_data),
    }

    return render(request, 'sotuken/returns.html', params)

  #返却確認画面 POSTされたデータを横流ししているだけ
@login_required(login_url="/login/")
def returns_check(request):
    book_data = []
    return_num = request.POST.getlist('num_s')

    if 0 == len(return_num):
      messages.error(request, '書籍を選択してください')

      return redirect('/sotuken/returns')

    for i in range(len(return_num)):
      book_data.append(Bookinfo.objects.get(smallcat = return_num[i]))

    params = {
        'title': '返却確認画面',
        'msg1': '以下の本を選択しました',
        'msg2': 'この本を返却しますか？',
        'book_data': book_data,
        'form': ReturnsForm(),
        'goto': 'はい',
        'back': '戻る',
    }

    if 1 < len(return_num):
      params['msg2']="選択した本を返却しますか？"

    return render(request, 'sotuken/returns_check.html', params)

  #returns_comp model
@login_required(login_url="/login/")
def returns_comp(request):
    userid = request.user.id
    book_data = []
    return_num = request.POST.getlist('num_s')

    params = {
        'title': '返却完了画面',
        'msg1': '返却が完了しました',
        'msg2': '返却に失敗しました',
        'msg3': '今後の運営のためにレビュー、アンケートのご協力をお願いします',
        'error': '以下の本の返却に失敗しました。',
        'book_data' :book_data,
        'que': 'アンケート',
        'rev': 'レビュー',
        'back': '戻る',
        'return_success': 0,
        'return_error' : 0,
    }

    for i in range(len(return_num)):
      lend_data = Lendmanage.objects.get(smallcat_id = return_num[i])
      if lend_data.lendflag == 0:
        book_data.append(Bookinfo.objects.get(smallcat = return_num[i]))
        params['return_error'] = 1
      elif lend_data.lendflag == 1:
        lend_data.lendflag = 0
        lend_data.save()
        Lendhistory.objects.create(accountid = userid,opeaccountid = userid,smallcat = return_num[i],lenddate = datetime.datetime.now(),lendtype = 1)
        params['return_success'] = 1

    params['book_data'] = book_data


    return render(request, 'sotuken/returns_comp.html', params)

#検索
@login_required(login_url="/login/")
def search(request):
  book_data=[]
  page_list = []
  msg1 = ""
  num = 0
  search_flag = 0


  #検索用システム
  if 'style' in request.GET:
    data = Bookinfo.objects.filter(deleteflag = 0)
    search_flag = 1
    if 'simple' == request.GET['style']:
      #キーワード検索
      keyword = request.GET['keyword']
      keyword_list = re.split('[ 　]',keyword)
      for t in range(len(keyword_list)):
        keyword = keyword_list[t]
        #大分類と中分類未対応の為要検討
        data = data.filter( Q(title_long__icontains = keyword) | Q(authors__icontains = keyword) | Q(publisher__icontains = keyword | Q(label__icontains = keyword) | Q(exp__icontains = keyword)))
      #必要性がわからなくなったので没
    elif 'detail' == request.GET['style']:
      #詳細検索
      #書籍名（タイトル、サブタイトル）
      if 'b_title' in request.GET:
        b_title = request.GET['b_title']
        '''if b_title == "":
          messages.error(request, '本のタイトルを入力してください')
          return redirect('/sotuken/search')'''
        if b_title != "":
          b_title_list = re.split('[ 　]',b_title)
          for t in range(len(b_title_list)):
            title = b_title_list[t]
            data = data.filter(title_long__icontains = title)
          #search_flag = 1
          msg1 += ("タイトル:" + b_title + " ")
      else :
        b_title = ""

      #著者
      if 'authors' in request.GET:
        authors = request.GET['authors']
        if authors != "":
          authors_list = re.split('[ 　]',authors)
          for t in range(len(authors_list)):
            authors = authors_list[t]
            data = data.filter(authors__icontains = authors)
          #search_flag = 1
          msg1 += ("著者:" + authors + " ")
      else :
        authors = ""

      #出版社
      if 'publisher' in request.GET:
        publisher = request.GET['publisher']
        if publisher != "":
          publisher_list = re.split('[ 　]',publisher)
          for t in range(len(publisher_list)):
            publisher = publisher_list[t]
            data = data.filter(publisher__icontains = publisher)
          #search_flag = 1
          msg1 += ("出版社:" + publisher + " ")
      else :
        publisher = ""
        
      #レーベル
      if 'label' in request.GET:
        label = request.GET['label']
        if label != "":
          label_list = re.split('[ 　]',label)
          for t in range(len(label_list)):
            label = label_list[t]
            data = data.filter(label__icontains = label)
          #search_flag = 1
          msg1 += ("レーベル:" + label + " ")
      else :
        label = ""

      #説明
      if 'exp' in request.GET:
        exp = request.GET['exp']
        if exp != "":
          exp_list = re.split('[ 　]',exp)
          for t in range(len(exp_list)):
            exp = exp_list[t]
            data = data.filter(exp__icontains = exp)
          #search_flag = 1
          msg1 += ("説明:" + exp + " ")
      else :
        label = ""

      #大分類
      if 'bigcat' in request.GET:
        bigcat = request.GET['bigcat']
        if bigcat != "":
          data = data.filter(bigcat__icontains = bigcat)
          #search_flag = 1
          b = BigCategory.objects.get(bigcat = bigcat)
          msg1 += ("大分類:" + bigcat + " " + b.catname + " ")
      else :
        bigcat = ""
      
      #中分類
      if 'midcat' in request.GET:
        midcat = request.GET['midcat']
        if midcat != "":
          data = data.filter(midcat__icontains = midcat)
          #search_flag = 1
          m = MidCategory.objects.filter(bigcat_id = bigcat,midcat = midcat)
          msg1 += ("中分類:" + midcat + " ")
          for m_name in m:
            msg1 += (m_name.catname + " ")
      else :
        midcat = ""
    
    #リスト化して扱いやすくする
    for i in data:
      book_data.append(i)
    #0件時のエラー
    if 0 == len(book_data) and 1 == search_flag:
      messages.error(request, '一致する本が見つかりませんでした')


  #検索結果の表示件数表示とか
  if 'page' in request.GET:
    page_num = int(request.GET['page'])
  else :
    page_num = 1

  #ページ遷移用のリストを作成
  pageval = (len(book_data) // 20) + 1
  if page_num < 4:
    page_list = []
    for i in range(5):
      value = i + 1
      if value > pageval:
        break
      page_list.append(value)
  elif page_num > pageval - 2:
    page_list = []
    for i in range(5):
      value = pageval + i - 4
      if value < 1:
        continue
      page_list.append(value)

  else:
    for n in range(1,pageval+1):
      page_list.append(n)
    page_list = page_list[page_num-3:page_num+2]

  #表示件数のパラメータ設定
  first_num = 1 + (page_num - 1) * 20
  if first_num > len(book_data):
    first_num = len(book_data)
  last_num = page_num * 20
  if last_num > len(book_data):
    last_num = len(book_data)

  num = len(book_data)
  book_data = book_data[(first_num-1):(last_num)]

  #if文の中用のパラメータ送信
  bigcat_p = -1
  if 'bigcat' in request.GET:
    try:
      bigcat_p = int(request.GET['bigcat'])
    except:
      pass
  midcat_p = -1
  if 'midcat' in request.GET:
    try:
      midcat_p = int(request.GET['midcat'])
    except:
      pass

  #大分類選択用データ取得
  bigcat_data = BigCategory.objects.all()

  #中分類選択用のデータ作成
  midcat_data = MidCategory.objects.all()
  midcat_dic = {item.bigcat :[] for item in bigcat_data}
  for d in bigcat_data:
    dataM = midcat_data.filter(bigcat_id = d.bigcat)
    dataM = dataM.order_by('midcat')
    for m in dataM:
      selected = 0
      if m.bigcat_id == bigcat_p and m.midcat == midcat_p:
        selected = 1
      midcat_dic[d.bigcat].append({"name":m.catname,"num":m.midcat,"selected":selected})
  json_list = json.dumps(midcat_dic,ensure_ascii=False)


  params = {
    'title' : '検索',
    'bigcat_data':bigcat_data,
    'midcat_data':midcat_data,
    'midcat_dic':json_list,
    'msg1': msg1,
    'num' : num,
    'yes' : '詳細検索',
    'book_data' :book_data,
    'first_num' :first_num,
    'last_num' : last_num,
    'page_num':page_num,
    'page_list':page_list,
    'page_first':'',
    'page_last':'',
    'no' : '戻る',
    'search_flag':search_flag,
    'bigcat_p':bigcat_p,
    'midcat_p':midcat_p,
  }

  if page_list[0] != 1:
    params['page_first'] = 1
  if page_list[len(page_list) - 1] != pageval:
    params['page_last'] = pageval
    
  return render(request, 'sotuken/search.html', params)

#書籍詳細画面
@login_required(login_url="/login/")
def details(request,num):
  msg1 = "エラー"
  midcatList = []
  exp_flag= 0 
  book_data = Bookinfo.objects.get(smallcat = num)
  lend_data = Lendmanage.objects.get(smallcat_id = num)
  bigcat = BigCategory.objects.get(bigcat = book_data.bigcat)
  midcat = MidCategory.objects.filter(midcat = book_data.midcat,bigcat_id = bigcat.bigcat)
  for obj in midcat:
    midcatList.append(obj.catname)

  
  if lend_data.lendflag == 1:
    msg1 = "貸出中"
  elif lend_data.lendflag == 0:
    msg1 = "貸出可能"

  if 99 < len(book_data.exp):
    exp_flag = 1


  params = {
    'title':"書籍詳細画面",
    'msg1' : msg1,
    'book_data':book_data,
    'lend_data':lend_data,
    'bigcat':bigcat.catname,
    'midcat_list':midcatList,
    'exp_flag':exp_flag,
    'goto': "貸出",
    'back': "戻る",
  }


  return render(request,'sotuken/details.html',params)

#管理画面トップ
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage(request):

  params = {
    'title':"管理画面トップ",
    'manage_user':"ユーザー情報",
    'manage_book':"書籍情報",
    'manage_lend':"貸出情報",
    'back':"戻る",
  }

  return render(request,'sotuken/manage.html',params)

#書籍管理画面トップ
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_booktable(request):

  params = {
    'title':"書籍管理画面トップ",
    'bookdata':"書籍情報",
    'bigcat':"大分類情報",
    'midcat':"中分類情報",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_booktable.html',params)

#貸出管理画面トップ
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_lendtable(request):

  params = {
    'title':"貸出管理画面トップ",
    'lendmanage':"貸出情報",
    'lendhistory':"貸出履歴情報",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_lendtable.html',params)

#ユーザー管理画面
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_user(request):

  user_data = User.objects.all()

  params = {
    'title':"ユーザー情報",
    'useradd':"ユーザー追加",
    'edit':"編集",
    'back':"戻る",
    'user_data':user_data,
  }

  return render(request,'sotuken/manage_user.html',params)

#ユーザー追加画面
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_user_add(request):
  if request.method == 'POST':
    form = SignUpForm(request.POST)
    if form.is_valid():
      form.save(request)
      usermail = request.POST.get('email')
      password = User.objects.make_random_password()
      aaa = make_password(password)
      obj = User.objects.get(email=usermail)
      #学籍番号処理
      if request.POST['userID'] == '':
        obj.userID = obj.id
        userid = obj.userID
        obj.save()
      else :
        userid = request.POST['userID']
      #名前(短)処理
      if len(obj.name) > header_name_len:
        objstr = obj.name
        objstr = objstr[:6]
        obj.shortname = objstr + "…"
      else:
        obj.shortname = obj.name
      obj.username = obj.id
      obj.password = aaa
      obj.first_password = aaa
      obj.save()
      try :
        URL = URL_default + "/login/"
        subject = "BOOK ON  利用可能のご案内"
        message = "あなたは管理者によってTIC図書システム「BOOK ON」の登録がされました。 以下のURLからログインし、利用を開始してください。<br><br>学籍番号 : " + str(userid) + "<br>パスワード : " + password + "<br><br>URL : " + URL
        mail_send(usermail,subject,message)
        msg1 = 'アカウントの登録及びメールの送信に成功しました。ログイン情報に関しましてはメールをご確認ください。'
      except:
        msg1 = 'アカウントの登録には成功しましたが、メールの送信に失敗しました。編集ページから送信可能なメールアドレスを再度入力し、登録メール再送信ボタンを押してください。'

      params = {
        'title':"ユーザー登録完了メール送信完了",
        'msg1':msg1,
        'back':"戻る",
        'yes':"完了",
      }

      return render(request,'sotuken/manage_user_edit_comp.html',params)
  else:
    form = SignUpForm()
  return render(request, 'sotuken/manage_user_add.html', {'form': form})


#ユーザー管理編集画面
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_user_edit(request,id):

  userdata = User.objects.get(id = id)
  

  params = {
    'title':"ユーザー情報編集",
    'back':"戻る",
    'yes':"完了",
    'p_delete':'削除',
    'userdata':userdata,
  }

  return render(request,'sotuken/manage_user_edit.html',params)

#ユーザー管理編集完了画面
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_user_edit_comp(request):

  msg1 = ""

  mID = request.POST.get('mID')
  newuserid = request.POST.get('userid')
  newname = request.POST.get('name')
  newemail = request.POST.get('email')
  superflag = request.POST.get('superflag')
  if superflag is None:
    superflag = 0
  activeflag = request.POST.get('activeflag')
  if activeflag is None:
    activeflag = 0
  adminflag = request.POST.get('adminflag')
  if adminflag is None:
    adminflag = 0
  userdata = User.objects.get(id = mID)
  try:
    userdata.userID = newuserid
    userdata.email = newemail
    userdata.is_superuser = superflag
    userdata.is_active = activeflag
    userdata.is_staff = adminflag
    userdata.name = newname
    #名前(短)処理
    if len(userdata.name) > header_name_len:
      objstr = userdata.name
      objstr = objstr[:6]
      userdata.shortname = objstr + "…"
    else:
      userdata.shortname = userdata.name
    userdata.save()
    msg1 = "内容を更新しました。"
  except:
    msg1 = "内容の更新に失敗しました。再度お試しください。"


  params = {
    'title':"ユーザー管理編集完了画面",
    'msg1':msg1,
    'back':"戻る",
    'yes':"完了",
    'userdata':userdata,
  }

  return render(request,'sotuken/manage_user_edit_comp.html',params)


#ユーザー削除画面
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_user_delete(request):

  mID = request.POST.get("mID")
  userdata = User.objects.get(id = mID)


  params = {
    'title':"ユーザー削除確認",
    'back':"戻る",
    'yes':"完了",
    'userdata':userdata,
  }

  return render(request,'sotuken/manage_user_delete.html',params)


#ユーザー削除完了画面
@login_required(login_url="/login/")
def manage_user_delete_comp(request):

  mID = request.POST.get("mID")
  User.objects.get(id = mID).delete()


  params = {
    'title':"ユーザー削除完了",
    'msg1':"削除が完了しました",
    'back':"戻る",
    'yes':"完了",
  }

  return render(request,'sotuken/manage_user_delete_comp.html',params)

#パスワード再送信
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_user_pass_re(request):

  mID = request.POST.get("mID")
  userdata = User.objects.get(id = mID)

  params = {
    'title':"パスワード再送信確認",
    'back':"戻る",
    'yes':"送信",
    'userdata':userdata,
  }

  return render(request,'sotuken/manage_user_pass_re.html',params)



#ユーザー削除完了画面
@login_required(login_url="/login/")
def manage_user_pass_send_comp(request):

  mID = request.POST.get('mID')
  userdata = User.objects.get(id = mID)
  usermail = userdata.email
  userid = userdata.userID
  password = User.objects.make_random_password()
  aaa = make_password(password)
  obj2 = User.objects.get(email=usermail)
  obj2.username = obj2.id
  obj2.password = aaa
  obj2.first_password = aaa
  obj2.save()
  try:
    URL = URL_default + "/login/"
    subject = "BOOK ON  利用可能のご案内"
    message = "あなたは管理者によってTIC図書システム「BOOK ON」のパスワードの再送信がおこなわれました。 パスワードを確認し、以下のURLからログインして利用を開始してください。<br><br>学籍番号 : "+ str(userid) +"<br>パスワード : " + password + "<br><br>URL : " + URL 
    mail_send(usermail,subject,message)
    msg1 = 'メールの送信に成功しました。メールをご確認ください。'
  except:
    msg1 = 'メールの送信に失敗しました。編集ページから送信可能なメールアドレスを再度入力し、再送信ボタンを押してください。'

  params = {
    'title':"パスワード再送信完了",
    'msg1':msg1,
    'back':"戻る",
    'yes':"完了",
  }

  return render(request,'sotuken/manage_user_pass_send_comp.html',params)


#書籍管理
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bookdata(request):

  book_data=[]
  page_list = []
  msg1 = ""
  num = 0
  search_flag = 0


  #検索用システム
  if 'style' in request.GET:
    data = Bookinfo.objects.all()
    search_flag = 1
    if 'detail' == request.GET['style']:
      #詳細検索
      #書籍名（タイトル、サブタイトル）
      if 'b_title' in request.GET:
        b_title = request.GET['b_title']
        '''if b_title == "":
          messages.error(request, '本のタイトルを入力してください')
          return redirect('/sotuken/search')'''
        if b_title != "":
          b_title_list = re.split('[ 　]',b_title)
          for t in range(len(b_title_list)):
            title = b_title_list[t]
            data = data.filter(title_long__icontains = title)
          msg1 += ("タイトル:" + b_title + " ")
      else :
        b_title = ""

      #著者
      if 'authors' in request.GET:
        authors = request.GET['authors']
        if authors != "":
          authors_list = re.split('[ 　]',authors)
          for t in range(len(authors_list)):
            authors = authors_list[t]
            data = data.filter(authors__icontains = authors)
          msg1 += ("著者:" + authors + " ")
      else :
        authors = ""

      #出版社
      if 'publisher' in request.GET:
        publisher = request.GET['publisher']
        if publisher != "":
          publisher_list = re.split('[ 　]',publisher)
          for t in range(len(publisher_list)):
            publisher = publisher_list[t]
            data = data.filter(publisher__icontains = publisher)
          msg1 += ("出版社:" + publisher + " ")
      else :
        publisher = ""

      #レーベル
      if 'label' in request.GET:
        label = request.GET['label']
        if label != "":
          label_list = re.split('[ 　]',label)
          for t in range(len(label_list)):
            label = label_list[t]
            data = data.filter(label__icontains = label)
          msg1 += ("レーベル:" + label + " ")
      else :
        label = ""

      #説明
      if 'exp' in request.GET:
        exp = request.GET['exp']
        if exp != "":
          exp_list = re.split('[ 　]',exp)
          for t in range(len(exp_list)):
            exp = exp_list[t]
            data = data.filter(exp__icontains = exp)
          msg1 += ("説明:" + exp + " ")
      else :
        label = ""

      #大分類
      if 'bigcat' in request.GET:
        bigcat = request.GET['bigcat']
        if bigcat != "":
          data = data.filter(bigcat__icontains = bigcat)
          b = BigCategory.objects.get(bigcat = bigcat)
          msg1 += ("大分類:" + bigcat + " " + b.catname + " ")
      else :
        bigcat = ""

      #中分類
      if 'midcat' in request.GET:
        midcat = request.GET['midcat']
        if midcat != "":
          data = data.filter(midcat__icontains = midcat)
          m = MidCategory.objects.filter(bigcat_id = bigcat,midcat = midcat)
          msg1 += ("中分類:" + midcat + " ")
          for m_name in m:
            msg1 += (m_name.catname + " ")
      else :
        midcat = ""

      #小分類
      if 'smallcat' in request.GET:
        smallcat = request.GET['smallcat']
        if smallcat != "":
          data = data.filter(smallcat = smallcat)
          msg1 += ("小分類:" + smallcat + " ")
      else :
        smallcat = ""

      #ISBN13
      if 'isbn13' in request.GET:
        isbn13 = request.GET['isbn13']
        if isbn13 != "":
          data = data.filter(isbn13__icontains = isbn13)
          msg1 += ("ISBN:" + isbn13 + " ")
      else :
        isbn13 = ""

      #削除フラグオプション
      if 'deleteOption' in request.GET:
        deleteOption = request.GET['deleteOption']
        if deleteOption != "0":
          if deleteOption == "1":
            data = data.filter(deleteflag = 0)
          elif deleteOption == "2":
            data = data.filter(deleteflag = 1)
      else :
        deleteOption = "0"


    #リスト化して扱いやすくする
    for i in data:
      book_data.append(i)
    #0件時のエラー
    if 0 == len(book_data) and 1 == search_flag:
      messages.error(request, '一致する本が見つかりませんでした')


  #検索結果の表示件数表示とか
  if 'page' in request.GET:
    page_num = int(request.GET['page'])
  else :
    page_num = 1

  #ページ遷移用のリストを作成
  pageval = (len(book_data) // 20) + 1
  if page_num < 4:
    page_list = []
    for i in range(5):
      value = i + 1
      if value > pageval:
        break
      page_list.append(value)
  elif page_num > pageval - 2:
    page_list = []
    for i in range(5):
      value = pageval + i - 4
      if value < 1:
        continue
      page_list.append(value)

  else:
    for n in range(1,pageval+1):
      page_list.append(n)
    page_list = page_list[page_num-3:page_num+2]

  #表示件数のパラメータ設定
  first_num = 1 + (page_num - 1) * 20
  if first_num > len(book_data):
    first_num = len(book_data)
  last_num = page_num * 20
  if last_num > len(book_data):
    last_num = len(book_data)

  num = len(book_data)
  book_data = book_data[(first_num-1):(last_num)]

  #if文の中用のパラメータ送信
  bigcat_p = -1
  if 'bigcat' in request.GET:
    try:
      bigcat_p = int(request.GET['bigcat'])
    except:
      pass
  midcat_p = -1
  if 'midcat' in request.GET:
    try:
      midcat_p = int(request.GET['midcat'])
    except:
      pass
  deleteOption_p = -1
  if 'deleteOption' in request.GET:
    try:
      deleteOption_p = int(request.GET['deleteOption'])
    except:
      pass

  #大分類選択用データ取得
  bigcat_data = BigCategory.objects.all()

  #中分類選択用のデータ作成
  midcat_data = MidCategory.objects.all()
  midcat_dic = {item.bigcat :[] for item in bigcat_data}
  for d in bigcat_data:
    dataM = midcat_data.filter(bigcat_id = d.bigcat)
    dataM = dataM.order_by('midcat')
    for m in dataM:
      selected = 0
      if m.bigcat_id == bigcat_p and m.midcat == midcat_p:
        selected = 1
      midcat_dic[d.bigcat].append({"name":m.catname,"num":m.midcat,"selected":selected})
  json_list = json.dumps(midcat_dic,ensure_ascii=False)


  params = {
    'title' : '書籍情報',
    'bookadd':'書籍追加',
    'bigcat_data':bigcat_data,
    'midcat_data':midcat_data,
    'midcat_dic':json_list,
    'msg1': msg1,
    'num' : num,
    'book_data' :book_data,
    'first_num' :first_num,
    'last_num' : last_num,
    'page_num':page_num,
    'page_list':page_list,
    'page_first':'',
    'page_last':'',
    'edit':'確認・編集',
    'delete':'削除',
    'back' : '戻る',
    'search_flag':search_flag,
    'bigcat_p':bigcat_p,
    'midcat_p':midcat_p,
    'deleteOption_p':deleteOption_p,
  }

  if page_list[0] != 1:
    params['page_first'] = 1
  if page_list[len(page_list) - 1] != pageval:
    params['page_last'] = pageval

  return render(request,'sotuken/manage_bookdata.html',params)

#書籍追加カメラ画面
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bookdata_add_camera(request):

  params = {
    'title':"書籍追加カメラ",
    'goto': '貸出',
  }

  return render(request,'sotuken/manage_bookdata_add_camera.html',params)

#書籍追加
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bookdata_add(request):
  isbn = request.POST.get('scanned-QR')
  title=''
  subtitle = ''
  label = ''
  isbn13=''
  authors=''
  ImprintName=''
  PublisherName=''
  publisher=''
  price=''
  publisheddate=''
  exp=''
  text04=''
  piclink=''
  page=''
  lang=''

  msg1 = '以下のデータベースからのデータを取得しています。'
  database_list = []
  #利用しているデータベースの情報追加
  database_list.append("Google Books API")
  url_GBA = 'https://www.googleapis.com/books/v1/volumes?q=isbn:'
  database_list.append("openBD")
  url_openBD = 'https://api.openbd.jp/v1/get?isbn='

  #Google Books APIのデータ取得
  GBA_json = requests.get(url_GBA + isbn).json()
  #openBDのデータ取得
  openBD_json = requests.get(url_openBD + isbn).json()

  #タイトル
  if title == '':
    try:
      title = openBD_json[0]['onix']['DescriptiveDetail']['TitleDetail']['TitleElement']['TitleText']['content']
    except:
      pass
  if title == '':
    try:
      title = GBA_json['items'][0]['volumeInfo']['title']
    except:
      pass
  #サブタイトル
  if subtitle == '':
    try:
      subtitle = openBD_json[0]['onix']['DescriptiveDetail']['TitleDetail']['TitleElement']['Subtitle']['content']
    except:
      pass
  if subtitle == '':
    try:
      subtitle = GBA_json['items'][0]['volumeInfo']['subtitle']
    except:
      pass
  #レーベル
  if label == '':
    try:
      label = openBD_json[0]['onix']['DescriptiveDetail']['Collection']['TitleDetail']['TitleElement'][0]['TitleText']['content']
    except:
      pass
  #ISBN13
  if isbn13 == '':
    try:
      isbn13 = openBD_json[0]['onix']['ProductIdentifier']['IDValue']
    except:
      pass
  if isbn13 == "":
    try:
      for i in range(len(GBA_json['items'][0]['volumeInfo']['industryIdentifiers'])):
        if 1 == ('ISBN_13' in GBA_json['items'][0]['volumeInfo']['industryIdentifiers'][i]['type']):
          isbn13 = GBA_json['items'][0]['volumeInfo']['industryIdentifiers'][i]['identifier']
    except:
      pass
  if isbn13 == "":
    isbn13 = isbn
  #著者
  if authors == '':
    try:
      authorsLen = len(openBD_json[0]['onix']['DescriptiveDetail']['Contributor'])
      if i >= 1:
        authors += ","
      authors += openBD_json[0]['onix']['DescriptiveDetail']['Contributor'][i]['PersonName']['content']
    except:
      pass
  if authors == '':
    try:
      for i in range(len(GBA_json['items'][0]['volumeInfo']['authors'])):
        if i >= 1:
          authors += ","
        authors += GBA_json['items'][0]['volumeInfo']['authors'][i]
    except:
      pass
  #出版社
  if publisher == '':
    try:
      ImprintName = openBD_json[0]['onix']['PublishingDetail']['Imprint']['ImprintName']
    except:
      pass
    try:
      PublisherName = openBD_json[0]['onix']['PublishingDetail']['Publisher']['PublisherName']
    except:
      pass
  if PublisherName != '':
    publisher = PublisherName
  elif ImprintName != '':
    publisher = ImprintName
  if publisher == '':
    try:
      publisher = GBA_json['items'][0]['volumeInfo']['publisher']
    except:
      pass
  #値段
  if price == '':
    try:
      price = openBD_json[0]['onix']['ProductSupply']['SupplyDetail']['Price'][0]['PriceAmount']
    except:
      pass
  if price == '':
    price = 0
  #発売日
  if publisheddate == '':
    try:
      publisheddate = openBD_json[0]['onix']['PublishingDetail']['PublishingDate'][0]['Date']
    except:
      pass
  #本の説明 "TextType": "04"は目次
  if exp == '':
    try:
      for i in range(len(openBD_json[0]['onix']['CollateralDetail']['TextContent'])):
        exp = openBD_json[0]['onix']['CollateralDetail']['TextContent'][i]['Text']
    except:
      pass
  if exp == '':
    try:
      exp = GBA_json['items'][0]['volumeInfo']['description']
    except:
      pass
  '''if '04' == openBD_json[0]['onix']['CollateralDetail']['TextContent'][i]['TextType']:
    text04 = openBD_json[0]['onix']['CollateralDetail']['TextContent'][i]['Text']'''
  #書籍画像URL
  if piclink == '':
    try:
      piclink = openBD_json[0]['onix']['CollateralDetail']['SupportingResource'][0]['ResourceVersion'][0]['ResourceLink']
    except:
      pass
  if piclink == '':
    try:
      piclink = GBA_json['items'][0]['volumeInfo']['imageLinks']['thumbnail']
    except:
      pass
  #ページ数
  if page == '':
    try:
      page = openBD_json[0]['onix']['DescriptiveDetail']['Extent'][0]['ExtentValue']
      if page == '0':
        page = ''
    except:
      pass
  if page == '':
    try:
      page = GBA_json['items'][0]['volumeInfo']["pageCount"]
    except:
      pass
  if page == '':
    page = 0
  #書籍の言語
  if lang == '':
    try:
      lang = openBD_json[0]['onix']['DescriptiveDetail']['Language'][0]['LanguageCode']
    except:
      pass
  if lang == '':
    try:
      lang = GBA_json['items'][0]['volumeInfo']["language"]
    except:
      pass

  #大分類選択用のデータ作成
  bigcat_list = []
  bigcat_data = BigCategory.objects.all()
  for i in bigcat_data:
    bigcat_list.append(i)
  midcat_list = []
  midcat_data = MidCategory.objects.all()
  for i in midcat_data:
    midcat_list.append(i)
  
  #中分類選択用のデータ作成
  midcat_data = MidCategory.objects.all()
  midcat_dic = {item.bigcat :[] for item in bigcat_data}
  for d in bigcat_data:
    dataM = midcat_data.filter(bigcat_id = d.bigcat)
    dataM = dataM.order_by('midcat')
    for m in dataM:
      midcat_dic[d.bigcat].append({"name":m.catname,"num":m.midcat,})
  json_list = json.dumps(midcat_dic,ensure_ascii=False)


  params = {
    'title_':"書籍情報追加",
    'msg1':msg1,
    'database_list':database_list,
    'isbn13': isbn13,
    'title': title,
    'subtitle': subtitle,
    'authors': authors,
    'publisher': publisher,
    'exp': exp,
    'lang': lang,
    'page': page,
    'publisheddate': publisheddate,
    'label': label,
    'price': price,
    'piclink': piclink,
    'bigcat_list':bigcat_list,
    'midcat_dic':json_list,
  }

  return render(request,'sotuken/manage_bookdata_add.html',params)

#書籍追加完了
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bookdata_add_comp(request):
  isbn13 = request.POST.get("isbn13")
  bigcat = request.POST.get("bigcat")
  midcat = request.POST.get("midcat")
  smallcat = request.POST.get("smallcat")
  title = request.POST.get("title")
  title_long = request.POST.get("title_long")
  authors = request.POST.get("authors")
  publisher = request.POST.get("publisher")
  exp = request.POST.get("exp")
  lang = request.POST.get("lang")
  page = request.POST.get("page")
  publisheddate = request.POST.get("publisheddate")
  label = request.POST.get("label")
  price = request.POST.get("price")
  piclink = request.POST.get("piclink")

  #小分類の有無で分岐
  #貸出管理のデータも作成
  try:
    if smallcat == '':
      conn = mydb.connect(
        database = database['default']['NAME'],
        user = database['default']['USER'],
        password = database['default']['PASSWORD'],
        host = database['default']['HOST'],
        port = database['default']['PORT'],
      )
      cur = conn.cursor(buffered=True)
      cur.execute("ALTER TABLE `sotuken_bookinfo` auto_increment = 1;")
      cur.close()
      conn.commit()
      newbook = Bookinfo.objects.create(isbn13 = isbn13,title = title,title_long = title_long,bigcat = bigcat,midcat = midcat,authors = authors,publisher = publisher,exp = exp,lang = lang,page = page,publisheddate = publisheddate,label = label,price = price,piclink = piclink)
    else:
      newbook = Bookinfo.objects.create(isbn13 = isbn13,title = title,title_long = title_long,bigcat = bigcat,midcat = midcat,smallcat = smallcat,authors = authors,publisher = publisher,exp = exp,lang = lang,page = page,publisheddate = publisheddate,label = label,price = price,piclink = piclink)
    msg1 = '書籍を登録しました。'
    try:
      Lendmanage.objects.create(smallcat_id = newbook.smallcat)
    except:
      msg1 = '書籍の登録には成功しましたが、貸出情報の作成に失敗しました。今回登録した書籍データを削除した上で再度お試しください。'
  except InternalError as d:
    msg1 = 'データベースのエラーにより書籍の登録に失敗しました。繰り返しこのエラーが表示される場合、管理者に連絡してください。'
  except:
    msg1 = '書籍の登録に失敗しました。内容をご確認の上再度お試しください。'


  params = {
    'title' : '書籍情報追加完了',
    'msg1':msg1,
    'back' : '戻る',
  }


  return render(request,'sotuken/manage_bookdata_add_comp.html',params)

#書籍編集
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bookdata_edit(request,id):

  bookobj = Bookinfo.objects.get(smallcat = id)
  #大分類選択用のデータ作成
  bigcat_list = []
  bigcat_data = BigCategory.objects.all()
  for i in bigcat_data:
    bigcat_list.append(i)
  '''midcat_list = []
  midcat_data = MidCategory.objects.all()
  for i in midcat_data:
    midcat_list.append(i)'''
  
  #中分類選択用のデータ作成
  midcat_data = MidCategory.objects.all()
  midcat_dic = {item.bigcat :[] for item in bigcat_data}
  for d in bigcat_data:
    dataM = midcat_data.filter(bigcat_id = d.bigcat)
    dataM = dataM.order_by('midcat')
    for m in dataM:
      selected = 0
      if m.bigcat_id == bookobj.bigcat and m.midcat == bookobj.midcat:
        selected = 1
      midcat_dic[d.bigcat].append({"name":m.catname,"num":m.midcat,"selected":selected})
  json_list = json.dumps(midcat_dic,ensure_ascii=False)

  params = {
    'title':"書籍情報編集",
    'p_delete':'削　除',
    'bookobj':bookobj,
    'bigcat_list':bigcat_list,
    'midcat_dic':json_list,
    'yes':"完了",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bookdata_edit.html',params)

#書籍編集完了
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bookdata_edit_comp(request):
  isbn13 = request.POST.get("isbn13")
  bigcat = request.POST.get("bigcat")
  midcat = request.POST.get("midcat")
  smallcat = request.POST.get("smallcat")
  title = request.POST.get("title")
  title_long = request.POST.get("title_long")
  authors = request.POST.get("authors")
  publisher = request.POST.get("publisher")
  exp = request.POST.get("exp")
  lang = request.POST.get("lang")
  page = request.POST.get("page")
  publisheddate = request.POST.get("publisheddate")
  label = request.POST.get("label")
  price = request.POST.get("price")
  piclink = request.POST.get("piclink")
  deleteflag = request.POST.get("deleteflag")
  if deleteflag is None:
    deleteflag = 0

  try:
    bookobj = Bookinfo.objects.get(smallcat = smallcat)
    bookobj.isbn13 = isbn13
    bookobj.bigcat = bigcat
    bookobj.midcat = midcat
    bookobj.title = title
    bookobj.title_long = title_long
    bookobj.authors = authors
    bookobj.publisher = publisher
    bookobj.exp = exp
    bookobj.lang = lang
    bookobj.page = page
    bookobj.publisheddate = publisheddate
    bookobj.label = label
    bookobj.price = price
    bookobj.piclink = piclink
    bookobj.deleteflag = deleteflag
    bookobj.save()
    msg1 = "内容を更新しました。"
  except:
    msg1 = "内容の更新に失敗しました。再度お試しください。"


  params = {
    'title':"書籍情報編集完了",
    'msg1':msg1,
    'yes':"完了",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bookdata_edit_comp.html',params)


#書籍削除
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bookdata_delete(request):
  smallcat = request.POST.get("smallcat")
  msg1 = ""

  bookobj = Bookinfo.objects.get(smallcat = smallcat)


  params = {
    'title':"書籍削除確認",
    'bookobj':bookobj,
    'id':id,
    'msg1':msg1,
    'yes':"削除する",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bookdata_delete.html',params)

#書籍削除完了
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bookdata_delete_comp(request):

  booknum = request.POST.get("booknum")
  Bookinfo.objects.get(smallcat = booknum).delete()
  #Lendmanage.objects.get(smallcat_id = booknum).delete()

  params = {
    'title':"書籍削除完了",
    'msg1':"削除を完了しました",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bookdata_delete_comp.html',params)

#大分類管理
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bigcat(request):
  bigcat_list = []
  bigcat_data = BigCategory.objects.all()
  #リスト化して扱いやすくする
  for i in bigcat_data:
    bigcat_list.append(i)

  params = {
    'title':"大分類情報",
    'bigcat_list':bigcat_list,
    'add':"追加",
    'edit':"編集",
    'delete':"削除",
    'back':'戻る',
  }

  return render(request,'sotuken/manage_bigcat.html',params)

#大分類追加
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bigcat_add(request):

  params = {
    'title':"大分類情報追加",
    'msg1':"番号は一意の数字である必要があります。",
  }

  return render(request,'sotuken/manage_bigcat_add.html',params)

#大分類追加完了画面
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bigcat_add_comp(request):
  msg1 = ""

  bignum = request.POST.get("num")
  bigname = request.POST.get("name")

  #bigcat_data = BigCategory.objects.all()
  try:
    BigCategory.objects.create(bigcat = bignum,catname = bigname)
    msg1 = "番号:" + bignum + " 名前:" + bigname + " を登録しました。"
  except:
    msg1 = "番号:" + bignum + " 名前:" + bigname + " の登録に失敗しました。\n内容をご確認の上再度お試しください。"

  params = {
    'title':"大分類情報追加完了",
    'msg1':msg1,
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bigcat_add_comp.html',params)

#大分類編集
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bigcat_edit(request,id):

  bigobj = BigCategory.objects.get(bigcat = id)

  params = {
    'title':"大分類情報編集",
    'bigobj':bigobj,
    'yes':"完了",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bigcat_edit.html',params)

#大分類編集完了
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bigcat_edit_comp(request):
  msg1 = ""

  bigcatid = request.POST.get("bigcatid")
  newname = request.POST.get("newname")
  try:
    bigobj = BigCategory.objects.get(bigcat = bigcatid)
    bigobj.catname = newname
    bigobj.save()
    msg1 = "内容を更新しました。"
  except:
    msg1 = "内容の更新に失敗しました。再度お試しください。"

  params = {
    'title':"大分類情報編集",
    'msg1':msg1,
    'yes':"完了",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bigcat_edit_comp.html',params)

#大分類削除確認
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bigcat_delete(request,id):
  msg1 = ""

  bigobj = BigCategory.objects.get(bigcat = id)

  if 0 < len(MidCategory.objects.filter(bigcat_id = id)):
    msg1 += "この大分類には、関連付けられた中分類が存在します。\n"
  
  if 0 < len(Bookinfo.objects.filter(bigcat = id)):
    msg1 += "この大分類には、関連付けられた図書が存在します。\n"
  

  params = {
    'title':"大分類情報削除確認",
    'bigobj':bigobj,
    'id':id,
    'msg1':msg1,
    'yes':"削除する",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bigcat_delete.html',params)

#大分類削除完了
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_bigcat_delete_comp(request):

  bigcatid = request.POST.get("bigcatid")
  BigCategory.objects.get(bigcat = bigcatid).delete()

  params = {
    'title':"大分類削除完了",
    'msg1':"削除を完了しました",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_bigcat_delete_comp.html',params)

#中分類管理
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_midcat(request):
  midcat_list = []
  bigcat_list = []
  msg1 = ''
  midcat_data = MidCategory.objects.all()
  bigcat_data = BigCategory.objects.all()
  
  if 'page' in request.GET:
    page = request.GET['page']
    midcat_data = midcat_data.filter(bigcat_id = page)
    msg1 = bigcat_data.get(bigcat = page).catname
  
  #リスト化して扱いやすくする
  for i in bigcat_data:
    bigcat_list.append(i)
  midcat_data = midcat_data.order_by('bigcat_id','midcat')
  for i in midcat_data:
    midcat_list.append(i)


  params = {
    'title': "中分類情報",
    'msg1': msg1,
    'midcat_list':midcat_list,
    'bigcat_list':bigcat_list,
    'add':"追加",
    'edit':"編集",
    'delete':"削除",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_midcat.html',params)

#中分類追加
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_midcat_add(request):
  bigcat_list = []
  bigcat_data = BigCategory.objects.all()
  for i in bigcat_data:
    bigcat_list.append(i)

  params = {
    'title':"中分類情報追加",
    'bigcat_list':bigcat_list,
  }

  return render(request,'sotuken/manage_midcat_add.html',params)

#中分類追加完了画面
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_midcat_add_comp(request):
  msg1 = ""

  bigcat = request.POST.get("bigcat")
  midnum = request.POST.get("num")
  midname = request.POST.get("name")

  try:
    MidCategory.objects.create(midcat = midnum,catname = midname,bigcat_id = bigcat)
    msg1 = "大分類:" + bigcat +" 番号:" + midnum + " 名前:" + midname + " を登録しました。"
  except:
    msg1 = "大分類:" + bigcat +" 番号:" + midnum + " 名前:" + midname + " の登録に失敗しました。\n内容をご確認の上再度お試しください。"

  params = {
    'title':"中分類情報追加完了",
    'msg1':msg1,
    'back':"戻る",
  }

  return render(request,'sotuken/manage_midcat_add_comp.html',params)

#中分類編集
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_midcat_edit(request,id):

  midobj = MidCategory.objects.get(id = id)
  bigcat_list = []
  bigcat_data = BigCategory.objects.all()
  for i in bigcat_data:
    bigcat_list.append(i)

  params = {
    'title':"中分類情報編集",
    'midobj':midobj,
    'bigcat_list':bigcat_list,
    'yes':"完了",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_midcat_edit.html',params)

#中分類編集完了
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_midcat_edit_comp(request):
  msg1 = ""

  midcatid = request.POST.get("midcatid")
  newbigcat = request.POST.get("newbigcat")
  newnum = request.POST.get("newnum")
  newname = request.POST.get("newname")
  try:
    midobj = MidCategory.objects.get(id = midcatid)
    midobj.bigcat_id = newbigcat
    midobj.midcat = newnum
    midobj.catname = newname
    midobj.save()
    msg1 = "内容を更新しました。"
  except:
    msg1 = "内容の更新に失敗しました。再度お試しください。"

  params = {
    'title':"中分類情報編集完了",
    'msg1':msg1,
    'yes':"完了",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_midcat_edit_comp.html',params)

#中分類削除確認
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_midcat_delete(request,id):

  midobj = MidCategory.objects.get(id = id)

  params = {
    'title':"中分類情報削除確認",
    'midobj':midobj,
    'id':id,
    'yes':"削除する",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_midcat_delete.html',params)

#中分類削除完了
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_midcat_delete_comp(request):

  midcatid = request.POST.get("midcatid")
  MidCategory.objects.get(id = midcatid).delete()

  params = {
    'title':"中分類情報削除完了",
    'msg1':"削除を完了しました",
    'back':"戻る",
  }

  return render(request,'sotuken/manage_midcat_delete_comp.html',params)


#貸出管理
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_lend(request):

  info_data = []
  book_data = []
  option_p = ''

  if 'option' in request.GET:
    option_p = int(request.GET['option'])

  if 0 == option_p or '' == option_p:
    lend_data = Lendmanage.objects.filter(lendflag = 1)
  elif 1 == option_p:
    lend_data = Lendmanage.objects.filter(lendflag = 0)
  elif 2 == option_p:
    lend_data = Lendmanage.objects.all()
  
  for i in range (len(lend_data)):
    info_data.append(Bookinfo.objects.get(smallcat = lend_data[i].smallcat_id))

  for d in info_data:
    dic = {'smallcat':d.smallcat,'title':(d.title_long),'authors':d.authors}
    l = Lendmanage.objects.get(smallcat_id = d.smallcat)
    dic.update({'lendflag':l.lendflag})
    try :
      u = User.objects.get(id = l.accountid)
      dic.update({'returndate':l.returndate,'accountid':u.userID})
    except :
      pass
    try:
      dic.update({'accountname': u.name})
    except: 
      pass
    book_data.append(dic)
    try :
      del u
    except :
      pass

  params = {
    'title': '貸出情報',
    'msg': '',
    'form': ReturnsForm(),
    'book_data': book_data,
    'option_p':option_p,
    'edit': '編集',
    'back': '戻る',
  }

  return render(request, 'sotuken/manage_lend.html', params)


#貸出編集
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_lend_edit(request,id):
  lendid = 0

  lenddata = Lendmanage.objects.get(smallcat_id = id)
  if True == User.objects.filter(id = lenddata.accountid).exists():
    lendid = User.objects.get(id = lenddata.accountid).userID
  else :
    lendid = -1

  #タイトルの用意
  b = Bookinfo.objects.get(smallcat = id)
  title_long = b.title_long

  params = {
    'title': '貸出情報編集',
    'msg1': '',
    'lenddata':lenddata,
    'lendid':lendid,
    'title_long':title_long,
    'yes': '完了',
    'back': '戻る',
  }

  return render(request, 'sotuken/manage_lend_edit.html', params)

#貸出編集完了
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_lend_edit_comp(request):

  smallcat = request.POST.get("smallcat")
  lendid = request.POST.get("lendid")
  r = request.POST.get("returndate")
  returndate = datetime.datetime.strptime(r, "%Y-%m-%d").date()
  lendflag = request.POST.get("lendflag")
  if lendflag is None:
    lendflag = 0
  lenddata = Lendmanage.objects.get(smallcat_id = smallcat)
  try:
    if True == User.objects.filter(userID = lendid).exists():
      accountid = User.objects.get(userID = lendid).id
    else :
      accountid = -1
    lenddata.accountid = accountid
    lenddata.returndate = returndate
    lenddata.lendflag = lendflag
    lenddata.save()
    msg1 = "貸出データを更新しました"
  except:
    msg1 = "貸出データの更新に失敗しました"

  params = {
    'title': '貸出情報編集完了',
    'msg1':msg1,
    'back':'戻る',
  }

  return render(request, 'sotuken/manage_lend_edit_comp.html', params)

#貸出履歴管理
@login_required(login_url="/login/")
@user_passes_test(lambda u: u.is_superuser)
def manage_lendhistory(request):
  lend_data = []
  page_list = []
  msg1 = ""
  num = 0
  search_flag = 0


  if request.GET:
    search_flag = 1
    l = Lendhistory.objects.all().order_by('-id')
    #絞り込み
    if 'option' in request.GET:
      option = request.GET['option']
      if option != "":
        if option == "1":
          l = l.filter(lendtype = 0)
        elif option == "2":
          l = l.filter(lendtype = 1)
    if 'accountid' in request.GET:
      accountid = request.GET['accountid']
      if accountid != "":
        iiii = -1
        if 1 == User.objects.filter(userID = accountid).count():
          userobj = User.objects.get(userID = accountid)
          iiii = userobj.id
        l = l.filter(accountid = iiii)
    if 'smallcat' in request.GET:
      smallcat = request.GET['smallcat']
      if smallcat != "":
        l = l.filter(smallcat = smallcat)
    if 'datestart' in request.GET:
      datestart = request.GET['datestart']
      if datestart != "":
        datestart = datetime.datetime.strptime(datestart, '%Y-%m-%d')
        l = l.filter(lenddate__gte=datestart)
    if 'dateend' in request.GET:
      dateend = request.GET['dateend']
      if dateend != "":
        dateend = datetime.datetime.strptime(dateend, '%Y-%m-%d')
        l = l.filter(lenddate__lte=dateend)

    #リスト化
    for i in l:
      if 1 == User.objects.filter(id = i.accountid).count():
        u = User.objects.get(id = i.accountid)
        u_name = u.name
        u_userID = u.userID
      else:
        u_name = "取得失敗"
        u_userID = i.accountid
      lend_data.append({"id":i.id,"smallcat":i.smallcat,"accountname":u_name,"accountid":u_userID,"lenddate":i.lenddate,"lendtype":i.lendtype})


  #検索結果の表示件数表示とか
  if 'page' in request.GET:
    page_num = int(request.GET['page'])
  else :
    page_num = 1

  #ページ遷移用のリストを作成
  pageval = (len(lend_data) // 200) + 1
  if page_num < 4:
    page_list = []
    for i in range(5):
      value = i + 1
      if value > pageval:
        break
      page_list.append(value)
  elif page_num > pageval - 2:
    page_list = []
    for i in range(5):
      value = pageval + i - 4
      if value < 1:
        continue
      page_list.append(value)
  else:
    for n in range(1,pageval+1):
      page_list.append(n)
    page_list = page_list[page_num-3:page_num+2]

  #表示件数のパラメータ設定
  first_num = 1 + (page_num - 1) * 200
  if first_num > len(lend_data):
    first_num = len(lend_data)
  last_num = page_num * 200
  if last_num > len(lend_data):
    last_num = len(lend_data)

  num = len(lend_data)
  lend_data = lend_data[(first_num-1):(last_num)]

  option_p = -1
  if 'option' in request.GET:
    try:
      option_p = int(request.GET['option'])
    except:
      pass

  params = {
    'title' : "貸出履歴情報",
    'lend_data': lend_data,
    'first_num' :first_num,
    'last_num' : last_num,
    'page_num':page_num,
    'page_list':page_list,
    'page_first':"",
    'page_last':"",
    'num':num,
    'search_flag':search_flag,
    'first_num':first_num,
    'last_num':last_num,
    'option_p':option_p,
    'back':'戻る',
  }

  if page_list[0] != 1:
    params['page_first'] = 1
  if page_list[len(page_list) - 1] != pageval:
    params['page_last'] = pageval

  return render(request,'sotuken/manage_lendhistory.html',params)

#お問い合せ
@login_required(login_url="/login/")
def contact(request):

  msg1 = "このページはサイトの製作者にアプリの要望や不具合等を報告できるページです。お気軽にご連絡ください。"

  params = {
    'title':"お問い合せページ",
    'msg1':msg1,
    'yes':"送信",
    'back':"戻る",
  }

  return render(request,'sotuken/contact.html',params)

#個人貸出履歴
@login_required(login_url="/login/")
def lendhistory(request):
  msg1 = ""
  userid = request.user.id
  lend_data = []
  lendhistory = Lendhistory.objects.filter(accountid = userid,lendtype = 0)
  for i in range(len(lendhistory)):
    l = lendhistory[i]
    try:
      booktitle = Bookinfo.objects.get(smallcat = l.smallcat).title
    except:
      booktitle = "削除されました"
    lend_data.append({"num":i + 1,"title": booktitle,"smallcat":l.smallcat,"date":l.lenddate,})
  lend_data.reverse()
  
  if False == lendhistory.exists():
    msg1 = "あなたはまだ書籍を貸出していません。"

  params = {
    'title':"あなたの貸出履歴",
    'msg1':msg1,
    'lend_data':lend_data,
  }

  return render(request,'sotuken/lendhistory.html',params)

@login_required(login_url="/login/")
def contact_comp(request):
  msg1 = ""
  msg2 = ""
  faild_list = []
  flag = False

  userid = request.user.id
  userobj = User.objects.get(id = userid)
  contents = request.POST.get('contents')
  contents = "送信者名: " + userobj.name + "<br><br>登録メールアドレス" + userobj.email + "<br><br>内容:<br>" + contents

  for a in AdminEmail:
    try:
      mail_send(a,"お問い合わせページからの自動送信メール",contents)
      flag = True
    except:
      faild_list.append(a)

  if flag == True:
    msg1 = "お問い合わせありがとうございます。送信しました。"

  if 0 < len(faild_list):
    msg2 = "全ての管理者にお問い合わせ内容を送信できていない可能性があります。管理者に連絡したい場合、以下のアドレスに個別にメールを送信してください。"

  params = {
    'title':"お問い合せページ",
    'msg1':msg1,
    'msg2':msg2,
    'faild_list':faild_list,
    'back' : "TOPに戻る",
  }

  return render(request,'sotuken/contact_comp.html',params)


class index(LoginRequiredMixin, generic.TemplateView):
  template_name = 'home.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs) # 継承元のメソッドCALL
    context["form_name"] = "home"
    return context

class PasswordChange(LoginRequiredMixin, PasswordChangeView):
  success_url = reverse_lazy('password_change_done')
  template_name = 'password_change.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs) # 継承元のメソッドCALL
    context["form_name"] = "password_change"
    return context

class PasswordChangeDone(LoginRequiredMixin,PasswordChangeDoneView):
  template_name = 'password_change_done.html'

def login_view(request):
  if request.method == 'POST':
    form = LoginForm(request.POST)
    if form.is_valid():
      IDorEmail = form.cleaned_data.get('username')
      password = form.cleaned_data.get('password')
      user = None
      try:
        if True == User.objects.filter(userID=IDorEmail).exists():
          username = User.objects.get(userID=IDorEmail).username
          user = authenticate(username=username,password=password)
      except:
        pass
      try:
        if True == User.objects.filter(email=IDorEmail).exists():
          username = User.objects.get(email=IDorEmail).username
          user = authenticate(username=username,password=password)
      except:
        pass
      if user is not None:
        if user.is_active:
          login(request, user)
          return redirect('home')
      else:
        messages.error(request, '学籍番号もしくはメールアドレス、及びパスワードが間違っています。')

        return redirect('/login')
  else:
    form = LoginForm()
  context = {
    'form': form,
  }
  return render(request, 'login.html', context)

#パスワード変更メール入力
def forgotPassword(request):
  params ={
    'title' : "パスワードリセット",
  }
  return render(request,'password_reset.html',)

#パスワード変更メール送信
def forgotPasswordSubmit(request):
  usermail = request.POST.get("mailaddress")

  if False == User.objects.filter(email = usermail).exists():
    messages.error(request, '登録されているアカウントが見つかりませんでした。')

    return redirect('/password_reset/')

  while True:
    newToken = secrets.token_urlsafe()
    if False == User.objects.filter(token = newToken).exists():
      break
  userobj = User.objects.get(email = usermail)
  userobj.token = newToken
  userobj.save()
  passwordURL = URL_default + "/reset/" + newToken

  subject = "図書システム パスワード変更のご案内"
  message = "ご利用の図書システムアカウントのパスワードをリセットするには、以下のURLからプロセスを完了してください。パスワードのリセットにお心当たりがない場合はこのメールを無視してください。 <br><br>" + passwordURL
  mail_send(usermail,subject,message)

  params = {
    'title' : "パスワードリセットメール送信",
    'msg1' : "パスワード再発行のURLをご案内したメールを送信しました。ご確認ください。",
  }
  return render(request,'password_reset_submit.html',params)

def forgotPassword2(request,token):

  if False == User.objects.filter(token = token).exists():
    redirect('home')

  if request.method != 'POST':
    ############################################ログインしてても飛べるようにする
    ############################################現状ログインしてるとバグったページが出る
    if str(request.user) != 'AnonymousUser':
      form = ''
    else:
      form = PasswordResetForm()
  else:
    form = PasswordResetForm(request.POST)
    if form.is_valid():
      newpass = request.POST.get("password")
      userobj = User.objects.get(token = token)
      userobj.set_password(newpass)
      userobj.token = None
      userobj.save()

      return redirect('home')
  
  params = {
    'form': form,
  }

  return render(request,'password_reset2.html',params)

# def random_pass(request):
#   print(string.ascii_letters)
#   print(string.digits)
#   print (''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)]))
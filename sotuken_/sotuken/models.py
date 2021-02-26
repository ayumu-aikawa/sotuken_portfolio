import re, uuid
from django.apps import apps
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, BaseUserManager

#class Lend(models.Model):

from django.db.models import fields

'''class PositiveSmallAutoField(fields.AutoField):
    def db_type(self, connection):
        if 'mysql' in connection.__class__.__module__:
            return 'smallint UNSIGNED AUTO_INCREMENT'
        return super(PositiveSmallAutoField, self).db_type(connection)'''

class Bookinfo(models.Model):
  isbn13 = models.BigIntegerField(validators=[MinValueValidator(9780000000000),MaxValueValidator(9799999999999)] ,null = False)
  bigcat = models.PositiveSmallIntegerField(validators=[MaxValueValidator(99)],null = True)
  midcat = models.PositiveSmallIntegerField(validators=[MaxValueValidator(99)],null = True)
  #smallcat = PositiveSmallAutoField(primary_key = True,null = False,unique = True)
  smallcat = models.AutoField(primary_key = True,null = False,unique = True)
  title = models.CharField(max_length = 150,null = False)
  title_long = models.CharField(max_length = 300,null = False)
  authors = models.CharField(max_length = 160,null = True)
  publisher = models.CharField(max_length = 50,null = True)
  exp = models.CharField(max_length = 3035,null = True)
  lang = models.CharField(max_length = 3,null = True)
  page = models.PositiveSmallIntegerField(null = True,default = 0,)
  publisheddate = models.CharField(max_length = 10,null = True)
  label = models.CharField(max_length = 50,null = True)
  price = models.PositiveIntegerField(null = True,default = 0)
  piclink = models.CharField(max_length = 120,null = True)
  deleteflag = models.BooleanField(default = False)

  def __str__(self):
    return self.smallcat

class Lendmanage(models.Model):
  #smallcat = models.ForeignKey(Bookinfo,primary_key = True,on_delete=models.CASCADE)
  smallcat = models.OneToOneField(Bookinfo, on_delete=models.CASCADE,primary_key = True,unique = True)
  lendflag = models.BooleanField(default = False)
  returndate = models.DateField(null = True,auto_now=False,auto_now_add=False)
  accountid = models.IntegerField(null = False,default = -1)
  #title = models.ForeignKey(Bookinfo,on_delete=models.CASCADE)
  #authors = models.ForeignKey(Bookinfo,on_delete=models.CASCADE)

  '''class Meta:
    unique_together = ('title', 'authors')'''

  def __str__(self):
    return self.smallcat

class Lendhistory(models.Model):
  accountid = models.IntegerField(null = False)
  opeaccountid = models.IntegerField(null = False)
  smallcat = models.SmallIntegerField(null = False)
  lenddate = models.DateTimeField(null = False)
  lendtype = models.BooleanField(null = False)


class Accountinfo(models.Model):
  pass

class BigCategory(models.Model):
  bigcat = models.PositiveSmallIntegerField(validators=[MaxValueValidator(99)],null = False,primary_key = True)
  catname = models.CharField(max_length = 50,null = False)

  def __str__(self):
    return self.bigcat

class MidCategory(models.Model):
  bigcat = models.ForeignKey(BigCategory, on_delete=models.CASCADE)
  midcat = models.PositiveSmallIntegerField(validators=[MaxValueValidator(99)],null = False)
  catname = models.CharField(max_length = 50,null = False)

def number_only(value):
  if(re.match(r'^[0~9]*$', value) == None):
    raise ValidationError(
    '※数字を入力してください',
    )

class Multi(models.Model):
  multi = models.IntegerField(  verbose_name='背表紙の番号を入力してください',validators=[MinValueValidator(0),MaxValueValidator(10000), number_only])

class Returns(models.Model):
  book_name = models.CharField(max_length=300)
  book_author1 = models.CharField(max_length=20)
  book_author2 = models.CharField(max_length=20)
  book_author3 = models.CharField(max_length=20)

  def __str__(self):
    return self.book_name

class UserManager(BaseUserManager):
  def create_user(self,userID, username, email, password=None, is_admin=False, is_staff=False, is_active=True):
    
    if not email:
      raise ValueError('Users must have an email adress')

    if not password:
      raise ValueError('Password is required')

    user = self.model(
      email=self.normalize_email(email)
    )

    user.set_password(password)
    user.userID = userID
    user.username = username
    user.email = email
    user.is_admin = is_admin
    user.is_staff = is_staff
    user.is_active = is_active
    user.save(using=self._db)
    return user

  def create_superuser(self, userID, username, email, password=None):

    user = self.model(
      email=self.normalize_email(email)
    )
    user.set_password(password)
    user.userID = userID
    user.username = username
    user.email = email
    user.is_admin = True
    user.is_staff = True
    user.is_active = True
    user.is_superuser = True
    user.save(using=self._db)
    return user

class User(AbstractBaseUser, PermissionsMixin):
  userID = models.PositiveIntegerField(verbose_name='学籍番号(教職員は未入力)', unique=True, blank=True, null=True,validators=[MinValueValidator(1900000)] )
  ValidationError:['1900000以上の有効な学籍番号を入力してください']
  username = models.CharField(verbose_name='名前',unique=True, blank=True, null=True,max_length=30)
  name = models.CharField(verbose_name='名前',max_length=30)
  email = models.EmailField(verbose_name='メールアドレス', unique=True, max_length = 255)
  date_joined = models.DateTimeField(auto_now_add=True)
  is_active = models.BooleanField(verbose_name='有効フラグ',default=True)
  is_staff = models.BooleanField(verbose_name='管理画面アクセス権限',default=False)
  token = models.CharField(max_length=100,null = True)
  first_password = models.CharField(max_length=128,null = True)
  Class = models.CharField(verbose_name='名前',max_length=30,blank=True,null = True,default = None)
  s_year = models.SmallIntegerField(verbose_name= '入学年',blank=True,null = True,default = None)
  shortname = models.CharField(verbose_name='名前短',max_length=7,blank=True,null = True,default = None)
  
  EMAIL_FIELD = 'email'
  USERNAME_FIELD = 'username'
  REQUIRED_FIELDS = ['userID','email']
  objects = UserManager()

  def __str__(self):
    return self.username

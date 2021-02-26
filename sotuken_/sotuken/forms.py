from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate,get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class CameraForm(forms.Form):
  camera = forms.BooleanField(label='次回表示を省略する', required=False)

class MultiForm(forms.Form):
  multi = forms.IntegerField(label='背表紙の番号を入力してください')

class ReturnsForm(forms.Form):
  book = forms.BooleanField(label='', required=False)
  
class LoginForm(forms.Form):
  username = forms.CharField(label='学籍番号またはメールアドレス',required=True,max_length=30,widget=forms.TextInput(
    attrs={
    'placeholder':'ID or Email'
    }
  ),)

  password = forms.CharField(label='パスワード',required=True,max_length=255,widget=forms.PasswordInput(
    attrs={
      'placeholder':'Password'
    }
  ))

  def clean_username(self):
    username = self.cleaned_data['username']
    return username

  def clean_password(self):
    password = self.cleaned_data['password']
    return password


class SignUpForm(forms.ModelForm):
  email = forms.CharField(max_length=254, required=True, widget=forms.EmailInput())
  class Meta:
    model = User
    fields = ('userID', 'name', 'email', 'is_superuser')

  # def save(self, commit=True):
  #       user = super().save(commit=False)
  #       user.set_password(self.cleaned_data["password"])
  #       if commit:
  #           user.save()
  #       return user

class PasswordResetForm(UserCreationForm):
  class Meta:
    model = User
    fields = ('password',)
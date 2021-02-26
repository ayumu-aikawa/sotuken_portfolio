# #from django.test import TestCase
# import pprint
from django.urls import reverse, resolve
from django.test import TestCase
from .views import signup

# # Create your tests here.


# l = [{'Name': 'Alice', 'Age': 40, 'Point': 80},{'Name': 'Bob', 'Age': 20},{'Name': 'Charlie', 'Age': 30, 'Point': 70}]
# pprint.pprint(sorted(l, key=lambda x: x['Age']))
# print(l[0][Age)

# text = 'aaa bbb ccc'
# word = text.split(' ')
# print(word)

# *[for title__icontains = value in word]
# Bookinfo.objects.filter(*[for title__icontains = value in word])

class SignupTests(TestCase):
  def test_signup_status_code(self):
    url = resolve('signup')
    response = self.client.get(url)
    self.assertEquals(response.status_code, 200)

  def test_signup_url_resolves_signup_view(self):
    view = resolve('/signup/')
    self.assertEquals(view.func, signup)
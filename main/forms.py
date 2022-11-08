from django import forms

class UserForm(forms.Form):
    name=forms.CharField()
    age=forms.IntegerField()
    
class UploadFileForm(forms.Form):
    file=forms.FileField()
    
class AuthForm(forms.Form):
    auth=forms.CharField()
    login=forms.CharField()
    password=forms.CharField()